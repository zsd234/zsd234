# Animation, Readability, And Iterative QA

Use this reference when the deck is meant for classroom delivery, live
presentation, lecture, training, or any mode where content must be readable from
a projected screen.

## Readability Rules

Use the template's typography hierarchy, but do not preserve unreadable text
sizes for newly generated content.

Recommended minimums for screen presentation:

- Cover title: `44-60pt`
- Section title: `38-52pt`
- Slide title: `30-40pt`
- Subtitle: `22-28pt`
- Body and bullet text: target `28-32pt` for classroom, minimum `28pt` for
  core teaching content, and `18-24pt` for report decks
- Card body: `18-22pt`, only when text is short
- Metric value: `34-54pt`
- Metric label: `16-22pt`
- Caption/source/footer: `9-12pt`, not core teaching content

Hard rules:

- Do not put important course content below the delivery-mode minimum. If the
  template uses tiny document-like text, enlarge, split, or move details to
  speaker notes.
- Avoid more than 6 bullets on one slide.
- Prefer 2-4 points per slide for teaching decks.
- Keep classroom slides below about 9 total text lines.
- Use speaker notes for nuance that does not fit visually.
- If text only fits by shrinking below the minimum, rewrite, split, or choose a
  different layout.
- Each point should usually be one short sentence, not a paragraph.

## Animation Strategy

Animation should support explanation order, not decorate the slide.

Default animation families:

- Title and subtitle: subtle `fade`.
- Bullets: `appear-by-paragraph`, one point per click in classroom mode.
- Metrics: `zoom-fade` or `fade`, after the title.
- Charts: `wipe-left-to-right` for time/flow, `fade` for static comparisons.
- Images: `fade`, usually with previous or immediately after title.
- Process/timeline steps: reveal step-by-step in reading order.
- Minimal mode: no object-level animation; preserve only safe existing template
  transitions if they do not distract.
- Executive/report mode: avoid paragraph-by-paragraph reveals unless the content
  needs staged interpretation.

Never animate:

- logos
- footers
- page numbers
- source notes
- decorative lines or background shapes
- every object individually just because it exists

Use `scripts/build_animation_plan.py` to create `animation_plan.json` from
`final_slide_plan.json`. If the generation runtime can safely write PowerPoint
animation XML, apply the plan by element id. If it cannot, preserve existing
template animations and deliver the animation plan as implementation guidance
rather than faking animations with rasterized text.

## QA Loop

Run this loop until there are no blocker or major findings:

1. Package check.
   - PPTX exists and opens.
   - Slide count matches the plan.
   - No empty media files or broken relationships.
   - Run `scripts/qa_pptx_package.py` and fix major findings before delivery.
   - Run `scripts/qa_accessibility_structure.py` and fix major findings before
     delivery.

2. Template fidelity check.
   - Same theme, major fonts, colors, footers, logos, page markers, and visual
     chrome unless intentionally changed.
   - Source slide or variant parent recorded for every output slide.

3. Content logic check.
   - Each slide has one clear claim.
   - The number of points matches the selected layout capacity.
   - No slide contains unrelated points only because they were nearby in the
     source document.
   - The narrative arc is visible from the slide titles alone.

4. Readability check.
   - Important body/bullet content meets the minimum font size.
   - Text does not overflow, clip, collide, or sit against edges.
   - Dense text was rewritten or split instead of shrunk.
   - Titles are present, unique, and short enough to scan.
   - Core content is not hidden in captions, source notes, or footers.

5. Visual balance check.
   - No empty card slots unless the design intentionally supports them.
   - Images are not stretched and subject crops are sensible.
   - Repeated cards/metrics/steps align and share style.
   - Charts use direct labels where possible, do not rely only on color, and
     avoid 3D effects or decorative chartjunk.
   - Text over images has a reliable contrast treatment.

6. Animation check.
   - Animation order matches teaching or speaking order.
   - Bullet reveals are not too slow.
   - No decorative object receives its own animation.
   - Existing template animations are preserved unless they conflict with the
     new semantic order.
   - Minimal mode has no newly generated object-level animation.

7. Accessibility check.
   - Every slide has a title, visible or intentionally hidden for accessibility.
   - Visuals and charts have alt text or are marked decorative.
   - Reading order follows the visual and speaking order.
   - Decorative objects are excluded from reading order.
   - Color is not the only signal for categories, status, or chart series.

8. Rehearsal and handout check.
   - Speaker notes contain concise delivery support, not pasted source text.
   - Any required handout/PDF version is generated after animation decisions.
   - Expected timing and click count are reasonable for the session.
   - Videos, fonts, and links are tested on the presentation machine when
     possible.

9. Self-question pass.
   - What is the one sentence this slide proves?
   - Is any text smaller than the audience can read?
   - Did the selected template page actually have enough slots?
   - Would a human designer split or merge this slide?
   - Is any generated variant visibly outside the template's design system?

Stop only when:

- no blocker findings remain
- no major findings remain
- any minor findings are documented as acceptable tradeoffs
- the rendered deck passes both thumbnail and full-size inspection
