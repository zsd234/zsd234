#!/usr/bin/env python3
"""Inspect a PPTX package for delivery and compatibility risks."""

from __future__ import annotations

import argparse
import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

from lxml import etree

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

COMMON_FONTS = {
    "arial",
    "aptos",
    "aptos display",
    "calibri",
    "cambria",
    "georgia",
    "helvetica",
    "segoe ui",
    "tahoma",
    "times new roman",
    "verdana",
    "microsoft yahei",
    "microsoft jhenghei",
    "dengxian",
    "simsun",
    "simhei",
    "pingfang sc",
    "noto sans cjk sc",
    "source han sans sc",
}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
VECTOR_EXTS = {".svg", ".emf", ".wmf"}
VIDEO_AUDIO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".wmv", ".mp3", ".wav", ".m4a", ".wma"}


def mb(value: int) -> float:
    return round(value / (1024 * 1024), 2)


def finding(severity: str, issue: str, fix: str, part: str | None = None) -> dict[str, Any]:
    return {"severity": severity, "part": part, "issue": issue, "proposed_fix": fix}


def read_xml(zf: zipfile.ZipFile, part: str) -> etree._Element | None:
    try:
        return etree.fromstring(zf.read(part))
    except Exception:
        return None


def collect_external_rels(zf: zipfile.ZipFile) -> list[dict[str, str | None]]:
    external = []
    for name in zf.namelist():
        if not name.endswith(".rels"):
            continue
        root = read_xml(zf, name)
        if root is None:
            continue
        for rel in root.findall("rel:Relationship", namespaces=NS):
            if rel.get("TargetMode") == "External":
                external.append(
                    {
                        "rels_part": name,
                        "id": rel.get("Id"),
                        "type": rel.get("Type"),
                        "target": rel.get("Target"),
                    }
                )
    return external


def collect_fonts(zf: zipfile.ZipFile) -> list[str]:
    fonts: set[str] = set()
    for name in zf.namelist():
        if not (name.startswith("ppt/slides/") or name.startswith("ppt/slideMasters/") or name.startswith("ppt/slideLayouts/") or name.startswith("ppt/theme/")):
            continue
        if not name.endswith(".xml"):
            continue
        root = read_xml(zf, name)
        if root is None:
            continue
        for tag in ("latin", "ea", "cs"):
            for node in root.findall(f".//a:{tag}", namespaces=NS):
                face = node.get("typeface")
                if face and not face.startswith("+"):
                    fonts.add(face)
    return sorted(fonts, key=str.lower)


def collect_media(zf: zipfile.ZipFile) -> list[dict[str, Any]]:
    media = []
    for name in sorted(n for n in zf.namelist() if n.startswith("ppt/media/") and not n.endswith("/")):
        data = zf.read(name)
        suffix = Path(name).suffix.lower()
        item: dict[str, Any] = {
            "part": name,
            "extension": suffix,
            "bytes": len(data),
            "mb": mb(len(data)),
            "kind": "other",
        }
        if suffix in IMAGE_EXTS or suffix in VECTOR_EXTS:
            item["kind"] = "image"
            if Image is not None and suffix in IMAGE_EXTS:
                try:
                    with Image.open(BytesIO(data)) as img:
                        item["width_px"] = img.width
                        item["height_px"] = img.height
                        item["format"] = img.format
                        item["megapixels"] = round((img.width * img.height) / 1_000_000, 2)
                except Exception:
                    item["image_read_error"] = True
        elif suffix in VIDEO_AUDIO_EXTS:
            item["kind"] = "video_audio"
        media.append(item)
    return media


def embedded_font_parts(zf: zipfile.ZipFile) -> list[str]:
    return [
        name
        for name in zf.namelist()
        if name.startswith("ppt/fonts/") or Path(name).suffix.lower() in {".fntdata", ".odttf"}
    ]


def analyze(pptx: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    with zipfile.ZipFile(pptx) as zf:
        media = collect_media(zf)
        fonts = collect_fonts(zf)
        font_parts = embedded_font_parts(zf)
        external = collect_external_rels(zf)

    package_bytes = pptx.stat().st_size
    media_bytes = sum(item["bytes"] for item in media)
    image_count = sum(1 for item in media if item["kind"] == "image")
    video_audio_count = sum(1 for item in media if item["kind"] == "video_audio")

    if package_bytes > 80 * 1024 * 1024:
        findings.append(finding("major", f"PPTX package is very large ({mb(package_bytes)} MB).", "Compress images/media, remove unused assets, and verify upload/email limits."))
    elif package_bytes > 30 * 1024 * 1024:
        findings.append(finding("minor", f"PPTX package is large ({mb(package_bytes)} MB).", "Consider image compression and removing unused media before sharing."))

    if media_bytes > 50 * 1024 * 1024:
        findings.append(finding("major", f"Embedded media totals {mb(media_bytes)} MB.", "Compress high-resolution images/videos or link to externally hosted video when appropriate."))

    for item in media:
        if item["kind"] == "image":
            if item["bytes"] > 10 * 1024 * 1024:
                findings.append(finding("minor", f"Large image asset ({item['mb']} MB).", "Crop/compress to the maximum display size needed for the slide.", item["part"]))
            width = item.get("width_px")
            height = item.get("height_px")
            if isinstance(width, int) and isinstance(height, int):
                if width < 640 or height < 360:
                    findings.append(finding("minor", f"Low-pixel image ({width}x{height}).", "Use a higher-resolution source if this image is displayed larger than an icon.", item["part"]))
                if width * height > 20_000_000:
                    findings.append(finding("minor", f"Oversized raster image ({width}x{height}).", "Downsample/crop the image to reduce file size without visible loss.", item["part"]))
        elif item["kind"] == "video_audio" and item["bytes"] > 50 * 1024 * 1024:
            findings.append(finding("major", f"Large video/audio asset ({item['mb']} MB).", "Compress media or verify playback and sharing constraints.", item["part"]))

    if external:
        findings.append(finding("major", f"{len(external)} external relationship(s) found.", "Embed required assets or verify links work offline and during presentation."))

    if font_parts:
        findings.append(finding("minor", f"{len(font_parts)} embedded font part(s) found.", "Verify font licensing and file size impact; consider common fonts for broad compatibility."))

    uncommon = [font for font in fonts if font.lower() not in COMMON_FONTS]
    if uncommon and not font_parts:
        findings.append(
            finding(
                "minor",
                f"Non-common fonts used without detected embedding: {', '.join(uncommon[:8])}.",
                "Verify target machines have these fonts, embed them if allowed, or substitute compatible fonts.",
            )
        )

    blocker = sum(1 for item in findings if item["severity"] == "blocker")
    major = sum(1 for item in findings if item["severity"] == "major")
    minor = sum(1 for item in findings if item["severity"] == "minor")
    return {
        "pptx": str(pptx.resolve()),
        "package_mb": mb(package_bytes),
        "media_mb": mb(media_bytes),
        "image_count": image_count,
        "video_audio_count": video_audio_count,
        "font_count": len(fonts),
        "fonts": fonts,
        "embedded_font_parts": font_parts,
        "external_relationships": external,
        "media": media,
        "blocker_count": blocker,
        "major_count": major,
        "minor_count": minor,
        "stop_condition_met": blocker == 0 and major == 0,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect PPTX package compatibility, media, fonts, and sharing risks.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = analyze(args.pptx)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    print(f"Wrote {args.out}")
    print(
        f"package={report['package_mb']}MB media={report['media_mb']}MB "
        f"majors={report['major_count']} minors={report['minor_count']} stop={report['stop_condition_met']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
