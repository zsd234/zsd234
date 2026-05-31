# Template Intelligence Schemas

All coordinates are stored in EMUs and points. Element ids come from the PPTX
shape id when available. Use `slide_id + element_id` as the stable reference.

## Template Model

```json
{
  "source_pptx": "/absolute/path/template.pptx",
  "slide_size": {
    "cx_emu": 12192000,
    "cy_emu": 6858000,
    "width_pt": 960.0,
    "height_pt": 540.0,
    "aspect_ratio": 1.7778
  },
  "theme": {
    "colors": {"accent1": "4472C4"},
    "fonts": {
      "major_latin": "Aptos Display",
      "minor_latin": "Aptos"
    }
  },
  "media": [
    {
      "part": "ppt/media/image1.png",
      "sha1": "...",
      "bytes": 12345,
      "width_px": 1600,
      "height_px": 900
    }
  ],
  "slides": [
    {
      "slide_id": "slide-001",
      "slide_index": 1,
      "part": "ppt/slides/slide1.xml",
      "layout": {
        "part": "ppt/slideLayouts/slideLayout1.xml",
        "name": "Title Slide",
        "master_part": "ppt/slideMasters/slideMaster1.xml"
      },
      "layout_profile": "LayoutProfile",
      "elements": ["TemplateElement"]
    }
  ]
}
```

## LayoutProfile

```json
{
  "family": "three_point",
  "semantic_label": "content",
  "template_origin": "slide-form",
  "point_capacity": 3,
  "point_capacity_source": "repeated-text-slots",
  "text_point_slot_count": 3,
  "metric_slot_count": 0,
  "image_slot_count": 0,
  "chart_table_slot_count": 0,
  "readability": {
    "profile": "presentation-readable",
    "too_small_text": [],
    "has_font_size_risk": false
  }
}
```

`template_origin` is `embedded-layout` when the PPTX layout name or placeholder
structure is meaningful, and `slide-form` when the page uses ordinary shapes to
create a layout. Treat both as valid templates.

## TemplateElement

```json
{
  "slide_id": "slide-001",
  "element_id": "shape-4",
  "name": "Title 1",
  "type": "text",
  "placeholder": {"type": "title", "idx": "1"},
  "bbox": {
    "x_emu": 914400,
    "y_emu": 457200,
    "w_emu": 10363200,
    "h_emu": 914400,
    "x_pt": 72.0,
    "y_pt": 36.0,
    "w_pt": 816.0,
    "h_pt": 72.0
  },
  "z_order": 3,
  "text": "Template title",
  "text_runs": [
    {
      "text": "Template title",
      "font_family": "Aptos Display",
      "font_size_pt": 36.0,
      "bold": true,
      "italic": false,
      "color": {"type": "scheme", "value": "tx1"}
    }
  ],
  "paragraphs": [
    {
      "text": "Template title",
      "alignment": "ctr",
      "level": 0,
      "bullet": null
    }
  ],
  "style": {
    "font_family": "Aptos Display",
    "font_size_pt": 36.0,
    "bold": true,
    "italic": false,
    "color": {"type": "scheme", "value": "tx1"},
    "fill": null,
    "line": null
  },
  "picture": null,
  "source": "direct"
}
```

## SemanticSlot

```json
{
  "slide_id": "slide-001",
  "element_id": "shape-4",
  "role": "title",
  "confidence": 0.93,
  "evidence": ["placeholder:title", "largest-font", "top-band"],
  "constraints": {
          "max_chars": 58,
          "max_lines": 2,
          "preferred_content_shape": "short_title",
          "observed_font_size_pt": 36,
          "recommended_min_font_size_pt": 28
      }
}
```

## VisualSpec

```json
{
  "slide_id": "slide-001",
  "element_id": "shape-4",
  "resolved_style": {
    "font_family": "Aptos Display",
    "font_size_pt": 36.0,
    "bold": true,
    "color": {"type": "scheme", "value": "tx1"},
    "alignment": "ctr"
  },
  "source": "direct",
  "must_preserve": ["font_family", "color", "alignment", "bbox"],
  "editable": true,
  "risk_notes": []
}
```

## FinalSlidePlan

```json
{
  "slides": [
    {
      "output_slide_id": "out-001",
      "source_slide_id": "slide-001",
      "source_slide_index": 1,
      "purpose": "cover",
      "layout_profile": "LayoutProfile",
      "content_point_count": 3,
      "generation_strategy": {
        "mode": "use-template-slide",
        "reason": "Selected template slide can hold the planned content.",
        "requires_designer_review": false
      },
      "elements": [
        {
          "element_id": "shape-4",
          "role": "title",
          "action": "set_text",
          "text": "New deck title",
          "media_asset": null,
          "style_strategy": "inherit",
          "transform": "titleize",
          "fit": {"estimated_chars": 14, "max_chars": 58}
        }
      ]
    }
  ]
}
```
