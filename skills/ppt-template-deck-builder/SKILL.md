---
name: ppt-template-deck-builder
description: Analyze user-provided PowerPoint (.pptx) templates and generate polished editable decks from documents or user content while preserving template structure, typography, image slots, semantic placeholders, master layouts, animations, and visual style. Use when Codex must inspect a PPT template, infer text box/image frame meaning, identify inner-page layout types and 2/3/4-point capacity even without embedded layouts, extract document logic into slide points, map content into a template, create missing template-consistent variants, add presentation-safe animations, enforce readable classroom/report font sizes, or create a human-quality PPTX from a specific template.
---

# PPT Template Deck Builder

Use this skill when the template is the product constraint. The goal is not to
make a similar-looking deck from scratch; it is to understand the supplied PPTX
as a reusable design system, map user content into its real semantic slots, and
deliver an editable PowerPoint that looks manually adapted.

If the task requires final PPTX export and the `Presentations` skill is
available, use it for high-polish editable deck creation and render QA. Use this
skill first to produce the template intelligence artifacts that drive that
build.

## Operating Rules

- Inspect the PPTX before planning content. Do not infer layout rules from
  screenshots alone.
- Treat extracted slide, element, and relationship ids as the stable source of
  truth.
- Preserve master layouts, theme colors, fonts, logo zones, footers, slide
  numbers, decorative elements, z-order, and image crop language unless the user
  explicitly asks to change them.
- Detect actual slide form, not only embedded PowerPoint layouts. A blank-layout
  slide with three visible cards is still a `three_point` content layout.
- Prefer adapting content over damaging the template. Summarize, split,
  titleize, bulletize, or omit material before forcing long text into a small
  slot.
- For classroom or live teaching decks, keep core body/bullet text readable from
  projection; do not shrink important content below the delivery-mode minimum.
- Add animations only when they support explanation order. Do not animate logos,
  footers, page numbers, backgrounds, or decorative chrome.
- Keep final text editable. Avoid rasterizing text or rebuilding template
  decoration as flat images.
- Render and inspect the result before delivery. A generated PPTX is not done
  until obvious overflow, clipping, image distortion, empty placeholders, small
  unreadable core text, animation overuse, and semantic mismatches are fixed.

## Workspace

Create a task workspace and keep intermediate JSON, screenshots, drafts, and QA
reports there:

```text
WORKSPACE=<cwd>/outputs/<task-slug>/ppt-template-deck-builder
MODEL_JSON=$WORKSPACE/template_model.json
SEMANTICS_JSON=$WORKSPACE/template_semantics.json
CONTENT_JSON=$WORKSPACE/content.json
PLAN_JSON=$WORKSPACE/final_slide_plan.json
OUTLINE_JSON=$WORKSPACE/content_outline.json
ANIMATION_JSON=$WORKSPACE/animation_plan.json
QA_JSON=$WORKSPACE/qa_report.json
ACCESSIBILITY_QA_JSON=$WORKSPACE/qa_accessibility_report.json
```

Use absolute paths in commands and handoffs.

## Workflow

1. Extract the template model.

   ```bash
   python "$SKILL_DIR/scripts/extract_template_model.py" \
     "template.pptx" \
     --out "$MODEL_JSON"
   ```

   This reads the PPTX package directly and records slide size, theme tokens,
   masters/layouts, media, element ids, bounding boxes, text runs, style hints,
   pictures, crops, and z-order.

2. Classify template semantics.

   ```bash
   python "$SKILL_DIR/scripts/classify_template_semantics.py" \
     "$MODEL_JSON" \
     --out "$SEMANTICS_JSON"
   ```

   Treat the output as a first-pass map. Revise it with model judgment and
   rendered screenshots when the template uses unusual visual language.

3. Use subagents when explicitly authorized.

   If the user asks for multi-agent work, delegation, or parallel agents, split
   the job using `references/multi-agent-workflow.md`. The main agent owns final
   decisions and integration. If subagents are unavailable or not authorized,
   perform the same roles sequentially.

4. Extract document logic when the user provides a document or long text.

   ```bash
   python "$SKILL_DIR/scripts/extract_document_logic.py" \
     "source.docx" \
     --out "$OUTLINE_JSON"
   ```

   Use the output as a draft. Refine it with model judgment so the deck is built
   around the document's real logic: sections, points, meaning, evidence,
   relation, and narrative role. Do not mechanically paste paragraphs into
   slides.

   Read `references/content-logic-and-layout.md` when the source is a document,
   report, transcript, article, course material, or any dense text.

5. Normalize user content.

   Convert the user's text, images, metrics, and section requirements into a
   structured JSON file. Prefer this shape:

   ```json
   {
     "title": "Deck title",
     "audience": "Audience",
     "slides": [
       {
         "title": "Slide claim",
         "subtitle": "Optional subtitle",
         "points": [
           {
             "title": "Point title",
             "summary": "Point summary",
             "meaning": "What this point means"
           }
         ],
         "bullets": ["Point one", "Point two"],
         "body": "Optional paragraph",
         "metrics": [{"label": "Revenue", "value": "$12M"}],
         "images": [{"path": "/absolute/path/image.png", "role": "hero"}]
       }
     ]
   }
   ```

6. Build a first-pass slide plan.

   ```bash
   python "$SKILL_DIR/scripts/build_deck_plan.py" \
     "$CONTENT_JSON" \
     "$SEMANTICS_JSON" \
     --out "$PLAN_JSON"
   ```

   Use this plan as a draft, not as an unquestioned answer. Review every mapping
   from user content to slide element. Confirm that each content slide's point
   count matches the selected template slide's `layout_profile.point_capacity`.
   If no exact slide exists, split content or create a template-consistent
   variant from the closest source slide.

7. Create the animation plan when requested or useful for live presentation.

   ```bash
   python "$SKILL_DIR/scripts/build_animation_plan.py" \
     "$PLAN_JSON" \
     --mode classroom \
     --out "$ANIMATION_JSON"
   ```

   Use `classroom` for teaching/course display, `executive` for subtle report
   delivery, and `minimal` when playback compatibility matters. Apply animations
   only if the PPTX generation path can safely preserve editable elements and
   valid PowerPoint animation data.

8. Generate the deck from the template.

   For production-quality template following, duplicate/import the starter PPTX
   and edit copied elements in place. Preserve geometry and inherited styles.
   Use the plan to decide which source slide each output slide uses and which
   element ids receive text, media, charts, animation, or preservation rules.
   For missing layouts, generate a variant by copying the nearest template page
   and deriving new repeated groups from existing geometry, typography, spacing,
   and color tokens. Record the variant in `decision_records.json`.

   For simple text-only edits, direct OOXML patching is acceptable if it keeps
   the package valid. For high-polish or multi-slide generation, prefer the
   `Presentations` skill exact clone/edit path when available.

9. Render and review.

   Render every output slide to images using the best available renderer in the
   environment. Inspect the contact sheet and full-size slides. Run the
   iterative QA loop in `references/animation-readability-qa.md`. Fix blocker
   and major issues before delivery.

10. Check delivery compatibility for final PPTX files.

   ```bash
   python "$SKILL_DIR/scripts/qa_pptx_package.py" \
     "$FINAL_PPTX" \
     --out "$WORKSPACE/qa_package_report.json"
   ```

   Use `references/delivery-compatibility.md` to fix file size, missing-font,
   linked-asset, media, and playback risks.

11. Check accessibility structure and rehearsal readiness.

   ```bash
   python "$SKILL_DIR/scripts/qa_accessibility_structure.py" \
     "$FINAL_PPTX" \
     --out "$ACCESSIBILITY_QA_JSON"
   ```

   Use `references/accessibility-structure-and-rehearsal.md` to fix slide
   titles, alt text, reading-order risk, placeholder/master issues, speaker
   notes, handouts, and rehearsal checks.

## Semantic Rules

Use these conflict rules when model judgment, script output, and user content
disagree:

- Template structure is authoritative for element identity and geometry.
- Template styles are authoritative unless minimal shrinkage is needed to avoid
  overflow.
- Semantic roles with confidence below `0.5` must not drive destructive edits.
- Title slots carry the slide claim, not long prose.
- Metric slots carry numbers, percentages, dates, or compact labels.
- Image slots carry images or charts, not paragraphs.
- Small footer/caption slots do not carry body copy.
- A 2-point section should use a 2-point/comparison/image-text layout; a
  3-point section should use a 3-card/3-step/3-metric layout; a 4-point section
  should use a 4-card/2x2/quadrant layout. Split or create a variant instead of
  hard-stuffing content into the wrong capacity.
- Decorative elements are preserved unless the user explicitly asks to remove
  or replace them.
- When uncertain whether an element is meaningful or decorative, preserve it.

## Required Artifacts

Create or maintain these artifacts for substantial template-following work:

- `template_model.json`: extracted PPTX structure and style facts.
- `template_semantics.json`: semantic roles, confidence, and visual specs.
- `content.json`: normalized user content.
- `content_outline.json`: document logic, points, evidence, and narrative plan
  when the source starts as a document.
- `final_slide_plan.json`: one integrated mapping for all output slides.
- `animation_plan.json`: semantic animation order and effect guidance.
- `decision_records.json`: conflicts and why the final choice was made.
- `qa_report.json`: render and package findings.
- `qa_package_report.json`: PPTX package, media, font, and external-link risks
  when a final PPTX exists.
- `qa_accessibility_report.json`: slide title, alt text, and reading-order
  findings when a final PPTX exists.

See `references/template-schema.md` for field definitions and
`references/template-heuristics.md` for role and fit heuristics. See
`references/content-logic-and-layout.md` for document-to-slide logic and
missing layout variants. See `references/animation-readability-qa.md` for
animation, font-size, and iteration standards. See
`references/ppt-common-problems-playbook.md` for source-informed fixes to common
PPT problems such as dense slides, tiny text, weak claims, chart issues,
animation overuse, and accessibility gaps. See
`references/delivery-compatibility.md` before final delivery across devices.
See `references/accessibility-structure-and-rehearsal.md` for slide structure,
speaker notes, handouts, and rehearsal readiness.

## Delivery Standard

The final deck must be editable, visually consistent with the supplied template,
concise enough for the slots it uses, and free of obvious placeholder artifacts.
It must also respect the requested delivery mode: classroom/course decks need
larger readable type and stepwise reveals, while executive/report decks need
subtle animation and tighter density. If a template cannot support part of the
requested content, split the content or create a template-consistent variant;
do not invent an unrelated design system.
