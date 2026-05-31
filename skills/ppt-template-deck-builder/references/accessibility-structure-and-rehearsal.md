# Accessibility Structure And Rehearsal

Use this reference after the visual deck is assembled and before final delivery.
It covers structural accessibility, slide-master discipline, presenter notes,
handouts, and rehearsal readiness.

## Structural Accessibility

Rules:

- Every slide needs a unique title. If the visual design should not show a
  title, add an off-slide or hidden accessibility title.
- Meaningful images, screenshots, icons, charts, and diagrams need alt text.
  Pure decoration should be marked decorative.
- Reading order should follow the real speaking and viewing order: title first,
  primary visual or claim support next, details last.
- Decorative shapes should not appear in the reading order.
- Do not rely only on automated accessibility checks. They are useful but do
  not prove that alt text is meaningful or reading order is correct.
- Items placed directly on the slide master may be unavailable to assistive
  technology. Put meaningful content on slides or layouts as placeholders where
  possible.

Run:

```bash
python "$SKILL_DIR/scripts/qa_accessibility_structure.py" \
  "$FINAL_PPTX" \
  --out "$WORKSPACE/qa_accessibility_report.json" \
  --pretty
```

Fix major findings before delivery unless the user explicitly accepts the risk.

## Slide Master And Placeholder Discipline

Rules:

- Prefer true placeholders for reusable content regions; they carry formatting
  and help PowerPoint map content between layouts.
- Do not place editable content as static text on the top master when it should
  change per slide.
- Preserve the template's master/layout relationships unless generating a
  deliberate variant.
- When creating a variant, derive it from the nearest existing layout and keep
  title, body, footer, logo, and page-number zones consistent.
- Re-test copied slides because copy/paste and layout remapping can change text
  flow and placeholder behavior.

## Speaker Notes

Use speaker notes for:

- explanation that would make the slide too dense
- source nuance
- definitions and examples
- verbal transitions between slides
- presenter prompts for classroom interaction

Do not use speaker notes as a dumping ground for unprocessed source text. Notes
should be short enough to support delivery without becoming a script dependency.

## Handouts And PDF Export

Create a handout or PDF version when:

- the audience needs detailed tables, citations, or step-by-step instructions
- the slide deck is used as course material after class
- animations or videos may not survive the delivery environment
- the user asks for printable or LMS-ready material

Before PDF/handout export:

- verify slide titles and reading order
- ensure charts and images have text summaries
- expand or remove animations that hide required content
- include source notes and speaker notes when they are part of the deliverable

## Rehearsal Readiness

Check:

- expected time per slide
- animation click count
- whether any slide requires the speaker to read dense text aloud
- whether speaker notes are concise enough to glance at
- whether transitions between sections are explicit
- whether videos, audio, fonts, and external links work on the presentation
  machine

If the deck is for live teaching, prefer a clear explanation rhythm over visual
novelty. If the deck is for self-study, use fewer animations and stronger slide
titles because the speaker will not be present to supply context.
