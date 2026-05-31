# Template Heuristics

Use these heuristics as evidence, not as absolute rules. Screenshots and the
PPTX element model together are stronger than either source alone.

## Slide Type

- `cover`: early slide, one dominant title, optional subtitle/date/author, and
  a large hero image or open background.
- `toc`: repeated short lines, section numbers, and little body prose.
- `section`: one large title or section label with sparse supporting text.
- `content`: clear title plus body, bullet, chart, table, or image slots.
- `image-heavy`: image area is a large share of slide area and text is mostly
  title/caption.
- `quote`: dominant text block with quote marks, attribution, or centered
  editorial treatment.
- `closing`: late slide with contact details, thanks, call to action, or logo
  emphasis.

## Inner Page Layout Capacity

Do not rely only on the PPTX layout name. Many templates use blank slides with
manual card, grid, and process structures.

- `two_point`: two balanced columns/cards/blocks, comparison sides, or two
  image-text pairs.
- `three_point`: three equal cards, columns, steps, icons, or metric groups.
- `four_point`: 2x2 grid, four quadrants, four cards, four steps, or four
  metric groups.
- `five_plus_list`: one large list/body area that can hold many short items.
- `image_text_split`: one dominant image slot and one text region.
- `metric_cards`: repeated large-number and label groups.
- `process_steps`: numbered nodes, arrows, or repeated step labels.
- `timeline_nodes`: date/stage nodes on a horizontal or vertical axis.
- `chart_with_callouts`: chart/table region plus labels or insight callouts.

Capacity is based on editable content slots, repeated geometry, style
consistency, and safe font size. Logos, footers, page numbers, source notes,
and decorative objects do not count as capacity.

## Text Role

- Placeholder type beats shape name. Shape name beats weak visual guesses.
- A top-band text box with the largest or second-largest font is usually a
  `title`.
- A nearby smaller text box under the title is usually a `subtitle`.
- A medium-font large-area text box is usually `body` or `bullets`.
- Multiple paragraphs or bullet markers suggest `bullets`.
- Numeric dominant text with labels nearby suggests `metric_value`.
- Very small text near the bottom is usually `footer`, `source`, page number,
  or legal note.
- Small text near an image slot is often `caption`.
- Text inside a repeated small label shape may be a `section_label`, tag, or
  navigation marker.

## Image Role

- A full-bleed or near-full-slide picture is usually `background_image`.
- The largest non-background picture is usually `image_hero`.
- Repeated same-size image boxes are usually `image_grid` or content cards.
- Small square or circular picture boxes are often `icon_slot`, avatar, or
  logo. Preserve logos unless the user explicitly asks to replace them.
- Use the template crop ratio. Do not stretch images to fill a frame.

## Capacity

- Estimate line count from frame height and line height. Use existing font size
  when present; otherwise infer from neighboring text.
- Estimate Latin text capacity with average glyph width near `0.55 * font_size`.
- Estimate CJK text capacity closer to `1.0 * font_size` per character.
- Titles should usually fit in 1-2 lines. If not, rewrite before shrinking.
- Bullets should usually be 3-6 items per slide.
- If content does not fit after concise rewriting, split the slide or choose a
  layout with a larger body slot.
- For teaching or course display, core body/bullet content should stay at
  `24pt` or larger. For ordinary report decks, avoid core body text below
  `16pt`. When the template's observed font is smaller than the delivery-mode
  minimum, preserve the style hierarchy but enlarge or split the content.

## Style Preservation

- Inherit font family, font size hierarchy, colors, alignment, bullets, margins,
  and line spacing from the template.
- Use template theme colors or directly observed colors. Avoid introducing new
  palette colors unless the user requests restyling.
- Preserve footer, logo, page marker, and decorative chrome zones.
- Only shrink text modestly for fit. Large style changes require a recorded
  reason in `decision_records.json`.

## QA Blockers

- Text overflows, clips, or visibly crowds frame edges.
- Text is mapped to the wrong semantic slot.
- A footer, logo, page number, or decoration was overwritten unintentionally.
- A picture is stretched, low-resolution, semantically wrong, or cropped through
  the subject.
- Slide rhythm repeats a source layout too many times when the template has
  better alternatives.
- The deck contains empty placeholders or leftover lorem ipsum/source text.
