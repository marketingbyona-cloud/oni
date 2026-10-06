#!/usr/bin/env python3
"""
Carousel Generator — Phases 4–5: kie.ai gpt-image-2 image-to-image with
chain-of-reference visual continuity.

Pipeline:
  Phase 4 (covers):
    For each carousel in copy-script.json, generate slide 1 (the cover).
    input_urls = [product_url, logo_url]   (no anchor exists yet)
    Saves to {NN:02d}-{framework}-9x16-01.png and rebuilds preview-covers.html.

  Phase 5 (slides):
    For each carousel, upload the just-generated cover to Vercel Blob → anchor.
    For each subsequent slide N>=2:
      input_urls = [product_url, logo_url, anchor_url]
    Saves to {NN:02d}-{framework}-9x16-{slide:02d}.png and rebuilds curation.html.

Both phases parallel via ThreadPoolExecutor. Default concurrency=4.

Mirrors generate_ads.py exactly for kie.ai auth, polling, ref hosting, retries,
and the auto-open gallery pattern. The universal prompt blocks (layout-pin,
safe-zones, chain-of-reference) are embedded as constants here so the script is
self-contained when copied into the campaign folder.

Usage (run from inside brands/{brand}/carousels/{campaign}/):
    python generate_carousels.py --phase covers
    python generate_carousels.py --phase slides
    python generate_carousels.py --phase all
    python generate_carousels.py --regenerate 1.2     # carousel 1 slide 2 only
    python generate_carousels.py --regenerate 1       # whole carousel 1
    python generate_carousels.py --dry-run

Required env vars:
    KIE_API_KEY            kie.ai bearer token (https://kie.ai/api-key)
    PICKS_UPLOAD_TOKEN     Bearer token for ia.generarimpacto.com /api/upload/image
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import platform
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' package required. pip install requests")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# ─── Auto-load credentials desde .env.local ──────────────────────────────────
# KIE_API_KEY + PICKS_UPLOAD_TOKEN no vienen de `vercel env pull` (ese baja
# solo env vars del backend deployado). Viven en estrategia-ia/.env.local
# agregadas a mano. Este loader los lee de ahi - asi ningun operador tiene
# que setear env vars de Windows ni que nadie le pregunte el token.
def _load_env_credential(_name: str) -> str:
    import os as _os
    from pathlib import Path as _P
    _v = _os.environ.get(_name, "").strip()
    if _v:
        return _v
    _cands = [
        _P.cwd() / ".env.local",
        _P.cwd().parent / ".env.local",
        _P.cwd().parent.parent / ".env.local",
        _P.home() / "estrategia-ia" / ".env.local",
        _P.cwd().parent / "estrategia-ia" / ".env.local",
        _P.home() / ".genera-impacto" / ".env.local",
    ]
    for _p in _cands:
        try:
            if not _p.exists():
                continue
            for _line in _p.read_text(encoding="utf-8").splitlines():
                if _line.startswith(_name + "="):
                    _val = _line.split("=", 1)[1].strip()
                    if len(_val) >= 2 and _val[0] in "\"'" and _val[-1] == _val[0]:
                        _val = _val[1:-1]
                    if _val:
                        return _val
        except OSError:
            continue
    return ""
# ─────────────────────────────────────────────────────────────────────────────


KIE_API_KEY = _load_env_credential("KIE_API_KEY")
KIE_BASE = "https://api.kie.ai"
KIE_CREATE = f"{KIE_BASE}/api/v1/jobs/createTask"
KIE_INFO = f"{KIE_BASE}/api/v1/jobs/recordInfo"
KIE_MODEL = "gpt-image-2-image-to-image"

PICKS_API_BASE = os.environ.get("PICKS_API_BASE", "https://ia.generarimpacto.com").rstrip("/")
PICKS_UPLOAD_TOKEN = _load_env_credential("PICKS_UPLOAD_TOKEN")

POLL_INTERVAL = 3
MAX_POLL_TIME = 300
DEFAULT_RESOLUTION = "2K"
DEFAULT_ASPECT = "9:16"
DEFAULT_CONCURRENCY = 10

_print_lock = threading.Lock()
def _safe_print(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)


# ---------------------------------------------------------------------------
# Universal prompt blocks (verbatim from references/visual-templates.md)
#
# Embedded here so the copied script is self-contained. If visual-templates.md
# is updated in the skill, these blocks should be kept in sync — but each copy
# of the script in a campaign folder locks in the version it was copied with,
# which is intentional (campaign reproducibility).
# ---------------------------------------------------------------------------

LAYOUT_PIN_BLOCK = """LAYOUT PIN — apply to every slide of this carousel without exception:

  - Brand mark / wordmark anchored TOP-LEFT, inset 8% from each edge, sized at
    ~6% of canvas height. Render the wordmark exactly as it appears in the
    attached logo reference; never redraw or stylise it.

  - Slide-number indicator anchored BOTTOM-RIGHT, inset 6% from each edge, in
    the brand's mono typography (or closest equivalent), tracked uppercase,
    format "{N}/{TOTAL}". Small (<= 2.5% of canvas height), low-contrast
    against background.

  - Headline block: composed in the brand's display typography, size and
    placement adapt to the slide's role:
      * Cover (slide 1): centered or upper-third, generous breathing room
      * Mid slides: upper-third or lower-third, never centered with body
      * Final slide: composed to make the product the hero, headline supports
        rather than competes

  - Body / supporting copy: 1-2 lines max, always in the brand's body
    typography, set in a high-contrast color from the palette. Place where it
    doesn't compete with the photo subject.

  - The photographic subject (product OR scene) occupies a minimum of 60% of
    the canvas. Type sits ON TOP of the photo with sufficient contrast — do
    not letterbox the photo into a smaller area to make room for type.

  - Color palette is strictly the brand palette. No accent colors invented
    outside it. No pure white #fff unless the brand explicitly uses it.

  - No emoji decoration, no clip-art icons, no stock photography signifiers."""


SAFE_ZONES_BLOCK = """SAFE ZONES — RESERVED CANVAS AREAS:

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
    them as part of the scene."""


CHAIN_OF_REFERENCE_BLOCK = """CHAIN OF REFERENCE — visual continuity:

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

  Do NOT shift mood (e.g. dusk -> daylight, warm -> cool, indoor -> outdoor)
  unless the per-slide visual_direction explicitly calls for it."""


# ---------------------------------------------------------------------------
# Vercel Blob hosting (refs upload — same pattern as generate_ads.py)
# ---------------------------------------------------------------------------

def _is_logo_filename(name: str) -> bool:
    n = name.lower()
    return ("logo" in n) or ("wordmark" in n) or ("brand-mark" in n) or ("brand_mark" in n)


def slug_framework(name: str) -> str:
    """Slugify a framework name for filenames. Multi-word names like
    'Before/After', 'Us vs Them', 'Propuesta Comercial' need to collapse to
    'before-after', 'us-vs-them', 'propuesta-comercial' so they're filename-safe
    AND match the SLIDE_RE regex in upload_carousels.py."""
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unknown"


def upload_ref_to_blob(brand_slug: str, image_path: Path, campaign_slug: str = "_kie_refs",
                       override_name: str | None = None) -> str:
    if not PICKS_UPLOAD_TOKEN:
        raise RuntimeError(
            "PICKS_UPLOAD_TOKEN env var required (kie.ai needs public URLs for refs)."
        )
    mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
    with open(image_path, "rb") as f:
        data = f.read()
    upload_name = override_name or image_path.name
    resp = requests.post(
        f"{PICKS_API_BASE}/api/upload/image",
        headers={"Authorization": f"Bearer {PICKS_UPLOAD_TOKEN}"},
        files={"file": (upload_name, data, mime)},
        data={"brand": brand_slug, "campaign": campaign_slug, "name": upload_name},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["url"]


def upload_brand_refs(product_images_dir: Path, brand_slug: str,
                      product_filename: str | None) -> tuple[str | None, str | None]:
    """Upload product (the one named in copy-script.json, or the first non-logo)
    and the brand logo to Vercel Blob. Returns (product_url, logo_url)."""
    if not product_images_dir.exists():
        raise RuntimeError(f"product-images/ not found at {product_images_dir}")

    files = sorted(
        (f for f in product_images_dir.iterdir()
         if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")),
        key=lambda p: p.name,
    )
    if not files:
        raise RuntimeError(f"no product images in {product_images_dir}")

    product_path = None
    logo_path = None

    if product_filename:
        for f in files:
            if f.name == product_filename:
                product_path = f
                break
        if product_path is None:
            raise RuntimeError(
                f"product_image '{product_filename}' from copy-script.json "
                f"not found in {product_images_dir}"
            )

    for f in files:
        if _is_logo_filename(f.name) and logo_path is None:
            logo_path = f
        elif not _is_logo_filename(f.name) and product_path is None:
            product_path = f

    if not product_path:
        raise RuntimeError(f"no non-logo product image found in {product_images_dir}")
    if not logo_path:
        _safe_print(f"  warn: no logo image found in {product_images_dir} — slides will render without logo ref")

    print(f"Hosting refs on Vercel Blob ({brand_slug}/_kie_refs/)...")
    product_url = upload_ref_to_blob(brand_slug, product_path)
    print(f"  OK   [product] {product_path.name}")
    logo_url = None
    if logo_path:
        logo_url = upload_ref_to_blob(brand_slug, logo_path)
        print(f"  OK   [logo   ] {logo_path.name}")
    print()
    return product_url, logo_url


def upload_cover_as_anchor(brand_slug: str, cover_path: Path,
                           campaign_slug: str, carousel_num: int,
                           framework: str) -> str:
    """Upload a generated cover PNG so it can serve as anchor for slides 2..N."""
    name = f"anchor-{campaign_slug}-c{carousel_num:02d}-{slug_framework(framework)}.png"
    return upload_ref_to_blob(brand_slug, cover_path, campaign_slug="_kie_refs",
                              override_name=name)


# ---------------------------------------------------------------------------
# kie.ai helpers (mirrors generate_ads.py)
# ---------------------------------------------------------------------------

def kie_headers():
    return {"Authorization": f"Bearer {KIE_API_KEY}", "Content-Type": "application/json"}


def kie_create_task(prompt: str, input_urls: list, aspect_ratio: str, resolution: str) -> str:
    payload = {
        "model": KIE_MODEL,
        "input": {
            "prompt": prompt,
            "input_urls": input_urls,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        },
    }
    resp = requests.post(KIE_CREATE, headers=kie_headers(), json=payload, timeout=60)
    resp.raise_for_status()
    j = resp.json()
    if j.get("code") != 200:
        raise RuntimeError(f"kie.ai create failed: {j.get('msg')} (code {j.get('code')})")
    return j["data"]["taskId"]


def kie_poll_task(task_id: str) -> str:
    elapsed = 0
    while elapsed < MAX_POLL_TIME:
        resp = requests.get(
            KIE_INFO,
            params={"taskId": task_id},
            headers={"Authorization": f"Bearer {KIE_API_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        j = resp.json()
        if j.get("code") != 200:
            raise RuntimeError(f"kie.ai info failed: {j.get('msg')}")
        d = j["data"]
        state = d.get("state", "")
        if state == "success":
            rj = json.loads(d.get("resultJson") or "{}")
            urls = rj.get("resultUrls") or []
            if not urls:
                raise RuntimeError(f"kie.ai success but no resultUrls: {d}")
            return urls[0]
        if state == "fail":
            raise RuntimeError(f"kie.ai fail: {d.get('failMsg')} (code {d.get('failCode')})")
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    raise TimeoutError(f"kie.ai task {task_id} timed out after {MAX_POLL_TIME}s")


def download_image(image_url: str, save_path: Path):
    r = requests.get(image_url, stream=True, timeout=120)
    r.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)


# ---------------------------------------------------------------------------
# Brand modifier builder
# ---------------------------------------------------------------------------

def build_brand_modifier(brand_dna: dict, asset_pack_vocab: str | None,
                         tone_override: str | None) -> str:
    """Build a 50-90 word brand modifier from brand-dna.json.

    Tolerant to missing fields — we just skip whatever isn't present.
    """
    info = brand_dna.get("brand_info", {}) or {}
    visual = brand_dna.get("visual_identity", {}) or {}
    palette = visual.get("color_palette", {}) or {}
    typography = visual.get("typography", {}) or {}
    photo = brand_dna.get("photography", {}) or {}
    voice_block = brand_dna.get("tone_of_voice", {}) or {}

    name = info.get("brand_name") or info.get("name") or "this brand"
    category = info.get("category") or info.get("vertical") or ""

    primary = palette.get("primary_hex") or palette.get("primary") or ""
    secondary = palette.get("secondary_hex") or palette.get("secondary") or ""
    accent = palette.get("accent_hex") or palette.get("accent") or ""

    display_font = typography.get("display_font") or typography.get("display") or ""
    body_font = typography.get("body_font") or typography.get("body") or ""
    mono_font = typography.get("mono_font") or typography.get("mono") or ""

    lighting = photo.get("lighting") or photo.get("lighting_style") or ""
    mood = photo.get("mood") or ""
    style = photo.get("style") or photo.get("aesthetic") or ""

    voice = (
        tone_override
        or voice_block.get("default_register")
        or voice_block.get("register")
        or ""
    )

    parts = []
    parts.append(f"BRAND: {name}{f' ({category})' if category else ''}.")

    palette_parts = []
    if primary: palette_parts.append(f"primary {primary}")
    if secondary: palette_parts.append(f"secondary {secondary}")
    if accent: palette_parts.append(f"accent {accent}")
    if palette_parts:
        parts.append(f"PALETTE: {', '.join(palette_parts)}.")
        joined = (primary + secondary + accent).lower()
        if "#fff" not in joined and "#ffffff" not in joined:
            parts.append("NEVER use pure white #fff as a background or large fill.")

    type_parts = []
    if display_font: type_parts.append(f"display {display_font}")
    if body_font: type_parts.append(f"body {body_font}")
    if mono_font: type_parts.append(f"mono {mono_font}")
    if type_parts:
        parts.append(f"TYPOGRAPHY: {', '.join(type_parts)}.")

    photo_parts = [p for p in (lighting, mood, style) if p and isinstance(p, str)]
    if photo_parts:
        parts.append(f"PHOTOGRAPHY: {'; '.join(photo_parts)}.")

    if voice:
        parts.append(f"VOICE: {voice}.")

    parts.append(
        "DON'TS: no clinical SaaS aesthetic, no stock-photo signifiers, "
        "no competitor products, no prices, no discount messaging, "
        "no medical claims, no emoji decoration, no generic icons."
    )

    modifier = " ".join(parts)
    if asset_pack_vocab:
        modifier = modifier + "\n\n" + asset_pack_vocab.strip()
    return modifier


# ---------------------------------------------------------------------------
# Per-slide prompt builder
# ---------------------------------------------------------------------------

def build_slide_block(carousel: dict, slide: dict, total_slides: int) -> str:
    role = slide.get("role", "")
    headline = slide.get("headline", "").strip()
    body = slide.get("body", "").strip()
    visual = slide.get("visual_direction", "").strip()
    n = slide["slide"]
    fwk = carousel["framework"]

    parts = [f"THIS SLIDE: {n}/{total_slides} - role: {role} ({fwk} framework)."]
    if headline:
        parts.append(f'HEADLINE TO RENDER ON THE SLIDE (verbatim, in the brand display font): "{headline}"')
    if body:
        parts.append(f'BODY COPY TO RENDER (verbatim, in the brand body font, 1-2 lines max): "{body}"')
    parts.append(f'SLIDE INDICATOR (bottom-right, brand mono font): "{n}/{total_slides}"')
    if visual:
        parts.append(f"VISUAL DIRECTION FOR THIS SPECIFIC SLIDE: {visual}")
    return "\n\n".join(parts)


def build_full_prompt(brand_modifier: str, carousel: dict, slide: dict,
                      total_slides: int, is_cover: bool) -> str:
    parts = [brand_modifier, LAYOUT_PIN_BLOCK, SAFE_ZONES_BLOCK]
    if not is_cover:
        parts.append(CHAIN_OF_REFERENCE_BLOCK)
    parts.append(build_slide_block(carousel, slide, total_slides))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Worker (single slide)
# ---------------------------------------------------------------------------

def _process_slide(prompt: str, input_urls: list, aspect: str, resolution: str,
                   save_path: Path, label: str) -> dict:
    if not input_urls:
        _safe_print(f"  ! {label}  no input_urls — skipping")
        return {"label": label, "ok": False, "path": None, "error": "no input_urls"}
    try:
        task_id = kie_create_task(prompt, input_urls, aspect, resolution)
        _safe_print(f"  -> {label}  queued task={task_id[:12]}...")
        result_url = kie_poll_task(task_id)
        download_image(result_url, save_path)
        _safe_print(f"  ok {label}  saved {save_path.name}")
        return {"label": label, "ok": True, "path": save_path, "kie_url": result_url}
    except Exception as e:
        _safe_print(f"  XX {label}  {e}")
        return {"label": label, "ok": False, "path": None, "error": str(e)}


# ---------------------------------------------------------------------------
# Phase orchestrators
# ---------------------------------------------------------------------------

def filename_for(carousel_num: int, framework: str, format_str: str, slide_num: int) -> str:
    return f"{carousel_num:02d}-{slug_framework(framework)}-{format_str}-{slide_num:02d}.png"


def cover_path(campaign_dir: Path, carousel_num: int, framework: str) -> Path:
    return campaign_dir / filename_for(carousel_num, framework, "9x16", 1)


def slide_path(campaign_dir: Path, carousel_num: int, framework: str, slide_num: int) -> Path:
    return campaign_dir / filename_for(carousel_num, framework, "9x16", slide_num)


def run_covers(copy_script: dict, campaign_dir: Path, brand_modifier: str,
               product_url: str, logo_url: str | None, resolution: str,
               concurrency: int, only_carousels: set[int] | None = None) -> list[dict]:
    refs = [product_url] + ([logo_url] if logo_url else [])
    jobs = []
    for c in copy_script["carousels"]:
        cn = c["carousel"]
        if only_carousels is not None and cn not in only_carousels:
            continue
        slides = c["slides"]
        total = len(slides)
        cover_slide = next((s for s in slides if s["slide"] == 1), None)
        if not cover_slide:
            _safe_print(f"  ! carousel {cn} has no slide 1 in copy-script.json — skipping")
            continue
        prompt = build_full_prompt(brand_modifier, c, cover_slide, total, is_cover=True)
        path = cover_path(campaign_dir, cn, c["framework"])
        label = f"[c{cn:02d} {c['framework']:5s} 1/{total} cover]"
        jobs.append((prompt, refs, "9:16", resolution, path, label))

    if not jobs:
        return []

    print(f"\nGenerating {len(jobs)} cover(s) in parallel (concurrency={concurrency})...")
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(_process_slide, *j) for j in jobs]
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def run_slides(copy_script: dict, campaign_dir: Path, brand_modifier: str,
               product_url: str, logo_url: str | None, resolution: str,
               concurrency: int, brand_slug: str, campaign_slug: str,
               only_carousels: set[int] | None = None,
               only_slide: tuple[int, int] | None = None) -> list[dict]:
    """Generate slides 2..N for each carousel. Uploads each carousel's cover
    as anchor first, then dispatches all (carousel, slide) jobs in parallel."""
    base_refs = [product_url] + ([logo_url] if logo_url else [])

    print("\nUploading covers as anchors for chain-of-reference...")
    anchors: dict[int, str] = {}
    for c in copy_script["carousels"]:
        cn = c["carousel"]
        if only_carousels is not None and cn not in only_carousels:
            continue
        if only_slide is not None and only_slide[0] != cn:
            continue
        cpath = cover_path(campaign_dir, cn, c["framework"])
        if not cpath.exists():
            _safe_print(f"  ! carousel {cn} cover missing at {cpath} — run --phase covers first")
            continue
        try:
            anchor_url = upload_cover_as_anchor(brand_slug, cpath, campaign_slug, cn, c["framework"])
            anchors[cn] = anchor_url
            print(f"  ok c{cn:02d} {c['framework']:5s} anchor uploaded")
        except Exception as e:
            _safe_print(f"  XX c{cn:02d} anchor upload failed: {e}")

    jobs = []
    for c in copy_script["carousels"]:
        cn = c["carousel"]
        if cn not in anchors:
            continue
        anchor_url = anchors[cn]
        refs = base_refs + [anchor_url]
        slides = c["slides"]
        total = len(slides)
        for s in slides:
            if s["slide"] == 1:
                continue
            if only_slide is not None and (cn, s["slide"]) != only_slide:
                continue
            prompt = build_full_prompt(brand_modifier, c, s, total, is_cover=False)
            path = slide_path(campaign_dir, cn, c["framework"], s["slide"])
            label = f"[c{cn:02d} {c['framework']:5s} {s['slide']}/{total} {s.get('role','')[:9]}]"
            jobs.append((prompt, refs, "9:16", resolution, path, label))

    if not jobs:
        print("  (no slides to generate)")
        return []

    print(f"\nGenerating {len(jobs)} slide(s) in parallel (concurrency={concurrency})...")
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [ex.submit(_process_slide, *j) for j in jobs]
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


# ---------------------------------------------------------------------------
# Gallery builders (Genera Impacto branded — Carbón Tech / Azul Impacto)
# ---------------------------------------------------------------------------

GI_HEAD = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>{title} - Genera Impacto</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@200;400;600;800;900&family=Poppins:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --carbon:#0A0F1C; --grafito:#1A2024; --grafito-2:#2A3142;
  --azul-brand:#0048AD; --azul-electrico:#1887E1;
  --white:#FFFFFF; --muted:#6B7280; --muted-2:#9CA3AF;
}}
html,body{{background:var(--carbon)}}
body{{font-family:'Poppins',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--white);
  padding:3rem 2.5rem 4rem;min-height:100vh;
  background:radial-gradient(circle at 80% 0%, rgba(0,72,173,.18) 0%, transparent 55%), var(--carbon)}}
.header{{display:flex;align-items:flex-start;justify-content:space-between;gap:2rem;
  margin-bottom:2.5rem;padding-bottom:1.5rem;border-bottom:1px solid var(--grafito-2)}}
.brand{{display:flex;align-items:center;gap:.85rem}}
.brand-mark{{width:46px;height:46px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.brand-mark img{{width:100%;height:100%;object-fit:contain;display:block}}
.brand-id .eye{{font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--azul-electrico);
  letter-spacing:.2em;text-transform:uppercase;display:block;margin-bottom:3px}}
.brand-id .nm{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:.95rem;color:var(--white)}}
.meta-block{{text-align:right;font-family:'JetBrains Mono',monospace;font-size:.68rem;
  color:var(--muted);letter-spacing:.13em;text-transform:uppercase;line-height:1.85}}
.meta-block strong{{color:var(--white);font-weight:500}}
.eyebrow{{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--azul-electrico);
  letter-spacing:.22em;text-transform:uppercase;margin-bottom:.7rem}}
h1{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:2.6rem;line-height:1.05;
  letter-spacing:-.025em;margin-bottom:2.5rem}}
h1 .accent{{color:var(--azul-electrico)}}
.carousel-card{{background:var(--grafito);border-radius:14px;padding:1.5rem;margin-bottom:1.5rem;
  border:1px solid var(--grafito-2)}}
.carousel-card h2{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:1.15rem;color:var(--white);
  margin-bottom:.3rem;letter-spacing:-.01em}}
.carousel-meta{{font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--muted);
  letter-spacing:.18em;text-transform:uppercase;margin-bottom:1.2rem}}
.carousel-meta .fwk{{color:var(--azul-electrico)}}
.slides-strip{{display:flex;gap:1rem;overflow-x:auto;padding-bottom:.5rem;scrollbar-width:thin;scrollbar-color:var(--grafito-2) transparent}}
.slides-strip::-webkit-scrollbar{{height:6px}}
.slides-strip::-webkit-scrollbar-track{{background:transparent}}
.slides-strip::-webkit-scrollbar-thumb{{background:var(--grafito-2);border-radius:3px}}
.slide{{flex-shrink:0;width:200px;border-radius:8px;overflow:hidden;background:#000;border:1px solid var(--grafito-2);position:relative}}
.slide img{{width:100%;display:block;aspect-ratio:9/16;object-fit:cover;background:#000}}
.slide.missing{{aspect-ratio:9/16;display:flex;align-items:center;justify-content:center;
  font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--muted);letter-spacing:.18em;text-transform:uppercase}}
.slide-label{{padding:.6rem .8rem;border-top:1px solid var(--grafito-2);background:var(--carbon)}}
.slide-num{{font-family:'JetBrains Mono',monospace;font-size:.62rem;color:var(--azul-electrico);letter-spacing:.18em;text-transform:uppercase}}
.slide-role{{font-family:'Montserrat',sans-serif;font-size:.78rem;color:var(--white);font-weight:600;margin-top:2px}}
footer{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--grafito-2);
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;
  font-family:'JetBrains Mono',monospace;font-size:.62rem;color:var(--muted);letter-spacing:.18em;text-transform:uppercase}}
footer a{{color:var(--azul-electrico);text-decoration:none}}
@media (max-width:760px){{body{{padding:2rem 1.25rem}}h1{{font-size:1.7rem}}.header{{flex-direction:column;gap:1.25rem}}.meta-block{{text-align:left}}.slide{{width:160px}}}}
</style></head><body>
<header class="header">
  <div class="brand">
    <div class="brand-mark"><img src="https://ia.generarimpacto.com/logo.png" alt="Genera Impacto"></div>
    <div class="brand-id">
      <span class="eye">Genera - Impacto - MMXXVI</span>
      <span class="nm">Performance Studio</span>
    </div>
  </div>
  <div class="meta-block">
    Brand - <strong>{brand}</strong><br>
    Date - <strong>{date}</strong><br>
    Engine - <strong>kie.ai gpt-image-2</strong>
  </div>
</header>
<p class="eyebrow">{eyebrow}</p>
<h1>{brand} - <span class="accent">{accent_label}</span></h1>"""

GI_FOOT = """<footer>
  <span>Genera Impacto - <a href="https://generarimpacto.com">generarimpacto.com</a> - hola@generarimpacto.com</span>
  <span>Internal - Brand v1.0 - {year}</span>
</footer></body></html>"""


def _carousel_card_html(carousel: dict, campaign_dir: Path, only_cover: bool) -> str:
    cn = carousel["carousel"]
    fwk = carousel["framework"]
    total = len(carousel["slides"])
    slide_html = []
    for s in carousel["slides"]:
        sn = s["slide"]
        path = slide_path(campaign_dir, cn, fwk, sn)
        if only_cover and sn != 1:
            continue
        if path.exists():
            slide_html.append(
                f'<div class="slide"><img src="{path.name}" loading="lazy" alt="">'
                f'<div class="slide-label"><div class="slide-num">{sn}/{total}</div>'
                f'<div class="slide-role">{s.get("label") or s.get("role","")}</div></div></div>'
            )
        else:
            slide_html.append(
                f'<div class="slide missing"><div class="slide-label" style="border:none;background:transparent">'
                f'<div class="slide-num">{sn}/{total}</div><div class="slide-role">pendiente</div></div></div>'
            )
    return (
        f'<section class="carousel-card">'
        f'<h2>Carrusel #{cn:02d}</h2>'
        f'<div class="carousel-meta"><span class="fwk">{fwk}</span> - {total} slides</div>'
        f'<div class="slides-strip">{"".join(slide_html)}</div>'
        f'</section>'
    )


def build_gallery(copy_script: dict, campaign_dir: Path, only_cover: bool,
                  out_path: Path, accent_label: str, eyebrow: str):
    brand = copy_script.get("brand", "Brand")
    date_s = time.strftime("%d - %m - %Y")
    year_s = time.strftime("%Y")
    head = GI_HEAD.format(
        title=f"{brand} - Carousels", brand=brand, date=date_s,
        eyebrow=eyebrow, accent_label=accent_label,
    )
    cards = "\n".join(_carousel_card_html(c, campaign_dir, only_cover)
                      for c in copy_script["carousels"])
    foot = GI_FOOT.format(year=year_s)
    # Inject auto-reload (meta refresh + JS polling) so the SAME tab refreshes
    # on subsequent rebuilds instead of spawning new tabs.
    head = head.replace("</head>", AUTO_RELOAD_HEAD + "</head>", 1)
    out_path.write_text(head + cards + foot, encoding="utf-8")
    write_gallery_version(out_path)


# ---------------------------------------------------------------------------
# Auto-open helpers
#
# Problem: os.startfile / xdg-open / open spawn a NEW browser tab on every
# call — annoying when iterating with --regenerate. Solution:
#   1. open_once_in_browser only opens if marker file is missing or stale (>4h)
#   2. AUTO_RELOAD_HEAD injected into every gallery: <meta refresh 15s>
#      (reliable on file://) + JS polling of .version file (3s, fast when
#      file:// fetch is allowed — Firefox by default).
#   3. Each rebuild_gallery writes <gallery>.version next to the HTML so
#      the polling script detects the change and reload()s the SAME tab.
# ---------------------------------------------------------------------------

AUTO_RELOAD_HEAD = """<meta http-equiv="refresh" content="15">
<script>
(async function() {
  // Auto-reload the same tab when the gallery rebuilds. Avoids spawning a
  // new browser tab on every --regenerate. Best-effort fetch polling at 3s;
  // <meta refresh 15s> above is the file:// fallback if fetch is blocked.
  let initial = null;
  async function check() {
    try {
      const url = location.pathname.replace(/\\.html$/, ".version") + "?t=" + Date.now();
      const r = await fetch(url, { cache: "no-store" });
      if (!r.ok) return;
      const v = (await r.text()).trim();
      if (initial === null) initial = v;
      else if (v !== initial) location.reload();
    } catch (e) {}
  }
  setInterval(check, 3000);
  check();
})();
</script>"""


def open_in_browser(path: Path):
    """Raw open — used by open_once_in_browser. Cross-platform best-effort."""
    p = str(path.resolve())
    sysname = platform.system()
    try:
        if sysname == "Windows":
            os.startfile(p)  # type: ignore[attr-defined]
        elif sysname == "Darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])
        print(f"\nOpening in browser: {p}")
    except Exception as e:
        print(f"\n(no pude auto-abrir: {e}) -- abrí manualmente: {p}")


def open_once_in_browser(path: Path, force: bool = False):
    """Open path in browser ONLY if marker is missing or older than 4h.
    Subsequent rebuilds in the same session are picked up by the existing
    tab via the auto-reload script (meta refresh 15s + JS polling 3s).

    Pass force=True (--reopen flag) to override the marker."""
    marker = path.parent / f".{path.stem}.opened"
    if not force and marker.exists():
        try:
            if time.time() - marker.stat().st_mtime < 4 * 3600:
                _safe_print(
                    f"\n({path.name} ya está abierta — la tab existente se va a refrescar sola "
                    f"(meta refresh 15s + JS polling 3s). Pasá --reopen para forzar nueva tab.)"
                )
                marker.touch()  # slide the 4h window forward while user iterates
                return
        except Exception:
            pass
    open_in_browser(path)
    marker.touch()


def write_gallery_version(html_path: Path):
    """Write a tiny .version file next to the gallery HTML so the auto-reload
    JS poller can detect rebuilds. Written every time build_gallery runs."""
    version_path = html_path.with_suffix(".version")
    version_path.write_text(str(time.time()), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

REGEN_RE = re.compile(r"^(?P<c>\d+)(?:\.(?P<s>\d+|\*))?$")


def parse_regenerate(arg: str) -> tuple[set[int], tuple[int, int] | None]:
    """'1' -> ({1}, None)   '1.2' -> ({1}, (1,2))   '1.*' -> ({1}, None)"""
    m = REGEN_RE.match(arg.strip())
    if not m:
        sys.exit(f"ERROR: --regenerate '{arg}' must be N or N.M (e.g. '1', '1.2', '1.*')")
    cn = int(m.group("c"))
    s = m.group("s")
    if s is None or s == "*":
        return ({cn}, None)
    return ({cn}, (cn, int(s)))


def main():
    p = argparse.ArgumentParser(description="Generate carousels via kie.ai gpt-image-2")
    p.add_argument("--phase", choices=["covers", "slides", "all"], default="all",
                   help="Which phase to run (default: all = covers then slides)")
    p.add_argument("--regenerate", type=str, default=None,
                   help="Regenerate one slide ('1.2') or one full carousel ('1' or '1.*')")
    p.add_argument("--resolution", choices=["1K", "2K", "4K"], default=DEFAULT_RESOLUTION)
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    p.add_argument("--no-open", action="store_true", help="Skip auto-open of gallery")
    p.add_argument("--reopen", action="store_true",
                   help="Force opening a new browser tab even if the gallery was already opened "
                        "in this session (default: open once, then auto-reload the same tab)")
    p.add_argument("--dry-run", action="store_true", help="Print prompts without API calls")
    p.add_argument("--campaign-dir", type=str, default=".",
                   help="Campaign folder (default: cwd)")
    p.add_argument("--brand-dir", type=str, default=None,
                   help="Brand folder (default: <campaign-dir>/../..)")
    args = p.parse_args()

    campaign_dir = Path(args.campaign_dir).resolve()
    brand_dir = Path(args.brand_dir).resolve() if args.brand_dir else campaign_dir.parent.parent

    copy_script_path = campaign_dir / "copy-script.json"
    if not copy_script_path.exists():
        sys.exit(f"ERROR: {copy_script_path} not found. Run Phase 3 first.")
    with open(copy_script_path, encoding="utf-8") as f:
        copy_script = json.load(f)

    brand_dna_path = brand_dir / "brand-dna.json"
    brand_dna = {}
    if brand_dna_path.exists():
        with open(brand_dna_path, encoding="utf-8") as f:
            brand_dna = json.load(f)
    else:
        print(f"  warn: {brand_dna_path} not found — using minimal modifier from copy-script.json metadata")

    asset_pack_vocab = None
    assets_path = brand_dir / "assets.json"
    if assets_path.exists():
        try:
            with open(assets_path, encoding="utf-8") as f:
                a = json.load(f)
            asset_pack_vocab = a.get("prompt_vocabulary") or None
        except Exception as e:
            print(f"  warn: could not parse {assets_path}: {e}")

    brand_slug = copy_script.get("brand_slug") or brand_dir.name
    campaign_slug = copy_script.get("campaign_slug") or campaign_dir.name
    brand_name = copy_script.get("brand", brand_slug)
    tone_override = copy_script.get("tone")
    product_filename = copy_script.get("product_image")

    brand_modifier = build_brand_modifier(brand_dna, asset_pack_vocab, tone_override)

    only_carousels = None
    only_slide = None
    if args.regenerate:
        only_carousels, only_slide = parse_regenerate(args.regenerate)
        if only_slide is not None:
            args.phase = "slides" if only_slide[1] != 1 else "covers"

    print(f"\n{'='*64}")
    print(f"  Carousel Generator (kie.ai gpt-image-2) - {brand_name}")
    print(f"  Campaign: {campaign_slug}")
    print(f"  Phase: {args.phase} | Resolution: {args.resolution} | Concurrency: {args.concurrency}")
    if only_carousels:
        print(f"  Filter: carousels {sorted(only_carousels)}" + (f" slide {only_slide[1]}" if only_slide else ""))
    print(f"{'='*64}\n")

    if args.dry_run:
        print("DRY RUN — building first prompt as a sample:\n")
        c0 = copy_script["carousels"][0]
        s0 = c0["slides"][0]
        sample = build_full_prompt(brand_modifier, c0, s0, len(c0["slides"]), is_cover=True)
        print(sample[:2000])
        if len(sample) > 2000:
            print(f"\n... [{len(sample) - 2000} more chars]")
        return

    if not KIE_API_KEY:
        sys.exit("ERROR: KIE_API_KEY env var required (https://kie.ai/api-key).")
    if not PICKS_UPLOAD_TOKEN:
        sys.exit("ERROR: PICKS_UPLOAD_TOKEN env var required.")

    product_url, logo_url = upload_brand_refs(brand_dir / "product-images", brand_slug, product_filename)

    t_start = time.time()
    cover_results: list[dict] = []
    slide_results: list[dict] = []

    if args.phase in ("covers", "all"):
        cover_results = run_covers(
            copy_script, campaign_dir, brand_modifier,
            product_url, logo_url, args.resolution, args.concurrency,
            only_carousels=only_carousels,
        )
        # Always rebuild preview-covers.html so partial regenerations reflect.
        preview_path = campaign_dir / "preview-covers.html"
        build_gallery(copy_script, campaign_dir, only_cover=True,
                      out_path=preview_path,
                      accent_label="covers preview.",
                      eyebrow=f"Carousels - Phase 4 - {len(copy_script['carousels'])} covers - 9:16")
        if args.phase == "covers" and not args.no_open:
            open_once_in_browser(preview_path, force=args.reopen)

    if args.phase in ("slides", "all"):
        slide_results = run_slides(
            copy_script, campaign_dir, brand_modifier,
            product_url, logo_url, args.resolution, args.concurrency,
            brand_slug, campaign_slug,
            only_carousels=only_carousels, only_slide=only_slide,
        )

    # curation.html always reflects the full filesystem state
    curation_path = campaign_dir / "curation.html"
    total_slides = sum(len(c["slides"]) for c in copy_script["carousels"])
    build_gallery(copy_script, campaign_dir, only_cover=False,
                  out_path=curation_path,
                  accent_label=f"{total_slides:02d} slides.",
                  eyebrow=f"Carousels - {len(copy_script['carousels'])} carruseles - 9:16")

    elapsed = time.time() - t_start
    ok = sum(1 for r in cover_results + slide_results if r["ok"])
    fail = sum(1 for r in cover_results + slide_results if not r["ok"])
    print(f"\n{'='*64}")
    print(f"  Done  |  OK: {ok}  |  FAIL: {fail}  |  Wall: {elapsed:.1f}s")
    print(f"  Output: {campaign_dir}/")
    print(f"{'='*64}\n")

    manifest = {
        "brand": brand_name,
        "brand_slug": brand_slug,
        "campaign_slug": campaign_slug,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": "kie.ai/gpt-image-2-image-to-image",
        "resolution": args.resolution,
        "phase": args.phase,
        "concurrency": args.concurrency,
        "wall_time_seconds": round(elapsed, 1),
        "carousels": [
            {
                "carousel": c["carousel"],
                "framework": c["framework"],
                "slide_count": len(c["slides"]),
                "slides": [
                    {
                        "slide": s["slide"],
                        "role": s.get("role"),
                        "file": filename_for(c["carousel"], c["framework"], "9x16", s["slide"]),
                        "exists": (campaign_dir / filename_for(c["carousel"], c["framework"], "9x16", s["slide"])).exists(),
                    }
                    for s in c["slides"]
                ],
            }
            for c in copy_script["carousels"]
        ],
    }
    (campaign_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if not args.no_open and args.phase != "covers":
        open_once_in_browser(curation_path, force=args.reopen)


if __name__ == "__main__":
    main()
