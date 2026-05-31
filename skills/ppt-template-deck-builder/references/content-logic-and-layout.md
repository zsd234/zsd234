# Content Logic And Layout Matching

Use this reference when the user provides a document, notes, transcript,
article, report, or long-form text rather than already-structured slide copy.

## Document Logic Workflow

1. Extract raw text.
   - Use `scripts/extract_document_logic.py` for `.txt`, `.md`, `.json`, and
     `.docx` inputs.
   - For PDFs or scanned sources, extract text with the best available document
     tool, then pass the text into the same outline workflow.

2. Build `content_outline.json`.
   - Identify sections, headings, paragraphs, bullets, tables, metrics, and
     images.
   - Group adjacent paragraphs into points when they share a subject, evidence,
     or transition.
   - Assign each section a logic role: `opening`, `context`, `problem`,
     `solution`, `evidence`, `impact`, `summary`, or `closing`.
   - Assign each section a relation: `list`, `process`, `comparison`,
     `cause-effect`, `timeline`, `case-study`, or `argument`.

3. Rewrite into slide-ready units.
   - Convert a section into 1 slide when it has 2-4 concise points.
   - Split a section when it has more than 4 points or mixed logic.
   - Merge sections when each has only a weak single point and the template has
     a 2-point or 3-point layout.
   - Every point needs `title`, `summary`, `meaning`, `evidence`, and
     `keywords`.

4. Match content needs to template capacity.
   - A 2-point section should prefer `two_point`, comparison, or image/text
     split pages.
   - A 3-point section should prefer `three_point`, three-card, three-step, or
     metric-card pages.
   - A 4-point section should prefer `four_point`, 2x2, quadrant, or four-card
     pages.
   - A 5+ point section should use `five_plus_list`, split across pages, or be
     rewritten into fewer grouped points.
   - Process and timeline content must prioritize step/timeline slots over
     generic bullet slots.
   - Metrics must prioritize `metric_value` and `metric_label` pairs.

5. Create missing layouts only when needed.
   - If no exact template page exists, first choose the closest page with the
     right visual grammar.
   - Duplicate it as a variant and add or remove repeated groups using the same
     grid, font hierarchy, color tokens, line style, icon style, and spacing.
   - Record the change in `decision_records.json` with the reason and the
     source slide used as the parent.
   - Do not invent a new visual system merely because the exact capacity does
     not exist.

## Content Outline Schema

```json
{
  "source_document": "/absolute/path/source.docx",
  "title": "Deck title",
  "narrative_arc": "Context -> Problem -> Solution -> Impact",
  "sections": [
    {
      "section_id": "section-01",
      "title": "Customer pain is concentrated in onboarding",
      "logic_role": "problem",
      "relation": "cause-effect",
      "points": [
        {
          "point_id": "section-01-point-01",
          "title": "Setup takes too long",
          "summary": "New customers spend two weeks on manual setup.",
          "meaning": "Time-to-value is the main adoption bottleneck.",
          "evidence": ["Support tickets mention setup delays."],
          "keywords": ["setup", "time-to-value"]
        }
      ]
    }
  ],
  "slides": [
    {
      "id": "slide-001",
      "title": "Customer pain is concentrated in onboarding",
      "logic_role": "problem",
      "relation": "cause-effect",
      "points": [],
      "bullets": []
    }
  ],
  "review_questions": []
}
```

## Layout Taxonomy

Use two labels for each source slide:

- `slide_purpose`: `cover`, `toc`, `section_divider`, `content`, `summary`,
  `case_study`, `comparison`, `process`, `timeline`, `data_chart`, `metrics`,
  `image_heavy`, `quote`, or `closing`.
- `layout_family`: `one_column_text`, `two_point`, `three_point`,
  `four_point`, `five_plus_list`, `image_text_split`, `image_grid`,
  `metric_cards`, `process_steps`, `timeline_nodes`, `table_matrix`,
  `chart_with_callouts`, `quote_editorial`, or `freeform_canvas`.

Do not trust the PowerPoint layout name alone. Many template libraries use blank
slides with manually placed elements. Infer the layout from visible/editable
content slots, repeated geometry, and actual styles.

## Capacity Rules

- Exclude logos, page numbers, footers, source notes, decorative lines, and
  background images from content capacity.
- Detect repeated structures: equal-size cards, equal-width columns, aligned
  image/text pairs, repeated metric groups, numbered steps, and timeline nodes.
- `point_capacity = 2`: two balanced columns/cards/blocks or comparison sides.
- `point_capacity = 3`: three equal cards/columns/steps/metrics.
- `point_capacity = 4`: 2x2 grid, four cards, four quadrants, or four steps.
- `point_capacity > 4`: large list or dense matrix page.
- A single large body slot is `flexible`, not a safe 4-point card layout.
- Estimate bullet capacity as slide-safe points, not just raw line count. One
  point should usually consume 1-2 lines.
- Use a safety factor around `0.8` when estimating character capacity so text
  does not sit against frame edges.

## Matching Rules

Score candidate slides by:

- purpose match
- exact point capacity match
- slot type match for image, metric, process, chart, or table content
- estimated text fit
- visual rhythm against neighboring slides
- semantic confidence
- risk of overwriting footer/logo/source/decorative elements

When the needed point count exceeds capacity, split the content or create a
template-consistent variant. Do not force 4 points into a 3-card page.
