# PPT Common Problems Playbook

This playbook distills external PowerPoint guidance into enforceable checks for
template-based deck generation. Use it when QA finds generic-looking,
unreadable, cluttered, inaccessible, or over-animated slides.

## Source-Informed Principles

Primary source themes:

- Microsoft accessibility guidance: every slide needs a unique title; reading
  order must match the intended reading path; non-text visuals need alt text or
  a decorative mark; use sans serif fonts, at least 18pt text, sufficient white
  space, and sufficient contrast.
- University teaching guidance: slides should support the presenter, not
  transcribe the lecture; dense content should become more slides, notes, or
  handouts; special effects and irrelevant graphics distract learners.
- Public health/science slide guidance: use sentence headlines, 2-4 bullet
  items when bullets are needed, visual evidence for the headline, generous
  blank space, high contrast, and line spacing around 1.5.
- Classroom display guidance: projected slides need larger type than ordinary
  report decks; complex diagrams often need progressive zoom or multiple
  slides.
- Data visualization guidance: do not rely on color alone; directly label
  important chart parts; avoid chartjunk, 3D effects, and labels that fight the
  message.

Useful source URLs:

- Microsoft PowerPoint accessibility:
  `https://support.microsoft.com/en-US/accessibility/powerpoint/make-your-powerpoint-presentations-accessible-to-people-with-disabilities`
- Microsoft Reading Order pane:
  `https://support.microsoft.com/en-us/office/make-slides-easier-to-read-by-using-the-reading-order-pane-863b5c1c-4f19-45ec-96e6-93a6457f5e1c`
- Microsoft effective presentations:
  `https://support.microsoft.com/en-us/office/tips-for-creating-and-delivering-an-effective-presentation-f43156b0-20d2-4c51-8345-0c337cefb88b`
- University of South Carolina teaching center:
  `https://sc.edu/about/offices_and_divisions/cte/teaching_resources/course_design_development_delivery/technology/designing_delivering_powerpoint_presentations/index.php`
- Harvard T.H. Chan slide checklist:
  `https://hsph.harvard.edu/research/health-communication/resources/slide-checklist/`
- Northern Illinois University teaching with PowerPoint:
  `https://www.niu.edu/citl/resources/guides/instructional-guide/teaching-with-powerpoint.shtml`
- Ohio University visual presentation:
  `https://www.ohio.edu/medicine/about/offices/information-learning-tech/visual-presentation`
- Old Dominion University presentation best practices:
  `https://www.odu.edu/online-faculty/training/presentations`
- Harvard data visualization accessibility:
  `https://accessibility.huit.harvard.edu/data-viz-charts-graphs`
- Microsoft compress pictures:
  `https://support.microsoft.com/en-us/office/reduce-the-file-size-of-a-picture-in-microsoft-office-8db7211c-d958-457c-babd-194109eb9535`
- Microsoft reduce presentation file size:
  `https://support.microsoft.com/en-us/office/reduce-the-file-size-of-your-powerpoint-presentations-9548ffd4-d853-41e7-8e40-b606bca036b4`
- Microsoft embedded fonts:
  `https://support.microsoft.com/en-us/office/benefits-of-embedding-custom-fonts-6af1a9c0-016c-4b07-9f2e-cb2606379a3e`
- Microsoft placeholders and slide layouts:
  `https://support.microsoft.com/en-us/office/add-edit-or-remove-a-placeholder-on-a-slide-layout-a8d93d28-66cb-43fd-9f9d-e12d0a7a1f06`
- Microsoft Reading Order pane:
  `https://support.microsoft.com/en-us/office/make-slides-easier-to-read-by-using-the-reading-order-pane-863b5c1c-4f19-45ec-96e6-93a6457f5e1c`
- Penn State PowerPoint accessibility:
  `https://accessibility.psu.edu/microsoftoffice/powerpoint/`

## Common Problems And Fixes

### Text-Dense Slides

Symptoms:

- More than 5 classroom bullets or 6 report bullets.
- Bullets become full sentences or paragraphs.
- Title plus body copy duplicates the speaker notes.
- Text fits only by shrinking below the delivery-mode minimum.

Fix:

- Convert paragraphs into 2-4 points.
- Move details into speaker notes or appendix.
- Split one dense section into multiple slides.
- Replace repeated explanatory text with a diagram, process, table, or metric.

### Unreadable Type

Symptoms:

- Core body text below `28pt` in classroom mode or below `18pt` in report mode.
- Template uses tiny body text because the source was designed as a document.
- Important content appears in captions, footers, or source-note zones.

Fix:

- Preserve hierarchy but enlarge core content.
- Shorten copy before shrinking.
- Use a larger-capacity slide or split.
- Keep footers and captions for metadata only.

### Weak Or Missing Slide Claim

Symptoms:

- Slide title is only a topic, such as `Background` or `Market`.
- Slide has no title role or only a hidden/inaccessible title.
- Slide title is too long to read quickly.

Fix:

- Rewrite title as a sentence claim.
- Keep visible titles concise; use hidden title only for accessibility when the
  visual design genuinely needs no visible title.
- If a topic continues, use continuation labeling such as `(2 of 3)`.

### Poor Template Fidelity

Symptoms:

- New variant changes font, grid, colors, corner radius, icon style, or footer.
- Reused source page has unmatched empty cards.
- Consecutive slides repeat the same layout even when the template has better
  alternatives.

Fix:

- Derive new variants from the nearest source slide.
- Copy existing repeated groups rather than inventing new decoration.
- Record base slide and preserved rules in `decision_records.json`.
- Use rhythm scoring to avoid monotonous layout repetition.

### Misused Images

Symptoms:

- Stock-like or irrelevant image fills a required proof slot.
- Low-resolution image is enlarged.
- Subject is cropped out.
- Image contains important text that is not repeated in editable slide text.

Fix:

- Use images only when they support the slide claim.
- Preserve template crop language, but adjust focal point.
- Split complex diagrams across slides or use progressive detail.
- Add alt text or mark purely decorative images as decorative.

### Chart And Data Problems

Symptoms:

- Chart uses color alone to encode meaning.
- Legend forces the viewer to look back and forth.
- 3D effects or heavy decoration distort the data.
- Every point is labeled, making the chart less clear than a table.
- Data labels are too small for the delivery mode.

Fix:

- Use direct labels, patterns, shapes, or text cues in addition to color.
- Remove 3D chart styles.
- Use a table when the viewer must read many exact values.
- Label only the values needed to prove the slide claim.
- Add source notes and alt text/summary for charts.

### Animation Overuse

Symptoms:

- Logo, footer, page number, background, or decoration is animated.
- More than 5 elements animate on one slide.
- Effects include spin, bounce, random bars, fast fly-in, or complex paths.
- Animation order conflicts with reading or teaching order.

Fix:

- Use fade/appear/simple wipe.
- Reveal bullets by paragraph only for live teaching.
- Use at most one emphasis animation per slide.
- Downgrade risky animation to a simple fade or no animation.

### Accessibility Gaps

Symptoms:

- Slide reading order follows object creation order instead of visual order.
- Images/charts have no alt text or visual summary.
- Decorative objects remain in reading order.
- Color alone communicates status, ranking, or category.
- Contrast is low or cannot be verified because text sits over images.

Fix:

- Set reading order to match the intended path.
- Group complex diagrams into logical units where safe; note that grouping can
  affect animations, so verify animation after grouping.
- Add alt text to visuals; mark pure decoration as decorative.
- Add labels/patterns/text cues in addition to color.
- Place text on high-contrast solid or semi-opaque backgrounds when over images.

### Delivery Compatibility Problems

Symptoms:

- Font changes on another computer and text overflows.
- Deck is too large to email or upload.
- Linked video/image works only on the creator's machine.
- Large embedded media makes playback slow.

Fix:

- Run `scripts/qa_pptx_package.py` on the final PPTX.
- Use common fonts or verify custom fonts are installed/embedded and licensed.
- Compress/crop oversized images and media.
- Replace low-resolution hero images.
- Remove external links unless they are intentional and tested.
- Use `minimal` animation mode when playback environment is uncertain.

### Structural Accessibility Problems

Symptoms:

- Slide has no unique title.
- Pictures, screenshots, diagrams, or charts have no alt text.
- Decorative shapes are read by screen readers.
- Reading order follows object creation order rather than visual/speaking order.
- Meaningful slide content is placed directly on the master and cannot be read
  as normal slide content.

Fix:

- Run `scripts/qa_accessibility_structure.py` on the final PPTX.
- Add unique titles or hidden accessibility titles.
- Add alt text to meaningful visuals or mark decoration as decorative.
- Verify Reading Order pane manually for complex slides.
- Use placeholders/layouts for recurring content instead of static master text.
