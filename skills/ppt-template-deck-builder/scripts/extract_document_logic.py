#!/usr/bin/env python3
"""Extract a first-pass presentation outline from a document.

This is a deterministic pre-pass. The agent should still refine the outline
with judgment, but the script gives a stable JSON shape for downstream mapping.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return json.dumps(data, ensure_ascii=False, indent=2)
    if suffix == ".docx":
        return read_docx_text(path)
    return path.read_text(encoding="utf-8-sig")


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    lines: list[str] = []
    for para in root.findall(".//w:p", WORD_NS):
        texts = [node.text or "" for node in para.findall(".//w:t", WORD_NS)]
        line = "".join(texts).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def is_heading(line: str) -> bool:
    value = clean_line(line)
    if not value:
        return False
    patterns = [
        r"^#{1,6}\s+",
        r"^\d+(\.\d+)*[.)、]\s+",
        r"^[一二三四五六七八九十]+[、.]\s*",
        r"^第[一二三四五六七八九十\d]+[章节部分]\s*",
    ]
    if any(re.match(pattern, value) for pattern in patterns):
        return True
    return len(value) <= 28 and not value.endswith(("。", ".", "！", "!", "？", "?", "；", ";", "，", ","))


def heading_text(line: str) -> str:
    value = clean_line(line)
    value = re.sub(r"^#{1,6}\s+", "", value)
    value = re.sub(r"^\d+(\.\d+)*[.)、]\s+", "", value)
    value = re.sub(r"^[一二三四五六七八九十]+[、.]\s*", "", value)
    return value.strip() or "Untitled"


def is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*•·]|\d+[.)、]|[（(]?\d+[）)])\s+", line))


def bullet_text(line: str) -> str:
    return re.sub(r"^\s*(?:[-*•·]|\d+[.)、]|[（(]?\d+[）)])\s+", "", clean_line(line)).strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?；;])\s+|\n+", text)
    return [clean_line(part) for part in parts if clean_line(part)]


def keyword_guess(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", text)
    seen: set[str] = set()
    result: list[str] = []
    for word in words:
        if word in seen:
            continue
        seen.add(word)
        result.append(word)
        if len(result) >= 6:
            break
    return result


def relation_guess(title: str, points: list[dict[str, Any]]) -> str:
    joined = f"{title} " + " ".join(point.get("summary", "") for point in points)
    if re.search(r"步骤|流程|阶段|先|然后|最后|path|process|step|phase", joined, re.I):
        return "process"
    if re.search(r"对比|相比|差异|versus|vs\.?|compare|comparison", joined, re.I):
        return "comparison"
    if re.search(r"原因|驱动|导致|because|driver|why", joined, re.I):
        return "cause-effect"
    if re.search(r"时间|计划|路线图|timeline|roadmap|date|month|year", joined, re.I):
        return "timeline"
    return "list"


def logic_role(index: int, total: int, title: str) -> str:
    value = title.lower()
    if index == 0:
        return "opening"
    if index == total - 1 or re.search(r"总结|结论|行动|next|conclusion|summary", value, re.I):
        return "closing"
    if re.search(r"问题|背景|现状|challenge|context|problem", value, re.I):
        return "context"
    if re.search(r"方案|策略|路径|solution|strategy|plan", value, re.I):
        return "solution"
    if re.search(r"结果|收益|价值|impact|result|benefit", value, re.I):
        return "impact"
    return "support"


def make_point(section_id: str, index: int, raw: str) -> dict[str, Any]:
    sentences = split_sentences(raw)
    summary = sentences[0] if sentences else clean_line(raw)
    title = summary
    if len(title) > 36:
        title = title[:34].rstrip() + "..."
    return {
        "point_id": f"{section_id}-point-{index:02d}",
        "title": title,
        "summary": summary,
        "meaning": summary,
        "evidence": sentences[1:3],
        "keywords": keyword_guess(raw),
    }


def parse_sections(text: str) -> list[dict[str, Any]]:
    lines = [line.rstrip() for line in text.splitlines()]
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    buffer: list[str] = []

    def flush_buffer() -> None:
        nonlocal buffer, current
        if current is None or not buffer:
            buffer = []
            return
        block = "\n".join(buffer).strip()
        if block:
            current.setdefault("blocks", []).append(block)
        buffer = []

    for line in lines:
        stripped = clean_line(line)
        if not stripped:
            flush_buffer()
            continue
        if is_heading(stripped):
            flush_buffer()
            current = {"title": heading_text(stripped), "blocks": []}
            sections.append(current)
        elif current is None:
            current = {"title": "Overview", "blocks": []}
            sections.append(current)
            buffer.append(stripped)
        elif is_bullet(stripped):
            flush_buffer()
            current.setdefault("blocks", []).append(bullet_text(stripped))
        else:
            buffer.append(stripped)
    flush_buffer()
    if not sections and text.strip():
        sections.append({"title": "Overview", "blocks": [text.strip()]})
    return sections


def outline_from_text(path: Path, text: str) -> dict[str, Any]:
    sections_raw = parse_sections(text)
    deck_title = sections_raw[0]["title"] if sections_raw else path.stem
    sections = []
    slides = []
    for idx, section in enumerate(sections_raw):
        section_id = f"section-{idx + 1:02d}"
        blocks = section.get("blocks") or []
        if not blocks:
            blocks = [section["title"]]
        points = [make_point(section_id, point_idx, block) for point_idx, block in enumerate(blocks, start=1)]
        relation = relation_guess(section["title"], points)
        role = logic_role(idx, len(sections_raw), section["title"])
        section_obj = {
            "section_id": section_id,
            "title": section["title"],
            "logic_role": role,
            "relation": relation,
            "points": points,
        }
        sections.append(section_obj)
        slides.append(
            {
                "id": f"slide-{idx + 1:03d}",
                "title": section["title"],
                "logic_role": role,
                "relation": relation,
                "points": points,
                "bullets": [point["summary"] for point in points],
            }
        )
    return {
        "source_document": str(path.resolve()),
        "title": deck_title,
        "narrative_arc": " -> ".join(section["title"] for section in sections[:6]),
        "sections": sections,
        "slides": slides,
        "review_questions": [
            "Are any points duplicates that should be merged?",
            "Does each slide title state the point, not only the topic?",
            "Can any dense section be split into a 2-point, 3-point, or 4-point template page?",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract presentation logic from a text, Markdown, JSON, or DOCX document.")
    parser.add_argument("document", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    text = read_text(args.document)
    outline = outline_from_text(args.document, text)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(outline, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    print(f"Wrote {args.out}")
    print(f"Sections: {len(outline['sections'])}; planned slides: {len(outline['slides'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
