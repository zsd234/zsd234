#!/usr/bin/env python3
"""Extract a PowerPoint template model from a .pptx package.

The script intentionally reads OOXML directly so it works without python-pptx.
It produces JSON intended for downstream semantic classification and planning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

from lxml import etree

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional runtime helper
    Image = None


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

EMU_PER_PT = 12700


def qn(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


def local_name(el: etree._Element) -> str:
    return etree.QName(el).localname


def parse_xml(zf: zipfile.ZipFile, part: str) -> etree._Element:
    return etree.fromstring(zf.read(part))


def rels_path(part: str) -> str:
    folder = posixpath.dirname(part)
    base = posixpath.basename(part)
    return posixpath.join(folder, "_rels", f"{base}.rels")


def resolve_target(part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def read_rels(zf: zipfile.ZipFile, part: str) -> dict[str, dict[str, str | None]]:
    path = rels_path(part)
    if path not in zf.namelist():
        return {}
    root = parse_xml(zf, path)
    rels: dict[str, dict[str, str | None]] = {}
    for rel in root.findall("rel:Relationship", namespaces=NS):
        rid = rel.get("Id")
        target = rel.get("Target")
        if not rid or not target:
            continue
        rels[rid] = {
            "id": rid,
            "type": rel.get("Type"),
            "target": target,
            "target_full": resolve_target(part, target),
            "target_mode": rel.get("TargetMode"),
        }
    return rels


def emu_to_pt(value: int | None) -> float | None:
    if value is None:
        return None
    return round(value / EMU_PER_PT, 3)


def int_attr(el: etree._Element | None, name: str) -> int | None:
    if el is None:
        return None
    raw = el.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def find_first(el: etree._Element, paths: list[str]) -> etree._Element | None:
    for path in paths:
        found = el.find(path, namespaces=NS)
        if found is not None:
            return found
    return None


def color_value(el: etree._Element | None) -> dict[str, str] | None:
    if el is None:
        return None
    solid = el.find("a:solidFill", namespaces=NS)
    if solid is None:
        solid = el.find(".//a:solidFill", namespaces=NS)
    if solid is None:
        return None
    srgb = solid.find("a:srgbClr", namespaces=NS)
    if srgb is not None and srgb.get("val"):
        return {"type": "srgb", "value": srgb.get("val")}
    scheme = solid.find("a:schemeClr", namespaces=NS)
    if scheme is not None and scheme.get("val"):
        return {"type": "scheme", "value": scheme.get("val")}
    sysclr = solid.find("a:sysClr", namespaces=NS)
    if sysclr is not None:
        return {"type": "system", "value": sysclr.get("lastClr") or sysclr.get("val") or ""}
    return None


def extract_bbox(el: etree._Element) -> dict[str, int | float | None]:
    xfrm = find_first(
        el,
        [
            "p:spPr/a:xfrm",
            "p:picPr/a:xfrm",
            "p:xfrm",
            "p:cxnSpPr/a:xfrm",
            "p:grpSpPr/a:xfrm",
        ],
    )
    off = xfrm.find("a:off", namespaces=NS) if xfrm is not None else None
    ext = xfrm.find("a:ext", namespaces=NS) if xfrm is not None else None
    x = int_attr(off, "x")
    y = int_attr(off, "y")
    w = int_attr(ext, "cx")
    h = int_attr(ext, "cy")
    return {
        "x_emu": x,
        "y_emu": y,
        "w_emu": w,
        "h_emu": h,
        "x_pt": emu_to_pt(x),
        "y_pt": emu_to_pt(y),
        "w_pt": emu_to_pt(w),
        "h_pt": emu_to_pt(h),
        "rotation": int_attr(xfrm, "rot"),
        "flip_h": xfrm.get("flipH") == "1" if xfrm is not None else False,
        "flip_v": xfrm.get("flipV") == "1" if xfrm is not None else False,
    }


def non_null_bbox_area(bbox: dict[str, Any]) -> int:
    w = bbox.get("w_emu") or 0
    h = bbox.get("h_emu") or 0
    return int(w) * int(h)


def c_nv_pr(el: etree._Element) -> etree._Element | None:
    paths = [
        "p:nvSpPr/p:cNvPr",
        "p:nvPicPr/p:cNvPr",
        "p:nvGraphicFramePr/p:cNvPr",
        "p:nvCxnSpPr/p:cNvPr",
        "p:nvGrpSpPr/p:cNvPr",
    ]
    return find_first(el, paths)


def placeholder(el: etree._Element) -> dict[str, str | None] | None:
    ph = el.find("p:nvSpPr/p:nvPr/p:ph", namespaces=NS)
    if ph is None:
        return None
    return {"type": ph.get("type"), "idx": ph.get("idx"), "orient": ph.get("orient")}


def font_from_rpr(rpr: etree._Element | None) -> str | None:
    if rpr is None:
        return None
    for tag in ("a:latin", "a:ea", "a:cs"):
        font = rpr.find(tag, namespaces=NS)
        if font is not None and font.get("typeface"):
            return font.get("typeface")
    return None


def run_style(rpr: etree._Element | None) -> dict[str, Any]:
    size = None
    if rpr is not None and rpr.get("sz"):
        try:
            size = round(int(rpr.get("sz")) / 100, 2)
        except ValueError:
            size = None
    underline = None
    if rpr is not None:
        underline = rpr.get("u")
    return {
        "font_family": font_from_rpr(rpr),
        "font_size_pt": size,
        "bold": rpr.get("b") in ("1", "true") if rpr is not None else None,
        "italic": rpr.get("i") in ("1", "true") if rpr is not None else None,
        "underline": underline,
        "color": color_value(rpr),
    }


def extract_text(el: etree._Element) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    paragraphs: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    tx_body = el.find("p:txBody", namespaces=NS)
    if tx_body is None:
        return "", runs, paragraphs

    para_texts: list[str] = []
    for para in tx_body.findall("a:p", namespaces=NS):
        ppr = para.find("a:pPr", namespaces=NS)
        fragments: list[str] = []
        for child in para:
            lname = local_name(child)
            if lname in {"r", "fld"}:
                text_el = child.find("a:t", namespaces=NS)
                text = text_el.text if text_el is not None and text_el.text else ""
                if text:
                    fragments.append(text)
                rpr = child.find("a:rPr", namespaces=NS)
                style = run_style(rpr)
                runs.append({"text": text, **style})
            elif lname == "br":
                fragments.append("\n")
        p_text = "".join(fragments)
        para_texts.append(p_text)
        paragraphs.append(
            {
                "text": p_text,
                "alignment": ppr.get("algn") if ppr is not None else None,
                "level": int(ppr.get("lvl")) if ppr is not None and ppr.get("lvl", "").isdigit() else 0,
                "bullet": paragraph_bullet(ppr),
            }
        )
    return "\n".join([text for text in para_texts if text]), runs, paragraphs


def paragraph_bullet(ppr: etree._Element | None) -> dict[str, str | None] | None:
    if ppr is None:
        return None
    if ppr.find("a:buNone", namespaces=NS) is not None:
        return None
    bu_char = ppr.find("a:buChar", namespaces=NS)
    if bu_char is not None:
        return {"type": "char", "value": bu_char.get("char")}
    bu_auto = ppr.find("a:buAutoNum", namespaces=NS)
    if bu_auto is not None:
        return {"type": "auto", "value": bu_auto.get("type")}
    return None


def shape_fill_and_line(el: etree._Element) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    sp_pr = find_first(el, ["p:spPr", "p:picPr", "p:cxnSpPr"])
    fill = color_value(sp_pr)
    line_el = sp_pr.find("a:ln", namespaces=NS) if sp_pr is not None else None
    line = color_value(line_el)
    return fill, line


def picture_info(el: etree._Element, rels: dict[str, dict[str, str | None]]) -> dict[str, Any] | None:
    blip = el.find(".//a:blip", namespaces=NS)
    if blip is None:
        return None
    rid = blip.get(qn("r", "embed")) or blip.get(qn("r", "link"))
    crop = el.find(".//a:srcRect", namespaces=NS)
    target = rels.get(rid, {}) if rid else {}
    return {
        "relationship_id": rid,
        "target": target.get("target_full"),
        "crop": {k: crop.get(k) for k in ("l", "r", "t", "b")} if crop is not None else None,
    }


def graphic_type(el: etree._Element, rels: dict[str, dict[str, str | None]]) -> tuple[str, dict[str, Any] | None]:
    chart = el.find(".//c:chart", namespaces=NS)
    if chart is not None:
        rid = chart.get(qn("r", "id"))
        return "chart", {"relationship_id": rid, "target": rels.get(rid, {}).get("target_full") if rid else None}
    if el.find(".//a:tbl", namespaces=NS) is not None:
        return "table", None
    return "graphic", None


def element_type(el: etree._Element, text: str, rels: dict[str, dict[str, str | None]]) -> tuple[str, dict[str, Any] | None]:
    lname = local_name(el)
    if lname == "pic":
        return "image", picture_info(el, rels)
    if lname == "graphicFrame":
        return graphic_type(el, rels)
    if lname == "cxnSp":
        return "line", None
    if lname == "grpSp":
        return "group", None
    if placeholder(el):
        return "placeholder", None
    if text.strip():
        return "text", None
    return "shape", None


def summarize_style(runs: list[dict[str, Any]], paragraphs: list[dict[str, Any]], el: etree._Element) -> dict[str, Any]:
    first = next((run for run in runs if run.get("text")), runs[0] if runs else {})
    fill, line = shape_fill_and_line(el)
    return {
        "font_family": first.get("font_family"),
        "font_size_pt": first.get("font_size_pt"),
        "bold": first.get("bold"),
        "italic": first.get("italic"),
        "underline": first.get("underline"),
        "color": first.get("color"),
        "alignment": paragraphs[0].get("alignment") if paragraphs else None,
        "fill": fill,
        "line": line,
    }


def iter_shape_elements(sp_tree: etree._Element) -> list[etree._Element]:
    result: list[etree._Element] = []

    def visit(parent: etree._Element) -> None:
        for child in parent:
            lname = local_name(child)
            if lname in {"sp", "pic", "graphicFrame", "cxnSp", "grpSp"}:
                result.append(child)
                if lname == "grpSp":
                    visit(child)

    visit(sp_tree)
    return result


def extract_elements(root: etree._Element, rels: dict[str, dict[str, str | None]], slide_id: str) -> list[dict[str, Any]]:
    sp_tree = root.find("p:cSld/p:spTree", namespaces=NS)
    if sp_tree is None:
        return []
    elements: list[dict[str, Any]] = []
    for z_order, el in enumerate(iter_shape_elements(sp_tree), start=1):
        cpr = c_nv_pr(el)
        raw_id = cpr.get("id") if cpr is not None else None
        name = cpr.get("name") if cpr is not None else None
        alt_text = {
            "title": cpr.get("title") if cpr is not None else None,
            "description": cpr.get("descr") if cpr is not None else None,
            "hidden": cpr.get("hidden") if cpr is not None else None,
        }
        text, runs, paragraphs = extract_text(el)
        etype, payload = element_type(el, text, rels)
        bbox = extract_bbox(el)
        element_id = f"shape-{raw_id}" if raw_id else f"element-{z_order:03d}"
        element = {
            "slide_id": slide_id,
            "element_id": element_id,
            "name": name,
            "alt_text": alt_text,
            "type": etype,
            "xml_tag": local_name(el),
            "placeholder": placeholder(el),
            "bbox": bbox,
            "area_emu2": non_null_bbox_area(bbox),
            "z_order": z_order,
            "text": text,
            "text_runs": runs,
            "paragraphs": paragraphs,
            "style": summarize_style(runs, paragraphs, el),
            "picture": payload if etype == "image" else None,
            "graphic": payload if etype in {"chart", "table", "graphic"} else None,
            "source": "direct",
        }
        elements.append(element)
    return elements


def theme_model(zf: zipfile.ZipFile) -> dict[str, Any]:
    theme_parts = sorted(name for name in zf.namelist() if name.startswith("ppt/theme/theme") and name.endswith(".xml"))
    if not theme_parts:
        return {"colors": {}, "fonts": {}, "part": None}
    root = parse_xml(zf, theme_parts[0])
    colors: dict[str, str] = {}
    clr_scheme = root.find(".//a:clrScheme", namespaces=NS)
    if clr_scheme is not None:
        for child in clr_scheme:
            name = local_name(child)
            srgb = child.find(".//a:srgbClr", namespaces=NS)
            sysclr = child.find(".//a:sysClr", namespaces=NS)
            if srgb is not None and srgb.get("val"):
                colors[name] = srgb.get("val")
            elif sysclr is not None:
                colors[name] = sysclr.get("lastClr") or sysclr.get("val") or ""
    fonts: dict[str, str | None] = {}
    for scope in ("majorFont", "minorFont"):
        node = root.find(f".//a:{scope}", namespaces=NS)
        if node is None:
            continue
        latin = node.find("a:latin", namespaces=NS)
        ea = node.find("a:ea", namespaces=NS)
        cs = node.find("a:cs", namespaces=NS)
        fonts[f"{scope}_latin"] = latin.get("typeface") if latin is not None else None
        fonts[f"{scope}_east_asia"] = ea.get("typeface") if ea is not None else None
        fonts[f"{scope}_complex"] = cs.get("typeface") if cs is not None else None
    return {"colors": colors, "fonts": fonts, "part": theme_parts[0]}


def layout_info(zf: zipfile.ZipFile, slide_part: str, slide_rels: dict[str, dict[str, str | None]]) -> dict[str, Any]:
    layout_rel = next((rel for rel in slide_rels.values() if rel.get("type", "").endswith("/slideLayout")), None)
    if not layout_rel or not layout_rel.get("target_full"):
        return {"part": None, "name": None, "master_part": None}
    layout_part = str(layout_rel["target_full"])
    name = None
    master_part = None
    if layout_part in zf.namelist():
        layout_root = parse_xml(zf, layout_part)
        c_sld = layout_root.find("p:cSld", namespaces=NS)
        name = c_sld.get("name") if c_sld is not None else None
        layout_rels = read_rels(zf, layout_part)
        master_rel = next((rel for rel in layout_rels.values() if rel.get("type", "").endswith("/slideMaster")), None)
        master_part = master_rel.get("target_full") if master_rel else None
    return {"part": layout_part, "name": name, "master_part": master_part}


def media_inventory(zf: zipfile.ZipFile) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for name in sorted(n for n in zf.namelist() if n.startswith("ppt/media/") and not n.endswith("/")):
        data = zf.read(name)
        item: dict[str, Any] = {
            "part": name,
            "bytes": len(data),
            "sha1": hashlib.sha1(data).hexdigest(),
        }
        if Image is not None:
            try:
                with Image.open(BytesIO(data)) as img:
                    item["width_px"] = img.width
                    item["height_px"] = img.height
                    item["format"] = img.format
            except Exception:
                pass
        items.append(item)
    return items


def slide_size(root: etree._Element) -> dict[str, Any]:
    size = root.find("p:sldSz", namespaces=NS)
    cx = int_attr(size, "cx")
    cy = int_attr(size, "cy")
    width_pt = emu_to_pt(cx)
    height_pt = emu_to_pt(cy)
    ratio = round(width_pt / height_pt, 4) if width_pt and height_pt else None
    return {"cx_emu": cx, "cy_emu": cy, "width_pt": width_pt, "height_pt": height_pt, "aspect_ratio": ratio}


def extract_model(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        if "ppt/presentation.xml" not in names:
            raise ValueError("The file is not a valid PPTX package: missing ppt/presentation.xml")
        presentation = parse_xml(zf, "ppt/presentation.xml")
        pres_rels = read_rels(zf, "ppt/presentation.xml")
        slides: list[dict[str, Any]] = []
        for idx, sld_id in enumerate(presentation.findall(".//p:sldIdLst/p:sldId", namespaces=NS), start=1):
            rid = sld_id.get(qn("r", "id"))
            rel = pres_rels.get(rid, {}) if rid else {}
            slide_part = rel.get("target_full")
            if not slide_part or slide_part not in names:
                continue
            slide_id = f"slide-{idx:03d}"
            slide_root = parse_xml(zf, str(slide_part))
            s_rels = read_rels(zf, str(slide_part))
            slides.append(
                {
                    "slide_id": slide_id,
                    "slide_index": idx,
                    "pptx_slide_id": sld_id.get("id"),
                    "part": slide_part,
                    "layout": layout_info(zf, str(slide_part), s_rels),
                    "elements": extract_elements(slide_root, s_rels, slide_id),
                }
            )
        return {
            "source_pptx": str(path.resolve()),
            "slide_size": slide_size(presentation),
            "theme": theme_model(zf),
            "media": media_inventory(zf),
            "slides": slides,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a structured JSON model from a PPTX template.")
    parser.add_argument("pptx", type=Path, help="Template .pptx file")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON path")
    parser.add_argument("--pretty", action="store_true", help="Write indented JSON")
    args = parser.parse_args()

    model = extract_model(args.pptx)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(model, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    print(f"Wrote {args.out}")
    print(f"Slides: {len(model['slides'])}; media: {len(model['media'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
