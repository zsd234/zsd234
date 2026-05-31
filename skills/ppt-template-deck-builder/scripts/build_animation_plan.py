#!/usr/bin/env python3
"""Create a conservative animation plan from a final slide plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROLE_ORDER = {
    "title": 10,
    "subtitle": 20,
    "image_hero": 25,
    "image_content": 30,
    "metric_value": 35,
    "metric_label": 36,
    "chart": 40,
    "table": 40,
    "bullets": 50,
    "body": 50,
    "caption": 70,
}


ROLE_EFFECT = {
    "title": {"effect": "fade", "duration_ms": 350},
    "subtitle": {"effect": "fade", "duration_ms": 300},
    "bullets": {"effect": "appear-by-paragraph", "duration_ms": 250},
    "body": {"effect": "fade", "duration_ms": 250},
    "metric_value": {"effect": "zoom-fade", "duration_ms": 350},
    "metric_label": {"effect": "fade", "duration_ms": 200},
    "image_hero": {"effect": "fade", "duration_ms": 300},
    "image_content": {"effect": "fade", "duration_ms": 250},
    "chart": {"effect": "wipe-left-to-right", "duration_ms": 500},
    "table": {"effect": "fade", "duration_ms": 300},
    "caption": {"effect": "fade", "duration_ms": 200},
}

MODE_LIMITS = {
    "classroom": {"max_animated_elements": 5, "transition": "fade", "body_reveal": "by_paragraph"},
    "executive": {"max_animated_elements": 4, "transition": "fade", "body_reveal": "all_at_once"},
    "minimal": {"max_animated_elements": 0, "transition": "none", "body_reveal": "none"},
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def animation_for_element(element: dict[str, Any], index: int, mode: str) -> dict[str, Any] | None:
    action = element.get("action")
    role = element.get("role")
    if mode == "minimal":
        return None
    if action not in {"set_text", "set_image"}:
        return None
    effect = ROLE_EFFECT.get(role, {"effect": "fade", "duration_ms": 250})
    trigger = "on-click" if mode == "classroom" and role in {"bullets", "body", "chart", "table"} else "with-previous"
    item = {
        "element_id": element.get("element_id"),
        "role": role,
        "order": index,
        "trigger": trigger,
        "effect": effect["effect"],
        "duration_ms": effect["duration_ms"],
        "delay_ms": 0 if index <= 2 else 80,
    }
    if role == "bullets" and mode == "classroom":
        item["paragraph_mode"] = "one-point-per-click"
    return item


def build_animation_plan(plan: dict[str, Any], mode: str) -> dict[str, Any]:
    slides = []
    for slide in plan.get("slides", []):
        animatable = [
            element
            for element in slide.get("elements", [])
            if element.get("action") in {"set_text", "set_image"}
        ]
        animatable.sort(key=lambda element: ROLE_ORDER.get(element.get("role"), 90))
        sequence = []
        for idx, element in enumerate(animatable, start=1):
            item = animation_for_element(element, idx, mode)
            if item:
                sequence.append(item)
        slides.append(
            {
                "output_slide_id": slide.get("output_slide_id"),
                "source_slide_id": slide.get("source_slide_id"),
                "animation_style": mode,
                "transition": MODE_LIMITS[mode]["transition"],
                "max_animated_elements": MODE_LIMITS[mode]["max_animated_elements"],
                "body_reveal": MODE_LIMITS[mode]["body_reveal"],
                "sequence": sequence,
                "rules": [
                    "Do not animate footers, logos, page numbers, or decorative chrome.",
                    "Use at most one primary animation family per slide.",
                    "Reveal bullets by paragraph only when the presentation is taught or narrated live.",
                ],
            }
        )
    return {
        "source_plan": plan.get("source_template"),
        "mode": mode,
        "slides": slides,
        "implementation_notes": [
            "Preserve existing template animations when they already match the semantic order.",
            "When using a generator that can write PowerPoint animation XML, apply this plan to editable elements by element id.",
            "If the runtime cannot safely write animations, deliver the PPTX without fake raster animations and include this plan for manual application.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a conservative animation plan from final_slide_plan.json.")
    parser.add_argument("final_slide_plan", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mode", choices=["classroom", "executive", "minimal"], default="classroom")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    plan = read_json(args.final_slide_plan)
    animation_plan = build_animation_plan(plan, args.mode)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(animation_plan, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    print(f"Wrote {args.out}")
    print(f"Animation slides planned: {len(animation_plan['slides'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
