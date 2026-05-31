#!/usr/bin/env python3
"""Classify first-pass semantic roles and layout capacity for a PPTX template model."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


TEXT_ROLES = {
    "title",
    "subtitle",
    "body",
    "bullets",
    "metric_value",
    "metric_label",
    "quote",
    "caption",
    "footer",
    "section_label",
}

DEFAULT_MIN_READABLE_PT = {
    "title": 28,
    "subtitle": 20,
    "body": 20,
    "bullets": 20,
    "caption": 14,
    "metric_label": 16,
    "metric_value": 30,
    "footer": 9,
}


def area(el: dict[str, Any]) -> float:
    return float(el.get("area_emu2") or 0)


def bbox(el: dict[str, Any]) -> dict[str, float]:
    raw = el.get("bbox") or {}
    return {
        "x": float(raw.get("x_emu") or 0),
        "y": float(raw.get("y_emu") or 0),
        "w": float(raw.get("w_emu") or 0),
        "h": float(raw.get("h_emu") or 0),
        "x_pt": float(raw.get("x_pt") or 0),
        "y_pt": float(raw.get("y_pt") or 0),
        "w_pt": float(raw.get("w_pt") or 0),
        "h_pt": float(raw.get("h_pt") or 0),
    }


def font_size(el: dict[str, Any]) -> float:
    style = el.get("style") or {}
    size = style.get("font_size_pt")
    if isinstance(size, (int, float)) and size > 0:
        return float(size)
    sizes = [run.get("font_size_pt") for run in el.get("text_runs", []) if isinstance(run.get("font_size_pt"), (int, float))]
    return float(max(sizes)) if sizes else 14.0


def text(el: dict[str, Any]) -> str:
    return (el.get("text") or "").strip()


def placeholder_type(el: dict[str, Any]) -> str:
    ph = el.get("placeholder") or {}
    return (ph.get("type") or "").lower()


def name_text(el: dict[str, Any]) -> str:
    return f"{el.get('name') or ''} {placeholder_type(el)}".lower()


def is_numeric_dominant(value: str) -> bool:
    compact = re.sub(r"\s+", "", value)
    if not compact:
        return False
    if re.match(r"^[+-]?[$¥€£]?\d[\d,]*(\.\d+)?%?([A-Za-z]{0,4}|万|亿|元)?$", compact):
        return True
    digits = len(re.findall(r"\d", compact))
    letters = len(re.findall(r"[A-Za-z\u4e00-\u9fff]", compact))
    return digits >= 2 and digits >= letters


def norm_ratio(value: float, total: float) -> float:
    return value / total if total else 0.0


def role_constraints(el: dict[str, Any], role: str) -> dict[str, Any]:
    box = bbox(el)
    size = max(font_size(el), 8.0)
    line_height = size * 1.2
    max_lines = max(1, int(box["h_pt"] / line_height)) if box["h_pt"] else None
    latin_per_line = max(4, int(box["w_pt"] / (size * 0.55))) if box["w_pt"] else None
    cjk_per_line = max(2, int(box["w_pt"] / size)) if box["w_pt"] else None
    max_chars = latin_per_line * max_lines if latin_per_line and max_lines else None
    shape = "paragraph"
    if role in {"title", "subtitle", "section_label"}:
        shape = "short_title"
    elif role == "bullets":
        shape = "bullets"
    elif role in {"metric_value", "metric_label"}:
        shape = "number"
    elif role.startswith("image"):
        shape = "image"
    elif role == "caption":
        shape = "short_caption"
    return {
        "max_chars": max_chars,
        "max_cjk_chars": cjk_per_line * max_lines if cjk_per_line and max_lines else None,
        "max_lines": max_lines,
        "preferred_content_shape": shape,
        "observed_font_size_pt": round(size, 2),
        "recommended_min_font_size_pt": DEFAULT_MIN_READABLE_PT.get(role, 18),
    }


def classify_text_element(
    el: dict[str, Any],
    slide_size: dict[str, Any],
    max_font: float,
    rank_by_font: int,
) -> tuple[str, float, list[str]]:
    role = "body"
    confidence = 0.45
    evidence: list[str] = []
    box = bbox(el)
    slide_w = float(slide_size.get("cx_emu") or 0)
    slide_h = float(slide_size.get("cy_emu") or 0)
    y_ratio = norm_ratio(box["y"], slide_h)
    h_ratio = norm_ratio(box["h"], slide_h)
    w_ratio = norm_ratio(box["w"], slide_w)
    size = font_size(el)
    ntext = name_text(el)
    value = text(el)
    paragraphs = el.get("paragraphs") or []
    has_bullets = any(p.get("bullet") for p in paragraphs)
    numericish = is_numeric_dominant(value)

    ph = placeholder_type(el)
    if ph in {"title", "ctrtitle"} or "title" in ntext:
        role, confidence = "title", 0.9
        evidence.append("placeholder-or-name:title")
    elif ph == "subt" or "subtitle" in ntext:
        role, confidence = "subtitle", 0.85
        evidence.append("placeholder-or-name:subtitle")
    elif ph in {"ftr", "dt", "sldnum"}:
        role, confidence = "footer", 0.95
        evidence.append(f"placeholder:{ph}")
    elif "footer" in ntext or "slide number" in ntext or y_ratio > 0.86:
        role, confidence = "footer", 0.82
        evidence.append("bottom-band-or-name")
    elif has_bullets or len([p for p in paragraphs if (p.get("text") or "").strip()]) >= 3:
        role, confidence = "bullets", 0.76
        evidence.append("multi-paragraph-or-bullets")
    elif numericish and (size >= max(22, max_font * 0.7) or len(value) <= 16):
        role, confidence = "metric_value", 0.78
        evidence.append("numeric-dominant")
    elif value.startswith(("\"", "'")) or value.endswith(("\"", "'")):
        role, confidence = "quote", 0.68
        evidence.append("quote-markers")
    elif y_ratio < 0.18 and size >= 18 and len(value) <= 140:
        role, confidence = "title", 0.78
        evidence.append("prominent-upper-band")
    elif rank_by_font == 0 and y_ratio < 0.35:
        role, confidence = "title", 0.82
        evidence.append("largest-font-top-band")
    elif rank_by_font <= 1 and y_ratio < 0.45 and size >= max_font * 0.75:
        role, confidence = "subtitle", 0.62
        evidence.append("large-font-upper-band")
    elif rank_by_font <= 2 and y_ratio < 0.3 and size >= 13 and len(value) <= 120:
        role, confidence = "subtitle", 0.58
        evidence.append("secondary-upper-band")
    elif size <= 11 and (y_ratio > 0.75 or h_ratio < 0.08):
        role, confidence = "caption", 0.58
        evidence.append("small-text-low-or-short")
    elif w_ratio < 0.22 and size <= 14:
        role, confidence = "section_label", 0.54
        evidence.append("small-label-frame")

    if role == "body" and ph in {"body", "obj"}:
        confidence = max(confidence, 0.75)
        evidence.append(f"placeholder:{ph}")
    if not evidence:
        evidence.append("default-text-heuristic")
    return role, round(confidence, 2), evidence


def classify_image_element(el: dict[str, Any], slide_size: dict[str, Any], largest_image_area: float) -> tuple[str, float, list[str]]:
    box = bbox(el)
    slide_w = float(slide_size.get("cx_emu") or 0)
    slide_h = float(slide_size.get("cy_emu") or 0)
    x_ratio = norm_ratio(box["x"], slide_w)
    y_ratio = norm_ratio(box["y"], slide_h)
    w_ratio = norm_ratio(box["w"], slide_w)
    h_ratio = norm_ratio(box["h"], slide_h)
    a = area(el)
    ntext = name_text(el)
    evidence: list[str] = []
    if w_ratio > 0.9 and h_ratio > 0.85 and x_ratio < 0.06 and y_ratio < 0.08:
        return "background_image", 0.9, ["near-full-slide"]
    if "logo" in ntext or (a > 0 and a < (slide_w * slide_h * 0.025) and (y_ratio < 0.15 or y_ratio > 0.78)):
        return "logo", 0.72, ["small-edge-image"]
    aspect = box["w"] / box["h"] if box["h"] else 0
    if a == largest_image_area or w_ratio > 0.4 or h_ratio > 0.4:
        return "image_hero", 0.78, ["largest-or-large-image"]
    if 0.75 <= aspect <= 1.35 and w_ratio < 0.18 and h_ratio < 0.25:
        return "icon_slot", 0.62, ["small-square-image"]
    evidence.append("image-frame")
    return "image_content", 0.55, evidence


def box_center(el: dict[str, Any]) -> tuple[float, float]:
    box = bbox(el)
    return box["x"] + box["w"] / 2, box["y"] + box["h"] / 2


def nearest_metric_label_candidates(elements: list[dict[str, Any]], slots: list[dict[str, Any]]) -> set[str]:
    by_id = {el.get("element_id"): el for el in elements}
    metric_ids = [slot["element_id"] for slot in slots if slot.get("role") == "metric_value"]
    if not metric_ids:
        return set()
    result: set[str] = set()
    for metric_id in metric_ids:
        metric = by_id.get(metric_id)
        if not metric:
            continue
        m_box = bbox(metric)
        m_cx, m_cy = box_center(metric)
        candidates: list[tuple[float, str]] = []
        for slot in slots:
            if slot.get("role") not in {"section_label", "caption", "body"}:
                continue
            candidate = by_id.get(slot.get("element_id"))
            if not candidate or not text(candidate):
                continue
            c_box = bbox(candidate)
            c_cx, c_cy = box_center(candidate)
            vertical_gap = abs(c_cy - m_cy)
            horizontal_gap = abs(c_cx - m_cx)
            below_or_above = c_box["y"] >= m_box["y"] - m_box["h"] * 0.4
            near_x = horizontal_gap <= max(m_box["w"], c_box["w"]) * 0.9
            near_y = vertical_gap <= max(m_box["h"] * 1.8, c_box["h"] * 3.0)
            small_enough = font_size(candidate) <= max(16, font_size(metric) * 0.55)
            if below_or_above and near_x and near_y and small_enough:
                distance = horizontal_gap + vertical_gap
                candidates.append((distance, str(candidate.get("element_id"))))
        if candidates:
            result.add(sorted(candidates)[0][1])
    return result


def paragraph_count(el: dict[str, Any]) -> int:
    paragraphs = [
        p
        for p in el.get("paragraphs", [])
        if (p.get("text") or "").strip()
    ]
    if paragraphs:
        return len(paragraphs)
    value = text(el)
    return len([line for line in re.split(r"[\r\n]+", value) if line.strip()])


def is_embedded_layout(slide: dict[str, Any], slots: list[dict[str, Any]]) -> bool:
    layout = slide.get("layout") or {}
    layout_name = (layout.get("name") or "").strip().lower()
    has_named_layout = bool(layout_name and layout_name not in {"blank", "空白"})
    has_placeholders = any(slot.get("role") != "decoration" and slot.get("confidence", 0) >= 0.8 for slot in slots)
    return has_named_layout or has_placeholders


def infer_point_capacity(elements: list[dict[str, Any]], slots: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {el.get("element_id"): el for el in elements}
    text_point_slots = []
    bullet_capacity = 0
    metric_count = 0
    image_count = 0
    chart_table_count = 0
    repeated_group_evidence = detect_repeated_content_groups(elements, slots)
    for slot in slots:
        role = slot.get("role")
        el = by_id.get(slot.get("element_id"))
        if not el:
            continue
        constraints = slot.get("constraints") or {}
        if role == "bullets":
            observed = paragraph_count(el)
            estimated = constraints.get("max_lines") or 0
            bullet_capacity = max(bullet_capacity, min(max(observed, estimated, 2), 6))
            text_point_slots.append(slot["element_id"])
        elif role in {"body", "quote", "subtitle", "section_label"} and is_content_point_candidate(el):
            text_point_slots.append(slot["element_id"])
        elif role == "metric_value":
            metric_count += 1
        elif role in {"image_hero", "image_content", "icon_slot"}:
            image_count += 1
        elif role in {"chart", "table"}:
            chart_table_count += 1

    repeated_text_slots = len(text_point_slots)
    repeated_group_count = repeated_group_evidence.get("count", 0)
    if repeated_group_count >= 2:
        point_capacity = repeated_group_count
        source = repeated_group_evidence.get("source", "repeated-geometry")
    elif bullet_capacity:
        point_capacity = int(bullet_capacity)
        source = "bullet-lines"
    elif repeated_text_slots >= 2:
        point_capacity = repeated_text_slots
        source = "repeated-text-slots"
    elif metric_count >= 2:
        point_capacity = metric_count
        source = "metric-slots"
    elif image_count >= 2:
        point_capacity = image_count
        source = "image-slots"
    elif chart_table_count:
        point_capacity = chart_table_count
        source = "chart-table-slots"
    elif repeated_text_slots == 1:
        point_capacity = 1
        source = "single-text-slot"
    else:
        point_capacity = 0
        source = "none"

    return {
        "point_capacity": point_capacity,
        "point_capacity_source": source,
        "text_point_slot_count": repeated_text_slots,
        "metric_slot_count": metric_count,
        "image_slot_count": image_count,
        "chart_table_slot_count": chart_table_count,
        "detected_layout_evidence": repeated_group_evidence.get("evidence", []),
    }


def is_content_point_candidate(el: dict[str, Any]) -> bool:
    box = bbox(el)
    if not text(el):
        return False
    # Exclude obvious title band while allowing card text in the upper half.
    return box["y_pt"] >= 70 and box["h_pt"] >= 24 and box["w_pt"] >= 80


def similar(a: float, b: float, tolerance: float) -> bool:
    return abs(a - b) <= tolerance


def detect_repeated_content_groups(elements: list[dict[str, Any]], slots: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {el.get("element_id"): el for el in elements}
    candidates = [
        by_id.get(slot.get("element_id"))
        for slot in slots
        if slot.get("role") in {"body", "subtitle", "section_label", "metric_value", "metric_label"}
    ]
    text_candidates = [el for el in candidates if el and is_content_point_candidate(el)]
    groups: list[list[dict[str, Any]]] = []
    for el in text_candidates:
        placed = False
        eb = bbox(el)
        for group in groups:
            gb = bbox(group[0])
            if similar(eb["y_pt"], gb["y_pt"], 40) and similar(eb["h_pt"], gb["h_pt"], 50) and similar(font_size(el), font_size(group[0]), 4):
                group.append(el)
                placed = True
                break
        if not placed:
            groups.append([el])
    best = max(groups, key=len, default=[])
    evidence = []
    if len(best) >= 2:
        xs = [round(bbox(el)["x_pt"], 1) for el in best]
        evidence.append(f"{len(best)} repeated text/card slots aligned near x={xs}")

    decorative_candidates = [
        el
        for el in elements
        if el.get("type") in {"shape", "group"} and area(el) > 0 and bbox(el)["y_pt"] >= 60
    ]
    deco_groups: list[list[dict[str, Any]]] = []
    for el in decorative_candidates:
        placed = False
        eb = bbox(el)
        for group in deco_groups:
            gb = bbox(group[0])
            if similar(eb["y_pt"], gb["y_pt"], 30) and similar(eb["w_pt"], gb["w_pt"], 50) and similar(eb["h_pt"], gb["h_pt"], 50):
                group.append(el)
                placed = True
                break
        if not placed:
            deco_groups.append([el])
    best_deco = max(deco_groups, key=len, default=[])
    if len(best_deco) > len(best):
        evidence = [f"{len(best_deco)} repeated card/background shapes"]
        return {"count": len(best_deco), "source": "repeated-card-geometry", "evidence": evidence}
    return {"count": len(best), "source": "repeated-text-geometry", "evidence": evidence}


def infer_layout_family(label: str, capacity: dict[str, Any], role_counts: dict[str, int]) -> str:
    points = capacity["point_capacity"]
    if label in {"cover", "section", "image-heavy", "metrics", "toc-or-list"}:
        base = label
    elif role_counts.get("chart") or role_counts.get("table"):
        base = "data"
    elif capacity.get("image_slot_count", 0) >= 2:
        base = "image-grid"
    elif capacity.get("metric_slot_count", 0) >= 2:
        base = "metrics"
    elif points == 2:
        base = "two_point"
    elif points == 3:
        base = "three_point"
    elif points == 4:
        base = "four_point"
    elif points > 4:
        base = "list-heavy"
    else:
        base = label
    return base


def infer_readability(slots: list[dict[str, Any]]) -> dict[str, Any]:
    too_small = []
    for slot in slots:
        role = slot.get("role")
        constraints = slot.get("constraints") or {}
        observed = constraints.get("observed_font_size_pt")
        minimum = constraints.get("recommended_min_font_size_pt")
        if role in {"footer", "decoration", "logo", "background_image", "unknown"}:
            continue
        if isinstance(observed, (int, float)) and isinstance(minimum, (int, float)) and observed < minimum:
            too_small.append(
                {
                    "element_id": slot.get("element_id"),
                    "role": role,
                    "observed_font_size_pt": observed,
                    "recommended_min_font_size_pt": minimum,
                }
            )
    return {
        "profile": "presentation-readable",
        "too_small_text": too_small,
        "has_font_size_risk": bool(too_small),
    }


def classify_slide(slide: dict[str, Any], slide_size: dict[str, Any]) -> dict[str, Any]:
    elements = slide.get("elements") or []
    text_elements = [el for el in elements if text(el) and el.get("type") in {"text", "placeholder"}]
    image_elements = [el for el in elements if el.get("type") == "image"]
    fonts = sorted([(font_size(el), idx, el) for idx, el in enumerate(text_elements)], reverse=True)
    font_rank = {id(el): rank for rank, (_, _, el) in enumerate(fonts)}
    max_font = fonts[0][0] if fonts else 14.0
    largest_image_area = max([area(el) for el in image_elements], default=0)

    slots: list[dict[str, Any]] = []
    visual_specs: list[dict[str, Any]] = []
    role_counts: dict[str, int] = {}
    for el in elements:
        etype = el.get("type")
        if etype == "image":
            role, confidence, evidence = classify_image_element(el, slide_size, largest_image_area)
        elif text(el) and etype in {"text", "placeholder"}:
            role, confidence, evidence = classify_text_element(el, slide_size, max_font, font_rank.get(id(el), 999))
        elif etype in {"shape", "line", "group"}:
            role, confidence, evidence = "decoration", 0.58, ["non-text-shape"]
        elif etype in {"chart", "table"}:
            role, confidence, evidence = etype, 0.75, [f"graphic:{etype}"]
        else:
            role, confidence, evidence = "unknown", 0.35, ["unclassified"]
        role_counts[role] = role_counts.get(role, 0) + 1
        slots.append(
            {
                "slide_id": slide.get("slide_id"),
                "element_id": el.get("element_id"),
                "role": role,
                "confidence": confidence,
                "evidence": evidence,
                "constraints": role_constraints(el, role),
            }
        )
        must_preserve = ["bbox", "z_order"]
        if role in {"footer", "logo", "decoration", "background_image"}:
            must_preserve.append("content")
        if role in TEXT_ROLES:
            must_preserve.extend(["font_family", "color", "alignment"])
        visual_specs.append(
            {
                "slide_id": slide.get("slide_id"),
                "element_id": el.get("element_id"),
                "resolved_style": el.get("style") or {},
                "source": el.get("source") or "direct",
                "must_preserve": sorted(set(must_preserve)),
                "editable": role not in {"decoration", "background_image", "logo", "footer"},
                "risk_notes": [] if confidence >= 0.5 else ["low-confidence-role"],
            }
        )
    for element_id in nearest_metric_label_candidates(elements, slots):
        for slot in slots:
            if slot.get("element_id") == element_id:
                slot["role"] = "metric_label"
                slot["confidence"] = max(float(slot.get("confidence") or 0), 0.72)
                slot["evidence"] = list(slot.get("evidence") or []) + ["nearby-metric-value"]
                slot["constraints"] = role_constraints(next(el for el in elements if el.get("element_id") == element_id), "metric_label")
        for spec in visual_specs:
            if spec.get("element_id") == element_id:
                spec["editable"] = True
                spec["risk_notes"] = [note for note in spec.get("risk_notes", []) if note != "low-confidence-role"]
    role_counts = {}
    for slot in slots:
        role = str(slot.get("role"))
        role_counts[role] = role_counts.get(role, 0) + 1
    label = slide_label(role_counts, text_elements, image_elements, slide.get("slide_index", 0))
    capacity = infer_point_capacity(elements, slots)
    layout_profile = {
        "family": infer_layout_family(label, capacity, role_counts),
        "semantic_label": label,
        "template_origin": "embedded-layout" if is_embedded_layout(slide, slots) else "slide-form",
        **capacity,
        "readability": infer_readability(slots),
    }
    return {
        "slide_id": slide.get("slide_id"),
        "slide_index": slide.get("slide_index"),
        "source_part": slide.get("part"),
        "layout": slide.get("layout"),
        "semantic_label": label,
        "layout_profile": layout_profile,
        "role_counts": role_counts,
        "slots": slots,
        "visual_specs": visual_specs,
    }


def slide_label(role_counts: dict[str, int], text_elements: list[dict[str, Any]], image_elements: list[dict[str, Any]], slide_index: int) -> str:
    text_count = len(text_elements)
    image_count = len(image_elements)
    if slide_index == 1 and role_counts.get("title") and text_count <= 4:
        return "cover"
    if role_counts.get("image_hero") or role_counts.get("background_image"):
        if text_count <= 3 or image_count >= 2:
            return "image-heavy"
    if role_counts.get("bullets", 0) >= 1:
        return "content"
    if role_counts.get("metric_value", 0) >= 2:
        return "metrics"
    if role_counts.get("title") and text_count <= 2 and image_count == 0:
        return "section"
    if text_count >= 5 and not image_count:
        return "toc-or-list"
    return "content"


def classify(model: dict[str, Any]) -> dict[str, Any]:
    slides = [classify_slide(slide, model.get("slide_size") or {}) for slide in model.get("slides", [])]
    role_index: dict[str, list[dict[str, Any]]] = {}
    for slide in slides:
        for slot in slide["slots"]:
            role_index.setdefault(slot["role"], []).append(
                {"slide_id": slot["slide_id"], "element_id": slot["element_id"], "confidence": slot["confidence"]}
            )
    return {
        "source_model": model.get("source_pptx"),
        "slide_size": model.get("slide_size"),
        "theme": model.get("theme"),
        "slides": slides,
        "role_index": role_index,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify semantic roles in a template model JSON file.")
    parser.add_argument("template_model", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    model = read_json(args.template_model)
    semantics = classify(model)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(semantics, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    print(f"Wrote {args.out}")
    print(f"Slides classified: {len(semantics['slides'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
