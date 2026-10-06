---
name: carouselscreator
description: |-
  Generate Instagram carousels (10 copy frameworks — PAS, AIDA, Listicle, Before/After, Us vs Them, HSO, Myth/Truth, How-to, Quote/Insight, Propuesta Comercial — 9:16 + 1:1) for any brand end-to-end — copy script generation, visual chain-of-reference rendering via openai/gpt-image-2 (kie.ai), client preview link, pick-driven 1:1 reformatting, deliverables ZIP, and Drive auto-upload. Use this skill whenever the user mentions generating carousels, Instagram carousels, carrouseles, multi-slide ads, slide decks for social media, or asks to "generemos carruseles", "armemos un set de carruseles", "carrusel para Instagram", "hacé un carrusel para [marca]", "carouseles PAS/AIDA", "set de carruseles", "carrusel para feed", "carousel ad", "propuesta comercial", "por qué elegirnos" — even if they don't explicitly mention this skill.
---
# Carousels Creator

End-to-end pipeline that turns a brand + product + tone into a set of Instagram carousels (PAS + AIDA frameworks) via openai/gpt-image-2 (kie.ai endpoint), with chain-of-reference visual consistency between slides.

## When to invoke

Trigger when the user asks to "generemos carruseles", "armemos un set de carruseles", "carrusel para Instagram", "carrusel para [marca]", "carrousel para feed", "carouseles PAS/AIDA", "carousel ad", "multi-slide ad" — for any brand or product. Don't wait for an explicit skill name.

If the user asks for static ads / placas / single-image creatives, use `staticadscreator` instead.

## v1.2 scope (locked)

| Decision | Value |
|---|---|
| Frameworks supported | **10** — PAS (3) · AIDA (4) · Listicle (5) · Before/After (3) · Us vs Them (4) · HSO (3) · Myth/Truth (4) · How-to (5) · Quote/Insight (3) · Propuesta Comercial (5) |
| Carousels per tanda | **10** by default — exactly 1 per available framework |
| Subset opt-in | User can say "solo PAS y Propuesta Comercial" (etc) in trigger prompt → Claude generates only those |
| Workflow | **Copy-first** — script JSON before any image |
| Pick granularity | Per **carousel** (whole), not per slide |
| Formats | **9:16 first, 1:1 after pick** (DROP-DON'T-CRAM) |
| Slide counts | Framework defaults (3-5); no per-carousel overrides for v1.2 |
| Cost target kie.ai | ~$5.85 preview (39 slides 9:16) + ~$0.55 per picked carousel (1:1 reformat) → **~$8-12 per tanda** |

Default = 10 carousels = 39 slides 9:16 + reformatted 1:1 of whatever the client picks. If the client picks 3 carousels (typical), the 1:1 phase generates ~12 more slides. Total ≈ 51 slides per tanda, ~$8.

Multi-word framework names (Propuesta Comercial, Before/After, Us vs Them) slugify to filename-safe form via `slug_framework()` in the Python pipeline (`"Propuesta Comercial"` → `propuesta-comercial`).

Adding more frameworks later (Recipe, Comparison Matrix, Customer Journey, Day-in-the-Life, etc) is purely a `copy-frameworks.md` append — no code changes.

## Prerequisites

- **`KIE_API_KEY`** env var — bearer token from https://kie.ai/api-key (gpt-image-2-image-to-image)
- **`PICKS_UPLOAD_TOKEN`** env var — bearer token for `ia.generarimpacto.com /api/upload/*` endpoints
- Python 3.10+ with `pip install requests pillow`
- A brand that already has `brand-dna.json` + `product-images/` populated (run `staticadscreator` Phase 1 first if not)
- A specific product name from the user

## Inputs to ask the user

1. **Brand name + slug** (e.g., "Cuchillos de Campo · cuchillosdecampo")
2. **Product name** (e.g., "Criollo en Roseta de Ciervo")
3. **Tone for this tanda** (e.g., "warm-rioplatense", "informative-premium", "playful-educational") — defaults to brand voice if unspecified
4. **Frameworks subset (optional)** — if the user says e.g. "solo PAS y Listicle" or "todos menos Quote", restrict to that subset. If they don't mention frameworks, default to all 9 available.

Slide counts come from each framework's defaults (PAS=3, AIDA=4, Listicle=5, Before/After=3, Us vs Them=4, HSO=3, Myth/Truth=4, How-to=5, Quote/Insight=3, Propuesta Comercial=5).

## Workflow — 10 linear steps, 3 hard checkpoints

Each phase produces files under `brands/{brand-slug}/carousels/{campaign-slug}/`. Pre-existing files at `brands/{brand-slug}/` (brand-dna.json, product-images/, assets/) are reused.

### Phase 1 — Brand DNA + producto (reuse)

**1. Verify scaffolding exists** — Check that `brands/{brand}/brand-dna.json` and `brands/{brand}/product-images/` exist with at least one product image + brand-logo.png. If not, stop and tell the user to run `staticadscreator` Phase 1 first. **Never re-research a brand that's already been bootstrapped.**

**2. Locate the product image** — Find the file under `product-images/` whose filename slug matches (or is closest to) the product name the user gave. This is the single product ref every slide will use.

### Phase 2 — Selector

**3. Confirm tanda parameters** — Ask the user (or infer from message):
- Product name → resolves to a specific filename in `product-images/`
- Tone (default: brand voice from `brand-dna.json`)
- Campaign slug (kebab-case, e.g. `criollo-roseta-2026`)

No checkpoint here — proceed straight to copy generation.

### Phase 3 — Copy script generation

**4. Generate `copy-script.json`** — Read `references/copy-frameworks.md` to get the PAS + AIDA structure. For each framework, fill the placeholders with brand-specific copy derived from `brand-dna.json` (voice register, vocabulary, positioning) + the product (description, materials, value props from `product-images/` source pages if available).

Write the JSON to `brands/{brand}/carousels/{campaign}/copy-script.json` with this exact shape:

```json
{
  "brand": "Cuchillos de Campo",
  "brand_slug": "cuchillosdecampo",
  "campaign": "Criollo en Roseta de Ciervo",
  "campaign_slug": "criollo-roseta-2026",
  "product_focus": "Criollo en Roseta de Ciervo",
  "product_image": "criollo-roseta-1.webp",
  "tone": "warm-rioplatense-craftsman",
  "generated_at": "2026-04-26T14:30:00Z",
  "carousels": [
    {
      "carousel": 1,
      "framework": "PAS",
      "slide_count": 3,
      "slides": [
        {
          "slide": 1,
          "role": "Problem",
          "label": "El problema",
          "headline": "...",
          "body": "...",
          "visual_direction": "..."
        },
        {
          "slide": 2,
          "role": "Agitate",
          ...
        },
        {
          "slide": 3,
          "role": "Solution",
          ...
        }
      ]
    },
    {
      "carousel": 2,
      "framework": "AIDA",
      "slide_count": 4,
      "slides": [...]
    },
    {
      "carousel": 10,
      "framework": "Propuesta Comercial",
      "slide_count": 5,
      "_compliance_override": {
        "scoped_to": "carousel-10-propuesta-comercial",
        "source_url": "https://cuchillosdecampo.com.ar/criollo-roseta",
        "fetched_at": "2026-04-27T14:30:00Z",
        "verbatim_excerpts": ["30% OFF", "25% por transferencia", "12 cuotas sin interés"],
        "rationale": "_compliance_notes en brand-dna indica que el sitio publica heavy promo. Override scoped solo al carrusel #10."
      },
      "slides": [...]
    }
  ]
}
```

**Schema notes:**
- `_compliance_override` is **only** valid on carousel #10 (Propuesta Comercial) when the brand has strict compliance flags but the site publishes commercial terms. See `references/copy-frameworks.md` § "Propuesta Comercial — Phase 0 (compliance scoped override)" for the full rule.
- If `_compliance_override` is absent on carousel #10, it means the brand's strict flags apply unchanged → write the slides non-monetarily (direccional sin números).

**✋ CHECKPOINT 1 — copy edit** — Tell the user the JSON is ready and ask them to review. They'll edit headlines, body, visual_direction inline and tell you to proceed. **Do NOT advance to Phase 4 without explicit "dale" / "seguí" / "OK copy".**

### Phase 4 — Slide 1 covers (kie.ai)

**5. Copy `generate_carousels.py` to brand folder** — `cp .claude/skills/carouselscreator/references/generate_carousels.py brands/{brand}/carousels/{campaign}/`

**6. Run cover phase** — Generates only slide 1 of each carousel (the covers). Strong brand modifier, no anchor refs yet (those don't exist yet). Outputs to `brands/{brand}/carousels/{campaign}/{carousel:02d}-{framework}-9x16-01.png`.

```bash
cd brands/{brand}/carousels/{campaign}
KIE_API_KEY=… PICKS_UPLOAD_TOKEN=… python generate_carousels.py --phase covers
```

The script:
- Hosts product + logo + (later) anchor on Vercel Blob via `_kie_refs/`
- For each carousel: builds prompt from copy-script.json + brand modifier + asset pack vocabulary + safe zones rule + visual-templates.md layout pin
- Slide 1 input_urls = `[product_url, logo_url]` (PRODUCT FIRST, logo second)
- Saves 2 covers (one per framework)
- Auto-opens `carousels/{campaign}/preview-covers.html` so the user can validate the visual anchor before generating slides 2..N

### Phase 5 — Slides 2..N (chain of reference)

**7. Run slides phase** — Generates slides 2..N for each carousel using slide 1 as a third visual anchor.

```bash
python generate_carousels.py --phase slides
```

The script:
- Reuploads each `01-{framework}-9x16-01.png` to Vercel Blob → gets `slide1_anchor_url` per carousel
- For slide N (N≥2) of carousel C: `input_urls = [product_url, logo_url, slide1_anchor_C_url]`
- Each prompt includes the layout pin verbatim (from `visual-templates.md`) so composition stays consistent
- Concurrency 4 (kie.ai handles parallel cleanly)
- Saves to `{carousel:02d}-{framework}-9x16-{slide:02d}.png`

### Phase 6 — Local curation gallery

**8. Build curation gallery** — Auto-runs at end of Phase 5. Generates `carousels/{campaign}/curation.html` with each carousel as an expandable card showing its slides side-by-side at 9:16 thumbnail size. Branded with Genera Impacto identity (Carbón Tech bg, Azul Impacto accents, Montserrat 900 / Poppins 300 / JetBrains Mono labels). Auto-opens in browser.

**✋ CHECKPOINT 2 — preview review** — User reviews `curation.html`. Possible curation actions:

- **Regenerate one slide** — `python generate_carousels.py --regenerate {carousel}.{slide}` (e.g. `1.2` = carousel 1 slide 2). Overwrites the PNG, gallery rebuilds.
- **Regenerate full carousel** — `python generate_carousels.py --regenerate {carousel}.*` (re-does the whole carousel, including the cover, breaking chain to test a different visual anchor)
- **Edit copy + regenerate** — User edits `copy-script.json`, then re-runs the affected slide(s)

**Wait for explicit "dale, subilas" / "subí al cliente" / "está bueno, mostralo".** Until then, files live ONLY locally.

### Phase 7 — Upload 9:16 to estrategia-ia (client preview)

**9. Run upload (9:16 only)** — `python upload_carousels.py --brand-slug … --brand-name … --campaign-slug … --campaign-title … --client-message …`

The script:
- Walks `carousels/{campaign}/*.png` (9:16 only — no 1:1 exists yet)
- Uploads each to Vercel Blob under `carousels/{brand}/{campaign}/`
- Posts the manifest to `/api/upload/carousel-set`
- Auto-opens `https://ia.generarimpacto.com/c/{brand}/{campaign}` in browser
- Pass the public URL back to the user

The client receives that link, navigates a horizontal slider per carousel (each card expandable to show slides), picks **K out of 2 carousels** (whole carousels — not individual slides), and submits.

### Phase 8 — Reformat picks to 1:1

**MANDATORY first step — fetch picks from the API. NEVER ask the user "qué carruseles eligió" without trying this first.**

```bash
curl -s -H "Authorization: Bearer $PICKS_UPLOAD_TOKEN" \
  https://ia.generarimpacto.com/api/carousel-picks/{brand}/{campaign}
```

Response shape (always JSON):
```json
{
  "ok": true,
  "count": 1,
  "latest": {
    "id": "...",
    "submitted_at": "2026-04-27T15:30:00Z",
    "selected_carousels": [1, 7, 10],
    "selected_carousel_frameworks": ["PAS", "Myth/Truth", "Propuesta Comercial"],
    "client_note": "Me gustaron mucho los 3"
  },
  "picks": [...],
  "set": { ... }
}
```

How to interpret:
- `count > 0` → use `latest.selected_carousels` directly. Tell the user *"El cliente eligió los carruseles {N, M, ...} ({frameworks}). Regenero esos a 1:1?"* and wait for confirmation.
- `count === 0` → cliente todavía no envió. Decile al usuario *"El cliente todavía no respondió en /c/{brand}/{campaign}"* y esperá.
- HTTP 401 → falta o está mal el `PICKS_UPLOAD_TOKEN` env var. Avisar al usuario.
- HTTP 404 → no existe la tanda con ese slug. Avisar.

**Solo después de fetchear** y confirmar con el usuario, ejecutar:

**10. Run regenerate-1x1** — `python regenerate_carousels_1x1.py --carousels 1[,2,…]`

The script:
- For each picked carousel × each slide: regenerates at 1:1 with DROP-DON'T-CRAM directive
- input_urls = `[product_url, logo_url, the_9x16_slide_url]` (the 9:16 slide is the visual anchor for its 1:1 sibling)
- Output to `carousels/{campaign}/picks-1x1/{carousel:02d}-{framework}-1x1-{slide:02d}.png`
- Auto-opens `carousels/{campaign}/picks-consistency.html` — side-by-side gallery (9:16 anchor with Azul Impacto badge | 1:1 new) per slide of each picked carousel

### Phase 9 — Final curation + deliverables

**✋ CHECKPOINT 3 — picks consistency review** — User reviews `picks-consistency.html`. Common actions:

- Regenerate a 1:1 if it dropped a critical element (`python regenerate_carousels_1x1.py --slide 1.2`)
- Mark a slide done if it looks good

**Wait for "subí la entrega" / "armá el link de deliverable" / "publicá las finales".**

**11. Run upload_deliverables** — `python upload_carousels.py --phase deliverables` (Drive auto-upload corre por default; pasá `--no-drive` solo para tests locales)

The script:
- Walks the picked carousels × both formats (9:16 + 1:1) under `carousels/{campaign}/` + `picks-1x1/`
- Compresses any PNG over 4.3 MB to JPG q=92 (Vercel multipart cap)
- Uploads to `carousel-deliverables/{brand}/{campaign}/` on Blob
- Posts the manifest to `/api/upload/carousel-deliverable`
- Public deliverable URL: `https://ia.generarimpacto.com/c/d/{brand}/{campaign}` (download per-asset + bulk ZIP)

### Phase 10 — Drive auto-upload

El upload a Google Drive corre **automáticamente en step 11** (a menos que se haya pasado `--no-drive`). Navega:

```
ADS|{CLIENTE} → ESTRATEGIAS DE CONTENIDO → {NN} - {MES} → ESTRATEGIA IA → CARRUSELES /
```

**Estructura interna**: cada carrusel queda en su propia subcarpeta con ambos formatos adentro:

```
CARRUSELES /
├── 01 - PAS - Criollo en Roseta de Ciervo /
│   ├── 9x16_slide_01.png
│   ├── 9x16_slide_02.png
│   ├── 9x16_slide_03.png
│   ├── 1x1_slide_01.png
│   ├── 1x1_slide_02.png
│   └── 1x1_slide_03.png
├── 02 - AIDA - Criollo en Roseta de Ciervo /
│   ├── 9x16_slide_01.png
│   ├── ... (4 slides x 2 formatos = 8 archivos)
└── 10 - Propuesta Comercial - Criollo en Roseta de Ciervo /
    └── ...
```

- **Subcarpeta**: `{NN:02d} - {framework} - {product_focus}` (número para sort, framework para identificar, producto para diferenciar tandas distintas con mismo framework).
- **Archivos**: `{formato}_slide_{NN}.{ext}` — limpio porque el contexto ya está en la carpeta padre.

If `_drive_folder_id` isn't in `brand-dna.json`, the script warns and skips Drive (no-op, doesn't fail).

### Phase 10.5 — Closing message (MANDATORY format)

Once `upload_carousels.py --phase deliverables` finishes, the assistant **MUST** close the flow with this exact two-link format. Both URLs come from the script's stdout (`Public client link:` for the client URL, `CARRUSELES folder:` for the Drive URL).

```
✅ Listo. Te dejo los dos links:

📬 PARA EL CLIENTE
   https://ia.generarimpacto.com/c/d/{brand-slug}/{campaign-slug}
   Mandalo por WhatsApp o email — descarga individual o .ZIP.

🗂️ PARA EL EQUIPO (Drive)
   https://drive.google.com/drive/folders/{CARRUSELES-folder-id}
   {N} subcarpetas ({frameworks, comma-separated}), cada una con 9:16 + 1:1.
```

Hard rules:
- **Two links, never one** — even if Drive was skipped (`--no-drive`), call it out explicitly: "Drive: skipped (--no-drive)".
- **Plain text, no extra commentary** — the format is the deliverable. Don't summarize stats unless the user asks.
- **`/c/d/` prefix is intentional** for carousels (videos use `/v/d/`, static ads use `/d/`).
- If any URL is missing from the script's stdout, **do not fabricate it** — say "no me llegó el link X, revisá la salida del script".

## Principles (non-negotiable)

- 🎯 **Exactly 1 carousel per available framework** — v1 means 2 carousels (PAS + AIDA). Adding Listicle later means 3.
- 🪪 **Reuse staticadscreator scaffolding** — never re-research a brand. brand-dna.json + product-images/ + assets/ are inputs, not outputs.
- 🔗 **Chain of reference is law** — slide 1 sets the visual anchor; slides 2..N use slide 1 as a third ref. Do not skip the cover-first phase.
- 📐 **Layout pinned across slides** — every prompt includes the same composition rule block from `references/visual-templates.md`. Brand mark top-left at 8%, slide indicator bottom-right, body block centered.
- 🔢 **Resolution `2K` default** — same memory as static. Step down to 1K only for cheap/test runs.
- ⚡ **Concurrency 4 default** — kie.ai handles 4–8 parallel jobs cleanly via ThreadPoolExecutor.
- 📂 **Flat output** — PNGs at `carousels/{campaign}/` root as `{NN}-{framework}-{format}-{slide:02d}.png`. 1:1 picks live under `picks-1x1/` subfolder. No further nesting.
- 🌐 **Auto-open galleries** — preview-covers.html (Phase 4), curation.html (Phase 6), picks-consistency.html (Phase 8). All branded with Genera Impacto.
- ⚖️ **Compliance is law** — the `compliance` block of `brand-dna.json` filters every slide's copy + visuals before generation.
- ✋ **3 hard checkpoints** — copy edit (Phase 3) | preview review (Phase 6) | picks consistency (Phase 9). Never skip any without explicit user OK.
- 🌐 **kie.ai needs public URLs for refs** — same `/api/upload/image` (campaign slug `_kie_refs`) pattern as static.
- 🔄 **Auto-retry failures** — same retry envelope as `generate_ads.py`. User sees only the final clean state.
- 📐 **9:16 first, 1:1 after pick** — never burn budget reformatting carousels the client won't pick.
- 🇦🇷 **Voice matches brand market** — rioplatense vos for AR brands; respect the `tone_of_voice` block of `brand-dna.json`.

## References

| File | Purpose |
|------|---------|
| `references/copy-frameworks.md` | PAS (3 slides) + AIDA (4 slides) structure with bracketed placeholders. Phase 3 source of truth. Add Listicle/extra frameworks here later. |
| `references/visual-templates.md` | Layout-pin block (composition rules every slide must include) + chain-of-reference rule + safe zones + per-framework visual hooks. |
| `references/generate_carousels.py` | Phase 4–5 image generation. kie.ai gpt-image-2-image-to-image, ThreadPoolExecutor concurrency=4, two phases (`--phase covers` then `--phase slides`), per-slide ref resolution (product + logo + slide1 anchor for slides 2+), Vercel Blob auto-hosting of refs, auto-open curation gallery. |
| `references/regenerate_carousels_1x1.py` | Phase 8 picks → 1:1 reformat. Same kie.ai stack + DROP-DON'T-CRAM directive + 9:16 sibling as visual anchor + auto-opens picks-consistency.html. |
| `references/upload_carousels.py` | Phases 7 + 9. Two modes (`--phase preview` for 9:16-only client link, `--phase deliverables` for picked-and-curated final delivery + ZIP). Auto-discovers picked carousels from picks payload. **Drive auto-upload corre por default** en deliverables phase (a `ESTRATEGIA IA / CARRUSELES /`, una subcarpeta por carrusel `{NN:02d} - {framework} - {product_focus}/` con archivos internos `{format}_slide_{NN}.{ext}`); `--no-drive` opt-out solo para tests. |

## Folder structure (per campaign)

```
brands/{brand-slug}/
├── product-images/                       ← from staticadscreator (reused)
├── brand-dna.json                        ← from staticadscreator (reused)
├── assets/                               ← from staticadscreator (reused, optional)
├── assets.json                           ← from staticadscreator (reused, optional)
└── carousels/
    └── {campaign-slug}/
        ├── copy-script.json              ← Phase 3 (✋ checkpoint 1)
        ├── generate_carousels.py         ← Phase 4–5 (copied from skill)
        ├── regenerate_carousels_1x1.py   ← Phase 8 (copied from skill)
        ├── upload_carousels.py           ← Phases 7 + 9 (copied from skill)
        ├── 01-pas-9x16-01.png            ← Phase 4 (cover)
        ├── 01-pas-9x16-02.png            ← Phase 5
        ├── 01-pas-9x16-03.png            ← Phase 5
        ├── 02-aida-9x16-01.png           ← Phase 4 (cover)
        ├── 02-aida-9x16-02.png           ← Phase 5
        ├── 02-aida-9x16-03.png           ← Phase 5
        ├── 02-aida-9x16-04.png           ← Phase 5
        ├── preview-covers.html           ← Phase 4 (auto-open)
        ├── curation.html                 ← Phase 6 (auto-open, ✋ checkpoint 2)
        ├── manifest.json                 ← Phase 7 (uploaded copy)
        ├── picks-1x1/
        │   ├── 01-pas-1x1-01.png         ← Phase 8 (only if PAS was picked)
        │   └── ...
        └── picks-consistency.html        ← Phase 8 (auto-open, ✋ checkpoint 3)
```

## kie.ai API specifics

Same endpoints, auth, polling, state machine, and refs-must-be-public-URLs constraint as `staticadscreator/SKILL.md` § "kie.ai API specifics". Do not duplicate; consult that section.

Key differences for this skill:
- Default aspect for Phase 4–5 = `9:16`; for Phase 8 = `1:1` (DROP-DON'T-CRAM)
- 1 task = 1 slide; per-carousel run = 3 (PAS) or 4 (AIDA) sequential createTask calls within a worker
- Phase 5 input_urls always 3 refs (product + logo + slide1-anchor); Phase 4 always 2 refs (product + logo)

## Cost notes (v1.2 — 10 frameworks)

Slide counts per framework: PAS 3 · AIDA 4 · Listicle 5 · Before/After 3 · Us vs Them 4 · HSO 3 · Myth/Truth 4 · How-to 5 · Quote/Insight 3 · Propuesta Comercial 5 = **39 slides total** for a full tanda.

- **9:16 preview** (full tanda, 39 slides at 2K): ~**$5.85**
- **1:1 reformat** (per picked carousel, 3-5 slides each): ~**$0.45-0.75 per pick**
- **Typical tanda** (client picks 3 of 10 carousels): ~**$5.85 + ~$2 = ~$8**
- **Worst case** (client picks all 10): ~**$5.85 + ~$5.85 = ~$11.70**
- **Subset opt-in** (e.g. "solo PAS y Propuesta Comercial" → 8 slides): ~**$1.20** preview + ~$1.50 picks = ~**$2.70**

Time on kie.ai with concurrency=4:
- Phase 4 (covers): 10 covers ≈ **3 minutes**
- Phase 5 (slides 2..N): 29 slides ≈ **4 minutes**
- Total preview: ~**6-7 minutes**
- 1:1 reformat post-pick: ~**2-3 minutes** depending on picks
