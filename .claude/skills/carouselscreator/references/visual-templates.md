# Visual Templates — layout pin + chain-of-reference + safe zones

This file is read by `generate_carousels.py` (Phase 4–5) and `regenerate_carousels_1x1.py` (Phase 8). Each kie.ai prompt is built as:

```
[brand modifier from brand-dna.json]
[asset pack vocabulary from assets.json]
[layout pin block — verbatim, this file]
[safe zones block — verbatim, this file]
[chain-of-reference instruction — verbatim, this file]
[per-slide visual_direction from copy-script.json]
```

The three middle blocks are universal — they go on every slide of every carousel. Repeating them on every prompt is what makes the 7 slides of a tanda look like they came from the same designer.

---

## Layout pin block (universal, paste verbatim into every prompt)

```
LAYOUT PIN — apply to every slide of this carousel without exception:

  - Brand mark / wordmark anchored TOP-LEFT, inset 8% from each edge, sized at
    ~6% of canvas height. Render the wordmark exactly as it appears in the
    attached logo reference; never redraw or stylise it.

  - Slide-number indicator anchored BOTTOM-RIGHT, inset 6% from each edge, in
    the brand's mono typography (or closest equivalent), tracked uppercase,
    format "{N}/{TOTAL}" — e.g. "1/3", "2/3", "3/3" for a 3-slide carousel.
    Small (≤2.5% of canvas height), low-contrast against background.

  - Headline block: composed in the brand's display typography, size and
    placement adapt to the slide's role:
      * Cover (slide 1): centered or upper-third, generous breathing room
      * Mid slides: upper-third or lower-third, never centered with body
      * Final slide: composed to make the product the hero, headline supports
        rather than competes

  - Body / supporting copy: 1–2 lines max, always in the brand's body
    typography, set in a high-contrast color from the palette. Place where it
    doesn't compete with the photo subject.

  - The photographic subject (product OR scene) occupies a minimum of 60% of
    the canvas. Type sits ON TOP of the photo with sufficient contrast — do
    not letterbox the photo into a smaller area to make room for type.

  - Color palette is strictly the brand palette. No accent colors invented
    outside it. No pure white #fff unless the brand explicitly uses it.

  - No emoji decoration, no clip-art icons, no stock photography signifiers.
```

---

## Safe zones block (universal — protects from IG/TikTok UI overlay)

```
SAFE ZONES — RESERVED CANVAS AREAS:

  - Top 7% of canvas: leave as continuous photographic breathing room (sky,
    out-of-focus background, neutral wash). Do NOT place headlines, badges,
    logos, or copy in this band. The Instagram/TikTok status bar lives here.
    The brand mark anchored at "top-left inset 8%" sits BELOW this band.

  - Bottom 20% of canvas: reserve as continuous photographic breathing room
    (foreground, out-of-focus floor, neutral wash). Do NOT place headlines,
    bodies, badges, ribbons, or stat callouts in this band. The Instagram
    caption + UI overlay lives here. The slide-number indicator at
    "bottom-right inset 6%" sits ABOVE this band, just inside it.

  - The two reserved bands MUST be visually continuous extensions of the
    photo — no horizontal stripe, no banner, no color block, no shadow
    gradient that hints at "I am a reserved area". The viewer should perceive
    them as part of the scene.
```

---

## Chain-of-reference instruction (slides 2..N only)

```
CHAIN OF REFERENCE — visual continuity:

  The third image attached to this prompt is slide 1 of this same carousel.
  Treat it as the visual anchor for this entire carousel set. This slide
  (slide N, where N >= 2) must inherit from the anchor:

    - Identical color palette (no new hues)
    - Identical lighting direction, intensity, and color temperature
    - Identical photographic style (lens, depth of field, grain, contrast)
    - Identical typographic treatment (display font, weight, kerning)
    - Identical brand mark placement and slide-number indicator style

  What CHANGES between slide 1 and this slide is only:
    - The composition / framing of the photographic subject
    - The headline + body copy
    - Whether the product is featured prominently or partially hidden

  Do NOT shift mood (e.g. dusk → daylight, warm → cool, indoor → outdoor)
  unless the per-slide visual_direction explicitly calls for it.
```

The cover slide (slide 1) gets only LAYOUT PIN + SAFE ZONES — no chain-of-reference, because there's no anchor yet.

---

## Per-framework visual hooks (informational, not a prompt block)

These are guidelines for *how* to write each slide's `visual_direction` in `copy-script.json`. They're for the human/Claude editing the script, not for kie.ai directly.

### PAS arc

| Slide | Mood | Subject | Product visibility |
|---|---|---|---|
| 1 — Problem | tense, unresolved | scene OF the problem (failure, frustration) | absent or out-of-focus |
| 2 — Agitate | heavier, stakes raised | consequence / cost / aftermath | still absent or barely glimpsed |
| 3 — Solution | clear, hopeful, resolved | product as hero | center, sharp, full reveal |

The arc should *visually* land like a story: tension → tension → release. Lighting can stay constant (chain of reference does its job) but framing tightens around the product on slide 3.

### AIDA arc

| Slide | Mood | Subject | Product visibility |
|---|---|---|---|
| 1 — Attention | bold, surprising | dramatic detail / unexpected angle | partial, intriguing |
| 2 — Interest | informative, intimate | process / craft / origin | partial, in-context |
| 3 — Desire | aspirational, sensory | lifestyle scene with product | featured but not isolated |
| 4 — Action | calm, clear | clean product hero | center, full reveal |

The arc *zooms out then back in*: macro detail → process → lifestyle → clean product. Lighting stays constant, framing rhythm gives the carousel its pace.

---

## Layout-pin verification checklist (for the curation gallery review)

When reviewing `curation.html` (Phase 6) before saying "subilas", scan each slide for:

- [ ] Brand mark visible top-left, NOT redrawn or distorted
- [ ] Slide indicator visible bottom-right with correct N/TOTAL
- [ ] Top 7% is photo continuation, NO type / badge / banner
- [ ] Bottom 20% is photo continuation, NO type / badge / banner
- [ ] Photo subject occupies ≥60% of canvas
- [ ] Headline + body in brand fonts, brand colors
- [ ] No invented colors / fonts / icons / emoji
- [ ] Slide N visually inherits palette + lighting + mood from slide 1 of its carousel

Any slide failing 2+ of these → regenerate it (`python generate_carousels.py --regenerate {carousel}.{slide}`).
Any slide failing the chain-of-reference (slide N looks unrelated to slide 1) → regenerate that whole carousel from cover up (`--regenerate {carousel}.*`).
