# Delivery Compatibility

Use this reference before final delivery, especially when the deck will be
emailed, uploaded to a learning platform, opened on another computer, or played
from a classroom podium.

## Common Delivery Problems

### Missing Or Replaced Fonts

Symptoms:

- Text reflows on another machine.
- Line breaks change and overflow appears after export.
- Font fallback changes the template's visual identity.

Fix:

- Prefer common system fonts or the template's existing theme fonts.
- If using a custom font, verify the presenter machine has it or embed it when
  licensing allows.
- Re-render the deck after font substitution or embedding because layout can
  change.
- Avoid relying on a custom font for dense body copy.

### File Too Large To Share

Symptoms:

- Email/upload fails.
- Deck opens slowly.
- Classroom machine stutters when playing videos.

Fix:

- Compress or crop high-resolution images to the display size actually needed.
- Use JPEG for photo-heavy imagery unless transparency is required.
- Keep PNG for flat graphics, screenshots, logos, or transparency.
- Compress videos and verify playback on the target machine.
- Remove unused media and hidden scratch slides before delivery.

### Linked Assets Break Offline

Symptoms:

- Video, image, chart, or font works on the authoring machine but fails during
  presentation.
- PPTX contains external relationships.

Fix:

- Embed essential media when the deck must run offline.
- If links are intentional, record them in the delivery notes and test on the
  presentation machine or network.

### Image Quality Mismatch

Symptoms:

- Image looks blurry when projected.
- File is huge because original images are far larger than displayed.
- Screenshot text is unreadable.

Fix:

- Replace low-pixel source images when they are used as hero or content images.
- Downsample oversized raster images after cropping.
- Recreate text-heavy screenshots as editable text or diagrams where possible.

### Playback Compatibility

Symptoms:

- Animation behaves differently across PowerPoint versions.
- Slide transitions lag.
- Embedded media codecs fail.

Fix:

- Use simple fades, appears, and wipes.
- Avoid complex motion paths for template-generated decks.
- Use `minimal` animation mode for uncertain playback environments.
- Test on the actual machine when videos, custom fonts, or animations matter.

## Package QA

Run:

```bash
python "$SKILL_DIR/scripts/qa_pptx_package.py" \
  "$FINAL_PPTX" \
  --out "$WORKSPACE/qa_package_report.json" \
  --pretty
```

Treat major findings as blockers unless the user explicitly accepts the risk.

The script checks:

- overall PPTX size
- total embedded media size
- oversized images
- low-pixel images that may blur if used large
- large video/audio assets
- embedded font parts
- non-common fonts without detected embedding
- external relationships that may fail offline
