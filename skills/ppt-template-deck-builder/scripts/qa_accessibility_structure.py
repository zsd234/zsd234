#!/usr/bin/env python3
"""Inspect PPTX slide structure for accessibility and presenter-readiness risks."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

EMU_PER_PT = 12700


def qn(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


def parse_xml(zf: zipfile.ZipFile, part: str) -> etree._Element:
    return etree.fromstring(zf.read(part))


def rels_path(part: str) -> str:
    return posixpath.join(posixpath.dirname(part), "_rels", f"{posixpath.basename(part)}.rels")


def resolve_target(part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def read_rels(zf: zipfile.ZipFile, part: str) -> dict[str, dict[str, str | None]]:
    path = rels_path(part)
    if path not in zf.namelist():
        return {}
    root = parse_xml(zf, path)
    result = {}
    for rel in root.findall("rel:Relationship", namespaces=NS):
        rid = rel.get("Id")
        target = rel.get("Target")
        if rid and target:
            result[rid] = {
                "type": rel.get("Type"),
                "target": target,
                "target_full": resolve_target(part, target),
                "target_mode": rel.get("TargetMode"),
            }
    return result


def local_name(el: etree._Element) -> str:
    return etree.QName(el).localname


def int_attr(el: etree._Element | None, name: str) -> int | None:
    if el is None or el.get(name) is None:
        return None
    try:
        return int(el.get(name))
    except ValueError:
        return None


def bbox(el: etree._Element) -> dict[str, float]:
    xfrm = None
    for path in ("p:spPr/a:xfrm", "p:picPr/a:xfrm", "p:graphicFramePr/a:xfrm", "p:cxnSpPr/a:xfrm"):
        xfrm = el.find(path, namespaces=NS)
        if xfrm is not None:
            break
    off = xfrm.find("a:off", namespaces=NS) if xfrm is not None else None
    ext = xfrm.find("a:ext", namespaces=NS) if xfrm is not None else None
    x = int_attr(off, "x") or 0
    y = int_attr(off, "y") or 0
    w = int_attr(ext, "cx") or 0
    h = int_attr(ext, "cy") or 0
    return {
        "x_pt": round(x / EMU_PER_PT, 2),
        "y_pt": round(y / EMU_PER_PT, 2),
        "w_pt": round(w / EMU_PER_PT, 2),
        "h_pt": round(h / EMU_PER_PT, 2),
        "area_pt2": round((w / EMU_PER_PT) * (h / EMU_PER_PT), 2),
    }


def c_nv_pr(el: etree._Element) -> etree._Element | None:
    for path in (
        "p:nvSpPr/p:cNvPr",
        "p:nvPicPr/p:cNvPr",
        "p:nvGraphicFramePr/p:cNvPr",
        "p:nvCxnSpPr/p:cNvPr",
        "p:nvGrpSpPr/p:cNvPr",
    ):
        found = el.find(path, namespaces=NS)
        if found is not None:
            return found
    return None


def placeholder_type(el: etree._Element) -> str | None:
    ph = el.find("p:nvSpPr/p:nvPr/p:ph", namespaces=NS)
    return ph.get("type") if ph is not None else None


def extract_text(el: etree._Element) -> str:
    texts = [node.text or "" for node in el.findall(".//a:t", namespaces=NS)]
    return re.sub(r"\s+", " ", "".join(texts)).strip()


def is_weak_alt_text(value: str | None) -> bool:
    if not value:
        return True
    stripped = value.strip()
    if not stripped:
        return True
    if re.match(r"^image\d*\.(png|jpe?g|gif|bmp|tiff?|webp)$", stripped, re.I):
        return True
    if re.match(r"^.*\.(png|jpe?g|gif|bmp|tiff?|webp)$", stripped, re.I):
        return True
    if stripped.lower() in {"picture", "image", "photo", "graphic", "screenshot"}:
        return True
    return False


def font_size(el: etree._Element) -> float | None:
    sizes = []
    for rpr in el.findall(".//a:rPr", namespaces=NS):
        raw = rpr.get("sz")
        if raw and raw.isdigit():
            sizes.append(int(raw) / 100)
    return max(sizes) if sizes else None


def iter_shapes(root: etree._Element) -> list[etree._Element]:
    sp_tree = root.find("p:cSld/p:spTree", namespaces=NS)
    if sp_tree is None:
        return []
    result = []

    def visit(parent: etree._Element) -> None:
        for child in parent:
            if local_name(child) in {"sp", "pic", "graphicFrame", "cxnSp", "grpSp"}:
                result.append(child)
                if local_name(child) == "grpSp":
                    visit(child)

    visit(sp_tree)
    return result


def slide_parts(zf: zipfile.ZipFile) -> list[str]:
    presentation = parse_xml(zf, "ppt/presentation.xml")
    rels = read_rels(zf, "ppt/presentation.xml")
    parts = []
    for sld_id in presentation.findall(".//p:sldIdLst/p:sldId", namespaces=NS):
        rid = sld_id.get(qn("r", "id"))
        rel = rels.get(rid, {}) if rid else {}
        part = rel.get("target_full")
        if part and part in zf.namelist():
            parts.append(str(part))
    return parts


def finding(severity: str, slide_id: str, issue: str, fix: str, element_id: str | None = None) -> dict[str, Any]:
    return {
        "severity": severity,
        "slide_id": slide_id,
        "element_id": element_id,
        "issue": issue,
        "proposed_fix": fix,
    }


def analyze_slide(root: etree._Element, slide_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    elements = []
    title_candidates = []
    picture_count = 0
    missing_alt = 0
    reading_order_risks = []
    for z, el in enumerate(iter_shapes(root), start=1):
        cpr = c_nv_pr(el)
        element_id = f"shape-{cpr.get('id')}" if cpr is not None and cpr.get("id") else f"element-{z:03d}"
        kind = local_name(el)
        text = extract_text(el)
        ph_type = placeholder_type(el)
        box = bbox(el)
        fsize = font_size(el)
        alt_title = cpr.get("title") if cpr is not None else None
        alt_descr = cpr.get("descr") if cpr is not None else None
        hidden = cpr.get("hidden") if cpr is not None else None
        elements.append(
            {
                "element_id": element_id,
                "kind": kind,
                "text": text,
                "placeholder_type": ph_type,
                "bbox": box,
                "font_size_pt": fsize,
                "z_order": z,
                "alt_title": alt_title,
                "alt_description": alt_descr,
                "hidden": hidden,
            }
        )
        if ph_type in {"title", "ctrTitle"} or (text and box["y_pt"] < 95 and (fsize or 0) >= 20):
            title_candidates.append((ph_type in {"title", "ctrTitle"}, fsize or 0, box["y_pt"], text, element_id))
        if kind == "pic":
            picture_count += 1
            weak_alt = is_weak_alt_text(alt_title) and is_weak_alt_text(alt_descr)
            if weak_alt:
                missing_alt += 1
                severity = "major" if box["area_pt2"] > 20_000 else "minor"
                findings.append(
                    finding(
                        severity,
                        slide_id,
                        "Picture has no meaningful alt text and is not detectably marked decorative.",
                        "Add concise meaningful alt text for content images or mark decorative images as decorative in PowerPoint.",
                        element_id,
                    )
                )
        if text and box["y_pt"] < 95 and z > 5:
            reading_order_risks.append(element_id)

    title_text = ""
    if title_candidates:
        title_candidates.sort(key=lambda item: (not item[0], -item[1], item[2]))
        title_text = title_candidates[0][3]
    else:
        findings.append(
            finding(
                "major",
                slide_id,
                "No slide title candidate found.",
                "Add a visible title or a hidden accessibility title so screen readers and slide navigation have structure.",
            )
        )
    if reading_order_risks:
        findings.append(
            finding(
                "minor",
                slide_id,
                f"Upper text appears late in object order: {', '.join(reading_order_risks[:5])}.",
                "Verify the Reading Order pane follows title, key visual, and body content in speaking order.",
            )
        )
    return (
        {
            "slide_id": slide_id,
            "title": title_text,
            "picture_count": picture_count,
            "missing_alt_count": missing_alt,
            "element_count": len(elements),
            "elements": elements,
        },
        findings,
    )


def analyze(pptx: Path) -> dict[str, Any]:
    slides = []
    findings: list[dict[str, Any]] = []
    with zipfile.ZipFile(pptx) as zf:
        for idx, part in enumerate(slide_parts(zf), start=1):
            root = parse_xml(zf, part)
            slide_id = f"slide-{idx:03d}"
            slide, slide_findings = analyze_slide(root, slide_id)
            slides.append(slide)
            findings.extend(slide_findings)

    titles: dict[str, list[str]] = {}
    for slide in slides:
        title = (slide.get("title") or "").strip().lower()
        if title:
            titles.setdefault(title, []).append(slide["slide_id"])
    for title, slide_ids in titles.items():
        if len(slide_ids) > 1:
            findings.append(
                finding(
                    "minor",
                    ", ".join(slide_ids),
                    f"Duplicate slide title: {title}.",
                    "Make slide titles unique, using continuation labels if the topic spans multiple slides.",
                )
            )

    blocker = sum(1 for item in findings if item["severity"] == "blocker")
    major = sum(1 for item in findings if item["severity"] == "major")
    minor = sum(1 for item in findings if item["severity"] == "minor")
    return {
        "pptx": str(pptx.resolve()),
        "slide_count": len(slides),
        "blocker_count": blocker,
        "major_count": major,
        "minor_count": minor,
        "stop_condition_met": blocker == 0 and major == 0,
        "slides": slides,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect PPTX accessibility structure: slide titles, alt text, and reading-order risks.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = analyze(args.pptx)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(
        f"slides={report['slide_count']} majors={report['major_count']} "
        f"minors={report['minor_count']} stop={report['stop_condition_met']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
