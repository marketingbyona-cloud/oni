#!/usr/bin/env python3
"""
Carousel 1:1 Reformatter — Phase 8: regenerate the carousels the client picked
in 1:1 (square) using each 9:16 slide as visual anchor + DROP-DON'T-CRAM directive.

After the client submits picks at /c/{brand}/{campaign} on estrategia-ia, the
user reads off the picked carousel numbers and runs:

    cd brands/{brand}/carousels/{campaign}
    python regenerate_carousels_1x1.py --carousels 1,2

For each picked carousel x each existing 9:16 slide:
  - Upload the 9:16 PNG to Vercel Blob -> anchor URL
  - kie.ai gpt-image-2-image-to-image at aspect 1:1 with refs:
        [product_url, logo_url, 9x16_anchor_url]
  - Output: picks-1x1/{NN:02d}-{framework}-1x1-{slide:02d}.png

After all picks regenerate, builds picks-consistency.html — a single gallery
that shows the 9:16 anchor (Azul Impacto badge) side-by-side with the 1:1
sibling for each slide of each picked carousel. Auto-opens in browser.

Mirrors regenerate_picks.py from staticadscreator (DROP-DON'T-CRAM directive,
identical kie.ai stack, identical Vercel Blob ref hosting).

Usage:
    python regenerate_carousels_1x1.py --carousels 1,2
    python regenerate_carousels_1x1.py --carousels 1
    python regenerate_carousels_1x1.py --slide 1.2     # carousel 1 slide 2 only
    python regenerate_carousels_1x1.py --dry-run

Required env vars:
    KIE_API_KEY            kie.ai bearer token
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
DEFAULT_CONCURRENCY = 10

_print_lock = threading.Lock()
def _safe_print(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)


# ---------------------------------------------------------------------------
# Universal prompt blocks (subset of generate_carousels.py)
# ---------------------------------------------------------------------------

LAYOUT_PIN_BLOCK = """LAYOUT PIN — apply to this slide without exception:

  - Brand mark / wordmark anchored TOP-LEFT, inset 8% from each edge.
    Render the wordmark exactly as in the attached logo reference.

  - Slide-number indicator anchored BOTTOM-RIGHT, inset 6% from each edge,
    in the brand's mono typography. Format "{N}/{TOTAL}" — same as the 9:16
    sibling. Small (<= 2.5% of canvas height), low-contrast.

  - Photographic subject occupies a minimum of 60% of the canvas.

  - Color palette is strictly the brand palette — no invented hues, no pure
    white #fff unless brand explicitly uses it.

  - No emoji decoration, no clip-art icons, no stock photography signifiers."""


SAFE_ZONES_1x1_BLOCK = """SAFE ZONES — RESERVED CANVAS AREAS (1:1 square):

  - Top 6% of canvas: leave as continuous photographic breathing room. NO
    type / badge / banner here. The Instagram status bar overlaps slightly
    when posted to feed.

  - Bottom 12% of canvas: reserve as continuous photographic breathing room.
    NO type / badge / banner here. The Instagram caption preview lives here
    on the feed.

  - The reserved bands MUST be visually continuous extensions of the photo —
    no horizontal stripe, no banner, no color block."""


def drop_dont_cram_block(carousel_num: int, framework: str, slide_num: int,
                         total_slides: int) -> str:
    return f"""FORMAT OVERRIDE — TARGET ASPECT IS NOW 1:1 SQUARE.

This slide was originally composed for 9:16 portrait. The third image attached
is the 9:16 sibling — your visual anchor. You are reframing THE SAME SCENE for
a square canvas.

GOLDEN RULE — DROP, DON'T CRAM. If a text block, badge, ribbon, caption,
secondary headline, supporting graphic, or stat doesn't fit naturally in the
square aspect, OMIT IT. Do not shrink to fit. Do not crowd. Do not stretch. A
clean, well-composed square with FEWER elements beats a cramped square with
everything.

PRESERVE (priority order):
  1. The product / scene subject (exactly as in the attached 9:16 anchor)
  2. The brand identity — palette, typography, mood, photographic style
  3. The headline — keep verbatim, may reflow lines
  4. The slide indicator "{slide_num}/{total_slides}" (bottom-right corner)
  5. The brand mark (top-left corner)

CAN BE DROPPED IF NEEDED:
  - Body / supporting copy (drop entirely if no clean place fits it)
  - Ribbons, badges, ornament marks
  - Secondary text blocks

INHERIT FROM THE 9:16 ANCHOR (the third attached image):
  - Identical color palette
  - Identical lighting direction, intensity, color temperature
  - Identical photographic style (lens, depth of field, grain, contrast)
  - Identical typographic treatment

This is carousel #{carousel_num:02d} ({framework} framework), slide
{slide_num} of {total_slides}. Same product, same brand, just a different
canvas shape."""


# ---------------------------------------------------------------------------
# Vercel Blob hosting
# ---------------------------------------------------------------------------

def _is_logo_filename(name: str) -> bool:
    n = name.lower()
    return ("logo" in n) or ("wordmark" in n) or ("brand-mark" in n) or ("brand_mark" in n)


def slug_framework(name: str) -> str:
    """Same slug as generate_carousels.py — keeps filenames in sync between
    the 9:16 generator and the 1:1 regenerator. 'Propuesta Comercial' →
    'propuesta-comercial', 'Before/After' → 'before-after', etc."""
    import re as _re
    return _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unknown"


def upload_to_blob(brand_slug: str, image_path: Path,
                   campaign_slug: str = "_kie_refs",
                   override_name: str | None = None) -> str:
    if not PICKS_UPLOAD_TOKEN:
        raise RuntimeError("PICKS_UPLOAD_TOKEN env var required.")
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
                      product_filename: str | None) -> tuple[str, str | None]:
    files = sorted(
        (f for f in product_images_dir.iterdir()
         if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")),
        key=lambda p: p.name,
    )
    product_path = None
    logo_path = None
    if product_filename:
        for f in files:
            if f.name == product_filename:
                product_path = f
                break
    for f in files:
        if _is_logo_filename(f.name) and logo_path is None:
            logo_path = f
        elif not _is_logo_filename(f.name) and product_path is None:
            product_path = f
    if not product_path:
        raise RuntimeError(f"no product image found in {product_images_dir}")
    print(f"Hosting brand refs on Vercel Blob ({brand_slug}/_kie_refs/)...")
    product_url = upload_to_blob(brand_slug, product_path)
    print(f"  OK   [product] {product_path.name}")
    logo_url = None
    if logo_path:
        logo_url = upload_to_blob(brand_slug, logo_path)
        print(f"  OK   [logo   ] {logo_path.name}")
    print()
    return product_url, logo_url


# ---------------------------------------------------------------------------
# kie.ai helpers
# ---------------------------------------------------------------------------

def kie_headers():
    return {"Authorization": f"Bearer {KIE_API_KEY}", "Content-Type": "application/json"}


def kie_create_task(prompt: str, input_urls: list, aspect: str, resolution: str) -> str:
    payload = {
        "model": KIE_MODEL,
        "input": {
            "prompt": prompt, "input_urls": input_urls,
            "aspect_ratio": aspect, "resolution": resolution,
        },
    }
    r = requests.post(KIE_CREATE, headers=kie_headers(), json=payload, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("code") != 200:
        raise RuntimeError(f"kie.ai create failed: {j.get('msg')}")
    return j["data"]["taskId"]


def kie_poll_task(task_id: str) -> str:
    elapsed = 0
    while elapsed < MAX_POLL_TIME:
        r = requests.get(KIE_INFO, params={"taskId": task_id},
                         headers={"Authorization": f"Bearer {KIE_API_KEY}"}, timeout=30)
        r.raise_for_status()
        j = r.json()
        if j.get("code") != 200:
            raise RuntimeError(f"kie.ai info failed: {j.get('msg')}")
        d = j["data"]
        state = d.get("state", "")
        if state == "success":
            rj = json.loads(d.get("resultJson") or "{}")
            urls = rj.get("resultUrls") or []
            if not urls:
                raise RuntimeError(f"no resultUrls: {d}")
            return urls[0]
        if state == "fail":
            raise RuntimeError(f"kie.ai fail: {d.get('failMsg')}")
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    raise TimeoutError(f"timed out after {MAX_POLL_TIME}s")


def download_image(url: str, save_path: Path):
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)


# ---------------------------------------------------------------------------
# Brand modifier (compact — same logic as generate_carousels.py)
# ---------------------------------------------------------------------------

def build_brand_modifier(brand_dna: dict, asset_pack_vocab: str | None,
                         tone_override: str | None) -> str:
    info = brand_dna.get("brand_info", {}) or {}
    visual = brand_dna.get("visual_identity", {}) or {}
    palette = visual.get("color_palette", {}) or {}
    typo = visual.get("typography", {}) or {}
    photo = brand_dna.get("photography", {}) or {}
    voice_block = brand_dna.get("tone_of_voice", {}) or {}

    name = info.get("brand_name") or info.get("name") or "this brand"
    cat = info.get("category") or info.get("vertical") or ""
    primary = palette.get("primary_hex") or palette.get("primary") or ""
    secondary = palette.get("secondary_hex") or palette.get("secondary") or ""
    accent = palette.get("accent_hex") or palette.get("accent") or ""
    display = typo.get("display_font") or typo.get("display") or ""
    body = typo.get("body_font") or typo.get("body") or ""
    mono = typo.get("mono_font") or typo.get("mono") or ""
    voice = (tone_override or voice_block.get("default_register")
             or voice_block.get("register") or "")

    parts = [f"BRAND: {name}{f' ({cat})' if cat else ''}."]
    pp = []
    if primary: pp.append(f"primary {primary}")
    if secondary: pp.append(f"secondary {secondary}")
    if accent: pp.append(f"accent {accent}")
    if pp:
        parts.append(f"PALETTE: {', '.join(pp)}.")
        if "#fff" not in (primary + secondary + accent).lower() and "#ffffff" not in (primary + secondary + accent).lower():
            parts.append("NEVER use pure white #fff.")
    tp = []
    if display: tp.append(f"display {display}")
    if body: tp.append(f"body {body}")
    if mono: tp.append(f"mono {mono}")
    if tp:
        parts.append(f"TYPOGRAPHY: {', '.join(tp)}.")
    photo_parts = [p for p in (photo.get("lighting"), photo.get("mood"), photo.get("style")) if p and isinstance(p, str)]
    if photo_parts:
        parts.append(f"PHOTOGRAPHY: {'; '.join(photo_parts)}.")
    if voice:
        parts.append(f"VOICE: {voice}.")
    parts.append("DON'TS: no clinical aesthetic, no stock-photo cues, no competitors, no prices, no discount messaging, no medical claims, no emoji.")

    out = " ".join(parts)
    if asset_pack_vocab:
        out = out + "\n\n" + asset_pack_vocab.strip()
    return out


# ---------------------------------------------------------------------------
# Per-slide prompt builder
# ---------------------------------------------------------------------------

def build_1x1_prompt(brand_modifier: str, carousel: dict, slide: dict,
                     total_slides: int) -> str:
    cn = carousel["carousel"]
    fwk = carousel["framework"]
    sn = slide["slide"]
    headline = (slide.get("headline") or "").strip()
    body = (slide.get("body") or "").strip()
    visual = (slide.get("visual_direction") or "").strip()

    parts = [
        brand_modifier,
        LAYOUT_PIN_BLOCK,
        SAFE_ZONES_1x1_BLOCK,
        drop_dont_cram_block(cn, fwk, sn, total_slides),
    ]
    sblock = [f"THIS SLIDE: {sn}/{total_slides} - role: {slide.get('role','')} ({fwk})."]
    if headline:
        sblock.append(f'HEADLINE TO RENDER (verbatim): "{headline}"')
    if body:
        sblock.append(f'BODY COPY TO RENDER (verbatim, may drop if no fit): "{body}"')
    sblock.append(f'SLIDE INDICATOR: "{sn}/{total_slides}"')
    if visual:
        sblock.append(f"VISUAL DIRECTION (already realised in the 9:16 anchor — preserve mood): {visual}")
    parts.append("\n\n".join(sblock))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Per-slide worker
# ---------------------------------------------------------------------------

def _process_slide(prompt: str, refs: list, save_path: Path, label: str,
                   resolution: str) -> dict:
    try:
        task_id = kie_create_task(prompt, refs, "1:1", resolution)
        _safe_print(f"  -> {label}  queued task={task_id[:12]}...")
        result_url = kie_poll_task(task_id)
        download_image(result_url, save_path)
        _safe_print(f"  ok {label}  saved {save_path.name}")
        return {"label": label, "ok": True, "path": save_path}
    except Exception as e:
        _safe_print(f"  XX {label}  {e}")
        return {"label": label, "ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# File path helpers
# ---------------------------------------------------------------------------

def slide_9x16_path(campaign_dir: Path, carousel_num: int, framework: str, slide_num: int) -> Path:
    return campaign_dir / f"{carousel_num:02d}-{slug_framework(framework)}-9x16-{slide_num:02d}.png"


def slide_1x1_path(campaign_dir: Path, carousel_num: int, framework: str, slide_num: int) -> Path:
    return campaign_dir / "picks-1x1" / f"{carousel_num:02d}-{slug_framework(framework)}-1x1-{slide_num:02d}.png"


# ---------------------------------------------------------------------------
# picks-consistency.html builder
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
  --white:#FFFFFF; --muted:#6B7280;
}}
html,body{{background:var(--carbon)}}
body{{font-family:'Poppins',sans-serif;color:var(--white);
  padding:3rem 2.5rem 4rem;min-height:100vh;max-width:920px;margin:0 auto;
  background:radial-gradient(circle at 80% 0%, rgba(0,72,173,.18) 0%, transparent 55%), var(--carbon)}}
.header{{display:flex;align-items:flex-start;justify-content:space-between;gap:2rem;
  margin-bottom:2.5rem;padding-bottom:1.5rem;border-bottom:1px solid var(--grafito-2)}}
.brand{{display:flex;align-items:center;gap:.85rem}}
.brand-mark{{width:46px;height:46px}}
.brand-mark img{{width:100%;height:100%;object-fit:contain;display:block}}
.brand-id .eye{{font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--azul-electrico);
  letter-spacing:.2em;text-transform:uppercase;display:block;margin-bottom:3px}}
.brand-id .nm{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:.95rem}}
.meta-block{{text-align:right;font-family:'JetBrains Mono',monospace;font-size:.68rem;
  color:var(--muted);letter-spacing:.13em;text-transform:uppercase;line-height:1.85}}
.meta-block strong{{color:var(--white);font-weight:500}}
.eyebrow{{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--azul-electrico);
  letter-spacing:.22em;text-transform:uppercase;margin-bottom:.7rem}}
h1{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:2.6rem;line-height:1.05;
  letter-spacing:-.025em;margin-bottom:2.5rem}}
h1 .accent{{color:var(--azul-electrico)}}
.carousel-block{{margin-bottom:3rem}}
.carousel-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:1.05rem;
  margin-bottom:1.2rem;color:var(--white);display:flex;align-items:baseline;gap:.8rem}}
.carousel-title .fwk{{font-family:'JetBrains Mono',monospace;font-size:.7rem;color:var(--azul-electrico);letter-spacing:.18em;text-transform:uppercase}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem;margin-bottom:1.5rem;
  background:var(--grafito);border:1px solid var(--grafito-2);border-radius:12px;padding:1.25rem}}
.cell{{position:relative;background:#000;border-radius:8px;overflow:hidden;max-width:280px;justify-self:center;width:100%}}
.cell img{{width:100%;display:block;background:#000}}
.cell.col9x16 img{{aspect-ratio:9/16;object-fit:cover}}
.cell.col1x1 img{{aspect-ratio:1/1;object-fit:cover}}
.badge{{position:absolute;top:.6rem;left:.6rem;background:var(--azul-brand);color:var(--white);
  font-family:'JetBrains Mono',monospace;font-size:.62rem;letter-spacing:.18em;text-transform:uppercase;
  padding:.3rem .55rem;border-radius:4px;font-weight:500}}
.badge.new{{background:transparent;border:1px solid var(--grafito-2);color:var(--muted)}}
.row-label{{grid-column:1/-1;font-family:'JetBrains Mono',monospace;font-size:.62rem;
  color:var(--muted);letter-spacing:.18em;text-transform:uppercase;margin-bottom:-.5rem}}
.cell.missing{{display:flex;align-items:center;justify-content:center;
  font-family:'JetBrains Mono',monospace;font-size:.7rem;color:var(--muted);letter-spacing:.18em;text-transform:uppercase;
  aspect-ratio:1/1;border:1px dashed var(--grafito-2);background:transparent}}
footer{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--grafito-2);
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;
  font-family:'JetBrains Mono',monospace;font-size:.62rem;color:var(--muted);letter-spacing:.18em;text-transform:uppercase}}
footer a{{color:var(--azul-electrico);text-decoration:none}}
@media (max-width:760px){{body{{padding:2rem 1.25rem}}h1{{font-size:1.7rem}}
  .header{{flex-direction:column}}.meta-block{{text-align:left}}
  .row{{grid-template-columns:1fr}}}}
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
<p class="eyebrow">Carousels - Phase 8 - picks 1:1 reformat</p>
<h1>{brand} - <span class="accent">{accent_label}</span></h1>"""

GI_FOOT = """<footer>
  <span>Genera Impacto - <a href="https://generarimpacto.com">generarimpacto.com</a> - hola@generarimpacto.com</span>
  <span>Internal - Brand v1.0 - {year}</span>
</footer></body></html>"""


def _consistency_carousel_html(c: dict, campaign_dir: Path) -> str:
    cn = c["carousel"]
    fwk = c["framework"]
    total = len(c["slides"])
    out = [
        f'<section class="carousel-block">',
        f'<div class="carousel-title">Carrusel #{cn:02d} <span class="fwk">{fwk} - {total} slides</span></div>',
    ]
    for s in c["slides"]:
        sn = s["slide"]
        p9 = slide_9x16_path(campaign_dir, cn, fwk, sn)
        p1 = slide_1x1_path(campaign_dir, cn, fwk, sn)
        cell9 = (
            f'<div class="cell col9x16"><img src="{p9.name}" loading="lazy" alt="">'
            f'<div class="badge">9:16 anchor</div></div>'
            if p9.exists()
            else '<div class="cell col9x16 missing">9:16 missing</div>'
        )
        cell1 = (
            f'<div class="cell col1x1"><img src="picks-1x1/{p1.name}" loading="lazy" alt="">'
            f'<div class="badge new">1:1 nuevo</div></div>'
            if p1.exists()
            else '<div class="cell col1x1 missing">1:1 pendiente</div>'
        )
        out.append(
            f'<div class="row"><div class="row-label">slide {sn}/{total} - {s.get("role","")}</div>'
            f'{cell9}{cell1}</div>'
        )
    out.append('</section>')
    return "".join(out)


def build_picks_consistency(copy_script: dict, campaign_dir: Path,
                            picked: set[int], out_path: Path):
    brand = copy_script.get("brand", "Brand")
    head = GI_HEAD.format(
        title=f"{brand} - Carousels picks consistency",
        brand=brand, date=time.strftime("%d - %m - %Y"),
        accent_label=f"{len(picked)} carrusel(es) elegidos.",
    )
    blocks = "\n".join(
        _consistency_carousel_html(c, campaign_dir)
        for c in copy_script["carousels"]
        if c["carousel"] in picked
    )
    foot = GI_FOOT.format(year=time.strftime("%Y"))
    # Inject auto-reload before </head> so the SAME tab refreshes on rebuilds.
    head = head.replace("</head>", AUTO_RELOAD_HEAD + "</head>", 1)
    out_path.write_text(head + blocks + foot, encoding="utf-8")
    write_gallery_version(out_path)


# ---------------------------------------------------------------------------
# Auto-open
# ---------------------------------------------------------------------------

# Auto-reload helpers (same pattern as generate_carousels.py — see that file for
# rationale). Inject AUTO_RELOAD_HEAD into HTML so the same tab refreshes on
# rebuilds; open_once_in_browser uses a marker file to avoid spawning new tabs.

AUTO_RELOAD_HEAD = """<meta http-equiv="refresh" content="15">
<script>
(async function() {
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


def write_gallery_version(html_path: Path):
    """Write a tiny .version file next to the gallery HTML for the auto-reload poller."""
    html_path.with_suffix(".version").write_text(str(time.time()), encoding="utf-8")


def open_once_in_browser(path: Path, force: bool = False):
    """Open path in browser ONLY if marker is missing or older than 4h.
    Subsequent rebuilds in the same session refresh the existing tab via
    the auto-reload script. Pass force=True (--reopen) to override."""
    marker = path.parent / f".{path.stem}.opened"
    if not force and marker.exists():
        try:
            if time.time() - marker.stat().st_mtime < 4 * 3600:
                _safe_print(
                    f"\n({path.name} ya está abierta — la tab existente se refresca sola "
                    f"(meta refresh 15s + JS polling 3s). Pasá --reopen para forzar nueva tab.)"
                )
                marker.touch()
                return
        except Exception:
            pass
    open_in_browser(path)
    marker.touch()


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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

REGEN_RE = re.compile(r"^(?P<c>\d+)\.(?P<s>\d+)$")


def parse_slide(arg: str) -> tuple[int, int]:
    m = REGEN_RE.match(arg.strip())
    if not m:
        sys.exit(f"ERROR: --slide '{arg}' must be N.M (e.g. '1.2')")
    return (int(m.group("c")), int(m.group("s")))


def main():
    p = argparse.ArgumentParser(description="Regenerate picked carousels in 1:1 (DROP-DON'T-CRAM)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--carousels", type=str, default=None,
                   help="Comma-separated carousel numbers picked by client (e.g. '1,2')")
    g.add_argument("--slide", type=str, default=None,
                   help="Single slide to regenerate (e.g. '1.2')")
    p.add_argument("--resolution", choices=["1K", "2K"], default=DEFAULT_RESOLUTION,
                   help="(1:1 doesn't support 4K)")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    p.add_argument("--no-open", action="store_true")
    p.add_argument("--reopen", action="store_true",
                   help="Force opening a new browser tab even if gallery already opened "
                        "in this session (default: open once, then auto-reload same tab)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--campaign-dir", type=str, default=".")
    p.add_argument("--brand-dir", type=str, default=None)
    args = p.parse_args()

    campaign_dir = Path(args.campaign_dir).resolve()
    brand_dir = Path(args.brand_dir).resolve() if args.brand_dir else campaign_dir.parent.parent

    copy_script_path = campaign_dir / "copy-script.json"
    if not copy_script_path.exists():
        sys.exit(f"ERROR: {copy_script_path} not found.")
    with open(copy_script_path, encoding="utf-8") as f:
        copy_script = json.load(f)

    brand_dna = {}
    bdp = brand_dir / "brand-dna.json"
    if bdp.exists():
        with open(bdp, encoding="utf-8") as f:
            brand_dna = json.load(f)

    asset_pack_vocab = None
    ap = brand_dir / "assets.json"
    if ap.exists():
        try:
            with open(ap, encoding="utf-8") as f:
                asset_pack_vocab = (json.load(f) or {}).get("prompt_vocabulary")
        except Exception:
            pass

    brand_slug = copy_script.get("brand_slug") or brand_dir.name
    brand_name = copy_script.get("brand", brand_slug)
    tone_override = copy_script.get("tone")
    product_filename = copy_script.get("product_image")

    brand_modifier = build_brand_modifier(brand_dna, asset_pack_vocab, tone_override)

    if args.slide:
        cn, sn = parse_slide(args.slide)
        picked = {cn}
        only_slide = (cn, sn)
    else:
        picked = {int(x.strip()) for x in args.carousels.split(",") if x.strip()}
        only_slide = None

    print(f"\n{'='*64}")
    print(f"  Carousel 1:1 Reformatter (kie.ai gpt-image-2) - {brand_name}")
    print(f"  Picks: carrusel(es) {sorted(picked)}" + (f" slide {only_slide[1]}" if only_slide else ""))
    print(f"  Resolution: {args.resolution} | Concurrency: {args.concurrency}")
    print(f"{'='*64}\n")

    (campaign_dir / "picks-1x1").mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        c0 = next((c for c in copy_script["carousels"] if c["carousel"] in picked), None)
        if c0:
            s0 = c0["slides"][0]
            sample = build_1x1_prompt(brand_modifier, c0, s0, len(c0["slides"]))
            print("DRY RUN — sample prompt for first picked slide:\n")
            print(sample[:2500])
            if len(sample) > 2500:
                print(f"\n... [{len(sample) - 2500} more chars]")
        return

    if not KIE_API_KEY:
        sys.exit("ERROR: KIE_API_KEY env var required.")
    if not PICKS_UPLOAD_TOKEN:
        sys.exit("ERROR: PICKS_UPLOAD_TOKEN env var required.")

    product_url, logo_url = upload_brand_refs(brand_dir / "product-images", brand_slug, product_filename)

    print("Uploading 9:16 slides as anchors for 1:1 reformat...")
    base_refs = [product_url] + ([logo_url] if logo_url else [])
    jobs = []
    for c in copy_script["carousels"]:
        cn = c["carousel"]
        if cn not in picked:
            continue
        for s in c["slides"]:
            sn = s["slide"]
            if only_slide is not None and (cn, sn) != only_slide:
                continue
            anchor_path = slide_9x16_path(campaign_dir, cn, c["framework"], sn)
            if not anchor_path.exists():
                _safe_print(f"  ! c{cn:02d} slide {sn}: 9:16 anchor missing at {anchor_path} — skipping")
                continue
            try:
                anchor_url = upload_to_blob(
                    brand_slug, anchor_path,
                    override_name=f"anchor-{copy_script.get('campaign_slug','c')}-c{cn:02d}-{c['framework'].lower()}-s{sn:02d}.png",
                )
                refs = base_refs + [anchor_url]
                prompt = build_1x1_prompt(brand_modifier, c, s, len(c["slides"]))
                save = slide_1x1_path(campaign_dir, cn, c["framework"], sn)
                label = f"[c{cn:02d} {c['framework']:5s} {sn}/{len(c['slides'])} {s.get('role','')[:9]}]"
                jobs.append((prompt, refs, save, label, args.resolution))
                print(f"  ok c{cn:02d} slide {sn} anchor uploaded")
            except Exception as e:
                _safe_print(f"  XX c{cn:02d} slide {sn}: anchor upload failed: {e}")

    if not jobs:
        print("\n(no slides to regenerate)")
        return

    print(f"\nRegenerating {len(jobs)} slide(s) at 1:1 in parallel (concurrency={args.concurrency})...")
    t_start = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = [ex.submit(_process_slide, *j) for j in jobs]
        for fut in as_completed(futures):
            results.append(fut.result())

    ok = sum(1 for r in results if r["ok"])
    fail = len(results) - ok
    elapsed = time.time() - t_start
    print(f"\n{'='*64}")
    print(f"  Done  |  OK: {ok}  |  FAIL: {fail}  |  Wall: {elapsed:.1f}s")
    print(f"  Output: {campaign_dir / 'picks-1x1'}/")
    print(f"{'='*64}\n")

    consistency_path = campaign_dir / "picks-consistency.html"
    build_picks_consistency(copy_script, campaign_dir, picked, consistency_path)

    if not args.no_open:
        open_once_in_browser(consistency_path, force=args.reopen)


if __name__ == "__main__":
    main()
