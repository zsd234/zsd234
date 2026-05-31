#!/usr/bin/env python3
"""Check a final slide plan and optional animation plan for planning risks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


READABILITY_PROFILES = {
    "classroom": {
        "min_title_pt": 40,
        "min_subtitle_pt": 28,
        "min_body_pt": 28,
        "min_caption_pt": 14,
        "max_body_items_per_slide": 5,
        "max_text_lines_per_slide": 9,
        "max_title_chars": 72,
    },
    "report": {
        "min_title_pt": 28,
        "min_subtitle_pt": 20,
        "min_body_pt": 18,
        "min_caption_pt": 9,
        "max_body_items_per_slide": 6,
        "max_text_lines_per_slide": 11,
        "max_title_chars": 90,
    },
}

CORE_ROLES = {"title", "subtitle", "body", "bullets", "metric_value", "metric_label", "caption"}
DISALLOWED_EFFECTS = {"bounce", "spin", "random_bars", "fly_in_fast", "complex_motion_path"}
NON_ANIMATED_ROLES = {"footer", "logo", "decoration", "background_image"}
ANIMATION_LIMITS = {
    "classroom": 5,
    "executive": 4,
    "minimal": 0,
}


def read_json(path: Path | None) -> Any:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def finding(severity: str, slide_id: str, issue: str, fix: str, element_id: str | None = None) -> dict[str, Any]:
    return {
        "severity": severity,
        "slide_id": slide_id,
        "element_id": element_id,
        "issue": issue,
        "proposed_fix": fix,
    }


def min_font_for_role(role: str, mode: str) -> int:
    profile = READABILITY_PROFILES[mode]
    if role == "title":
        return profile["min_title_pt"]
    if role == "subtitle":
        return profile["min_subtitle_pt"]
    if role in {"caption", "metric_label"}:
        return profile["min_caption_pt"]
    return profile["min_body_pt"]


def check_plan(plan: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for slide in plan.get("slides", []):
        slide_id = slide.get("output_slide_id") or "unknown-slide"
        profile = slide.get("layout_profile") or {}
        point_capacity = int(profile.get("point_capacity") or 0)
        point_count = int(slide.get("content_point_count") or 0)
        if point_capacity and point_count > point_capacity:
            findings.append(
                finding(
                    "major",
                    slide_id,
                    f"Content has {point_count} points but selected layout capacity is {point_capacity}.",
                    "Split the slide, summarize points, or create a template-consistent layout variant.",
                )
            )
        strategy = slide.get("generation_strategy") or {}
        if strategy.get("requires_designer_review"):
            findings.append(
                finding(
                    "minor",
                    slide_id,
                    strategy.get("reason") or "Slide requires designer review.",
                    "Review generated variant or choose a closer template page before final export.",
                )
            )
        has_title = False
        title_text = ""
        body_items = 0
        text_lines = 0
        for element in slide.get("elements", []):
            role = element.get("role")
            element_text = str(element.get("text") or "")
            if role == "title":
                has_title = True
                title_text = element_text or title_text
            if role == "bullets" and element.get("text"):
                body_items += len([line for line in element_text.splitlines() if line.strip()])
            if role in {"title", "subtitle", "body", "bullets", "caption", "metric_label"} and element_text:
                explicit_lines = [line for line in element_text.splitlines() if line.strip()]
                text_lines += max(1, len(explicit_lines))
            constraints = (element.get("fit") or {})
            if constraints.get("fits") is False:
                findings.append(
                    finding(
                        "major",
                        slide_id,
                        f"Mapped text exceeds estimated slot capacity ({constraints.get('estimated_chars')} > {constraints.get('max_chars')}).",
                        "Rewrite shorter, split to another slide, or select a larger capacity layout.",
                        element.get("element_id"),
                    )
                )
            observed = ((element.get("constraints") or {}).get("observed_font_size_pt"))
            if role in CORE_ROLES and isinstance(observed, (int, float)):
                minimum = min_font_for_role(role, mode)
                if observed < minimum:
                    findings.append(
                        finding(
                            "major",
                            slide_id,
                            f"{role} font size {observed}pt is below {mode} minimum {minimum}pt.",
                            "Increase font size via the inherited hierarchy, shorten copy, or split the slide.",
                            element.get("element_id"),
                        )
                    )
        if not has_title:
            findings.append(
                finding(
                    "major",
                    slide_id,
                    "Slide has no title role in the final plan.",
                    "Add a visible title or an intentionally hidden accessibility title.",
                )
            )
        if title_text and len(title_text) > READABILITY_PROFILES[mode]["max_title_chars"]:
            findings.append(
                finding(
                    "major",
                    slide_id,
                    f"Title is too long to scan quickly ({len(title_text)} characters).",
                    "Rewrite the title as a shorter claim and move nuance into subtitle or speaker notes.",
                )
            )
        if body_items > READABILITY_PROFILES[mode]["max_body_items_per_slide"]:
            findings.append(
                finding(
                    "major",
                    slide_id,
                    f"Slide has {body_items} body items, above {mode} recommended maximum.",
                    "Group, shorten, or split body points.",
                )
            )
        if text_lines > READABILITY_PROFILES[mode]["max_text_lines_per_slide"]:
            findings.append(
                finding(
                    "major",
                    slide_id,
                    f"Slide has about {text_lines} text lines, above the {mode} safe limit.",
                    "Split the slide, shorten copy, or move detail to speaker notes.",
                )
            )
    return findings


def check_animation(animation_plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not animation_plan:
        return []
    findings: list[dict[str, Any]] = []
    for slide in animation_plan.get("slides", []):
        slide_id = slide.get("output_slide_id") or "unknown-slide"
        sequence = slide.get("sequence") or []
        style = slide.get("animation_style") or animation_plan.get("mode") or "classroom"
        max_allowed = ANIMATION_LIMITS.get(style, 5)
        if len(sequence) > max_allowed:
            findings.append(
                finding(
                    "major",
                    slide_id,
                    f"Slide animates {len(sequence)} elements, above the safe maximum of {max_allowed} for {style} mode.",
                    "Animate only the teaching order or downgrade to a single fade.",
                )
            )
        emphasis_count = 0
        for item in sequence:
            role = item.get("role")
            effect = str(item.get("effect") or "").lower()
            if role in NON_ANIMATED_ROLES:
                findings.append(
                    finding(
                        "major",
                        slide_id,
                        f"Non-content role {role} is animated.",
                        "Remove animation from decorative/template chrome.",
                        item.get("element_id"),
                    )
                )
            if effect in DISALLOWED_EFFECTS:
                findings.append(
                    finding(
                        "major",
                        slide_id,
                        f"Disallowed animation effect used: {effect}.",
                        "Use fade, appear, or simple wipe instead.",
                        item.get("element_id"),
                    )
                )
            if "pulse" in effect or "emphasis" in effect:
                emphasis_count += 1
        if emphasis_count > 1:
            findings.append(
                finding(
                    "major",
                    slide_id,
                    "More than one emphasis animation on the slide.",
                    "Keep only the one emphasis that supports the core point.",
                )
            )
    return findings


def summarize(findings: list[dict[str, Any]], iteration: int) -> dict[str, Any]:
    blocker = sum(1 for item in findings if item["severity"] == "blocker")
    major = sum(1 for item in findings if item["severity"] == "major")
    minor = sum(1 for item in findings if item["severity"] == "minor")
    return {
        "iteration": iteration,
        "blocker_count": blocker,
        "major_count": major,
        "minor_count": minor,
        "readability_failures": sum(1 for item in findings if "font size" in item["issue"] or "body items" in item["issue"]),
        "animation_overuse_count": sum(1 for item in findings if "animat" in item["issue"].lower() or "effect" in item["issue"].lower()),
        "stop_condition_met": blocker == 0 and major == 0,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="QA a final slide plan and optional animation plan.")
    parser.add_argument("final_slide_plan", type=Path)
    parser.add_argument("--animation-plan", type=Path)
    parser.add_argument("--delivery-mode", choices=["classroom", "report"], default="classroom")
    parser.add_argument("--iteration", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    plan = read_json(args.final_slide_plan)
    animation_plan = read_json(args.animation_plan)
    findings = check_plan(plan, args.delivery_mode) + check_animation(animation_plan)
    report = summarize(findings, args.iteration)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    print(f"Wrote {args.out}")
    print(
        f"blockers={report['blocker_count']} majors={report['major_count']} "
        f"minors={report['minor_count']} stop={report['stop_condition_met']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
