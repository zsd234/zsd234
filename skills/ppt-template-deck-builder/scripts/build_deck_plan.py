#!/usr/bin/env python3
"""Build a first-pass content-to-template slide plan."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_content(raw: Any) -> dict[str, Any]:
    if isinstance(raw, list):
        slides = raw
        title = None
    elif isinstance(raw, dict):
        slides = raw.get("slides") or raw.get("sections") or []
        title = raw.get("title")
        if not slides and any(k in raw for k in ("bullets", "body", "subtitle", "metrics", "images")):
            slides = [raw]
    else:
        slides = [{"body": str(raw)}]
        title = None
    normalized = []
    for idx, slide in enumerate(slides, start=1):
        if isinstance(slide, str):
            slide = {"title": slide}
        body = slide.get("body") or slide.get("text") or slide.get("notes")
        points = as_list(slide.get("points"))
        bullets = as_list(slide.get("bullets") or [
            point.get("summary") or point.get("title") or point.get("text")
            for point in points
            if isinstance(point, dict)
        ] or points)
        metrics = as_list(slide.get("metrics"))
        images = as_list(slide.get("images") or slide.get("media"))
        normalized.append(
            {
                "source_content_id": slide.get("id") or f"content-{idx:03d}",
                "title": slide.get("title") or slide.get("claim") or (title if idx == 1 else None),
                "subtitle": slide.get("subtitle"),
                "body": body,
                "bullets": bullets,
                "points": points,
                "logic_role": slide.get("logic_role"),
                "relation": slide.get("relation"),
                "metrics": metrics,
                "images": images,
                "raw": slide,
            }
        )
    return {"title": title, "audience": raw.get("audience") if isinstance(raw, dict) else None, "slides": normalized}


def role_counts(slide: dict[str, Any]) -> dict[str, int]:
    return slide.get("role_counts") or {}


def layout_profile(slide: dict[str, Any]) -> dict[str, Any]:
    return slide.get("layout_profile") or {}


def content_point_count(content: dict[str, Any]) -> int:
    points = [p for p in as_list(content.get("points")) if p]
    bullets = [b for b in as_list(content.get("bullets")) if str(b).strip()]
    if points:
        return len(points)
    if bullets:
        return len(bullets)
    return 1 if content.get("body") else 0


def content_family(content: dict[str, Any]) -> str:
    if content.get("images"):
        return "image"
    if content.get("metrics"):
        return "metrics"
    relation = (content.get("relation") or "").lower()
    if relation in {"process", "timeline", "sequence", "步骤", "流程"}:
        return "process"
    points = content_point_count(content)
    if points == 2:
        return "two_point"
    if points == 3:
        return "three_point"
    if points == 4:
        return "four_point"
    if points > 4:
        return "list-heavy"
    return "content"


def slide_score(content: dict[str, Any], candidate: dict[str, Any], idx: int) -> float:
    counts = role_counts(candidate)
    label = candidate.get("semantic_label")
    profile = layout_profile(candidate)
    point_capacity = int(profile.get("point_capacity") or 0)
    required_points = content_point_count(content)
    required_family = content_family(content)
    candidate_family = profile.get("family") or label
    score = 0.0
    has_images = bool(content.get("images"))
    has_metrics = bool(content.get("metrics"))
    has_bullets = bool(content.get("bullets"))
    explicit_cover = (content.get("logic_role") in {"cover", "title", "opening_cover"}) or bool(content.get("is_cover"))
    if explicit_cover and label == "cover":
        score += 4
    elif label == "cover" and (required_points or content.get("body") or content.get("bullets") or content.get("metrics")):
        score -= 6
    if label == "section" and (required_points > 1 or content.get("body") or content.get("bullets")):
        score -= 3
    if has_images and (counts.get("image_hero") or counts.get("image_content") or label == "image-heavy"):
        score += 4
    if has_metrics and counts.get("metric_value"):
        score += 4
    if has_bullets and counts.get("bullets"):
        score += 3
    if content.get("body") and (counts.get("body") or counts.get("bullets")):
        score += 2
    if content.get("title") and counts.get("title"):
        score += 2
    if required_points:
        if point_capacity >= required_points:
            score += 5 - min(point_capacity - required_points, 3)
        elif point_capacity > 0:
            score -= (required_points - point_capacity) * 2.5
        else:
            score -= 2
    if candidate_family == required_family:
        score += 3
    elif required_family.endswith("_point") and candidate_family in {"content", "list-heavy", "five_plus_list"}:
        score += 1
    elif required_family == "metrics" and label == "metrics":
        score += 2
    elif required_family == "image" and label == "image-heavy":
        score += 2
    if not has_images and label == "image-heavy":
        score -= 2
    if not has_metrics and label == "metrics":
        score -= 1
    score -= abs((candidate.get("slide_index") or 1) - (idx + 1)) * 0.03
    return score


def choose_template_slide(content: dict[str, Any], templates: list[dict[str, Any]], idx: int) -> dict[str, Any]:
    ranked = sorted(templates, key=lambda slide: slide_score(content, slide, idx), reverse=True)
    return ranked[0]


def generation_strategy(content: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    profile = layout_profile(selected)
    required_points = content_point_count(content)
    capacity = int(profile.get("point_capacity") or 0)
    if required_points and capacity and required_points > capacity:
        return {
            "mode": "create-variant-from-nearest",
            "reason": f"Content has {required_points} points but selected template slide capacity is {capacity}. Duplicate the nearest slide and add/derive slots using the template grid, typography, and spacing.",
            "requires_designer_review": True,
        }
    if required_points and not capacity:
        return {
            "mode": "manual-template-extension",
            "reason": "No explicit content point capacity was detected; preserve the selected slide and create a template-consistent variant only if needed.",
            "requires_designer_review": True,
        }
    if required_points and capacity > required_points:
        return {
            "mode": "use-template-slide-or-create-smaller-variant",
            "reason": f"Selected template slide has capacity {capacity} but content has {required_points} points. Either leave the extra slot intentionally unused, merge with supporting evidence, or derive a smaller variant from the same slide.",
            "requires_designer_review": True,
        }
    return {
        "mode": "use-template-slide",
        "reason": "Selected template slide can hold the planned content.",
        "requires_designer_review": False,
    }


def take_text(content: dict[str, Any], role: str, used: dict[str, int]) -> tuple[str | None, str]:
    if role == "title":
        value = content.get("title")
        return value, "titleize" if value else "omit"
    if role == "subtitle":
        value = content.get("subtitle")
        return value, "keep" if value else "omit"
    if role in {"bullets", "body"}:
        bullets = [str(x) for x in as_list(content.get("bullets")) if str(x).strip()]
        if role == "bullets" and bullets:
            return "\n".join(f"- {b}" for b in bullets), "bulletize"
        body = content.get("body")
        return (str(body), "summarize") if body else (None, "omit")
    if role == "metric_value":
        metrics = as_list(content.get("metrics"))
        pos = used.get("metrics", 0)
        if pos < len(metrics):
            used["metrics"] = pos + 1
            metric = metrics[pos]
            if isinstance(metric, dict):
                value = metric.get("value") or metric.get("number") or metric.get("label")
            else:
                value = metric
            return str(value), "keep"
    if role == "metric_label":
        metrics = as_list(content.get("metrics"))
        pos = max(0, used.get("metrics", 1) - 1)
        if pos < len(metrics) and isinstance(metrics[pos], dict):
            return str(metrics[pos].get("label") or ""), "keep"
    if role == "caption":
        value = content.get("caption")
        return (str(value), "keep") if value else (None, "omit")
    return None, "omit"


def take_image(content: dict[str, Any], used: dict[str, int]) -> str | None:
    images = as_list(content.get("images"))
    pos = used.get("images", 0)
    if pos >= len(images):
        return None
    used["images"] = pos + 1
    item = images[pos]
    if isinstance(item, dict):
        return item.get("path") or item.get("url") or item.get("src")
    return str(item)


def fits_text(text: str | None, constraints: dict[str, Any]) -> dict[str, Any]:
    estimated = len(text or "")
    max_chars = constraints.get("max_chars")
    fits = True if not max_chars else estimated <= int(max_chars)
    return {"estimated_chars": estimated, "max_chars": max_chars, "fits": fits}


def shorten_note(text: str | None, fit: dict[str, Any]) -> str | None:
    if not text or fit.get("fits"):
        return None
    return f"Text length {fit['estimated_chars']} exceeds estimated slot capacity {fit.get('max_chars')}; rewrite or split before generation."


def element_action(slot: dict[str, Any], content: dict[str, Any], used: dict[str, int]) -> dict[str, Any]:
    role = slot.get("role")
    constraints = slot.get("constraints") or {}
    if role in {"title", "subtitle", "body", "bullets", "metric_value", "metric_label", "caption"}:
        value, transform = take_text(content, role, used)
        action = "set_text" if value else "preserve"
        fit = fits_text(value, constraints)
        return {
            "element_id": slot.get("element_id"),
            "role": role,
            "action": action,
            "text": value,
            "media_asset": None,
            "style_strategy": "inherit",
            "transform": transform,
            "fit": fit,
            "constraints": constraints,
            "notes": [note for note in [shorten_note(value, fit)] if note],
        }
    if role in {"image_hero", "image_content", "icon_slot"}:
        media = take_image(content, used)
        return {
            "element_id": slot.get("element_id"),
            "role": role,
            "action": "set_image" if media else "preserve",
            "text": None,
            "media_asset": media,
            "style_strategy": "preserve-crop",
            "transform": "keep" if media else "omit",
            "fit": {},
            "constraints": constraints,
            "notes": [],
        }
    return {
        "element_id": slot.get("element_id"),
        "role": role,
        "action": "preserve",
        "text": None,
        "media_asset": None,
        "style_strategy": "preserve",
        "transform": "omit",
        "fit": {},
        "constraints": constraints,
        "notes": [],
    }


def build_plan(content: dict[str, Any], semantics: dict[str, Any]) -> dict[str, Any]:
    templates = semantics.get("slides") or []
    if not templates:
        raise ValueError("No template slides found in template semantics.")
    normalized = normalize_content(content)
    output_slides = []
    decisions = []
    for idx, content_slide in enumerate(normalized["slides"]):
        selected = choose_template_slide(content_slide, templates, idx)
        used = {"metrics": 0, "images": 0}
        elements = [element_action(slot, content_slide, used) for slot in selected.get("slots", [])]
        notes = [note for el in elements for note in el.get("notes", [])]
        output_slides.append(
            {
                "output_slide_id": f"out-{idx + 1:03d}",
                "source_content_id": content_slide["source_content_id"],
                "source_slide_id": selected.get("slide_id"),
                "source_slide_index": selected.get("slide_index"),
                "purpose": selected.get("semantic_label"),
                "layout_profile": layout_profile(selected),
                "content_point_count": content_point_count(content_slide),
                "generation_strategy": generation_strategy(content_slide, selected),
                "elements": elements,
                "notes": notes,
            }
        )
        decisions.append(
            {
                "output_slide_id": f"out-{idx + 1:03d}",
                "decision": "selected-source-slide",
                "selected_source_slide_id": selected.get("slide_id"),
                "reason": f"Best first-pass fit for family={content_family(content_slide)} points={content_point_count(content_slide)} score={slide_score(content_slide, selected, idx):.2f}",
                "needs_human_review": bool(notes) or generation_strategy(content_slide, selected)["requires_designer_review"],
            }
        )
    return {
        "source_template": semantics.get("source_model"),
        "deck_title": normalized.get("title"),
        "audience": normalized.get("audience"),
        "slides": output_slides,
        "decision_records": decisions,
        "warnings": collect_warnings(output_slides),
    }


def collect_warnings(slides: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for slide in slides:
        if not any(el["action"] in {"set_text", "set_image"} for el in slide["elements"]):
            warnings.append(f"{slide['output_slide_id']} has no mapped content.")
        for note in slide.get("notes", []):
            warnings.append(f"{slide['output_slide_id']}: {note}")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a first-pass final slide plan from content and template semantics.")
    parser.add_argument("content_json", type=Path)
    parser.add_argument("template_semantics", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    content = read_json(args.content_json)
    semantics = read_json(args.template_semantics)
    plan = build_plan(content, semantics)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    print(f"Wrote {args.out}")
    print(f"Output slides planned: {len(plan['slides'])}; warnings: {len(plan['warnings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
