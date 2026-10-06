#!/usr/bin/env python3
"""
upload_carousels.py — Phases 7 + 9: ship carousels to estrategia-ia.

Two modes:

  --phase preview
      Uploads the 9:16 carousel set so the client can pick at
      https://ia.generarimpacto.com/c/{brand}/{campaign}
      Reads copy-script.json + the on-disk 9:16 PNGs, builds a CarouselSet
      manifest, and POSTs to /api/upload/carousel-set + /api/upload/carousel-slide.

  --phase deliverables --carousels 1,2
      For carousels the client picked, walks both 9:16 PNGs (campaign root) and
      1:1 PNGs (picks-1x1/ subfolder), uploads as CarouselDeliverableAsset[],
      and POSTs the manifest to /api/upload/carousel-deliverable.
      Final URL: https://ia.generarimpacto.com/c/d/{brand}/{campaign}

Drive auto-upload (deliverables phase) — DEFAULT ON. Also pushes the same
files to Google Drive at:
  ADS|{cliente} / ESTRATEGIAS DE CONTENIDO / {NN} - {MES} / ESTRATEGIA IA / CARRUSELES /
Estructura: una subcarpeta por carrusel, con naming
  `{NN:02d} - {framework} - {product_focus}/`
y dentro los archivos `{format}_slide_{NN}.{ext}` (ej. `9x16_slide_01.png`).

To skip Drive (e.g. for local tests), pass `--no-drive`. Required for Drive:
  - `_drive_folder_id` set in `brand-dna.json` (cliente folder URL)
  - service account JSON at `$GOOGLE_APPLICATION_CREDENTIALS` or `~/.genera-impacto/drive-sa.json`

Required env:
    PICKS_UPLOAD_TOKEN   — bearer token for /api/upload/* endpoints

Usage:
    cd brands/{brand}/carousels/{campaign}
    python upload_carousels.py --phase preview \\
        --brand-slug cuchillosdecampo --brand-name "Cuchillos de Campo" \\
        --campaign-slug criollo-roseta-2026 --campaign-title "Criollo Roseta" \\
        --client-message "Elegí los carruseles que más resuenen con la marca."

    # After client picks, e.g. carousel 1:
    python upload_carousels.py --phase deliverables --carousels 1 \\
        --brand-slug cuchillosdecampo --brand-name "Cuchillos de Campo" \\
        --campaign-slug criollo-roseta-2026 --campaign-title "Criollo Roseta" \\
        # (Drive auto-upload corre por default; usá --no-drive para saltearlo)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests

BASE_URL = os.environ.get("ESTRATEGIA_IA_BASE_URL", "https://ia.generarimpacto.com").rstrip("/")
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


TOKEN = _load_env_credential("PICKS_UPLOAD_TOKEN")

MAX_UPLOAD_BYTES = 4_300_000  # Vercel multipart cap

# Filename pattern produced by generate_carousels.py + regenerate_carousels_1x1.py.
# Framework slug accepts hyphens because multi-word framework names (e.g.
# "Propuesta Comercial", "Before/After", "Us vs Them") slugify to
# "propuesta-comercial", "before-after", "us-vs-them" in those scripts.
# 9:16: 01-pas-9x16-01.png   /   01-propuesta-comercial-9x16-01.png
# 1:1:  01-pas-1x1-01.png    (under picks-1x1/)
SLIDE_RE = re.compile(
    r"^(?P<c>\d{1,3})-(?P<fwk>[a-z0-9-]+?)-(?P<fmt>9x16|1x1)-(?P<s>\d{1,3})\.(?:png|jpg|jpeg|webp)$",
    re.IGNORECASE,
)


def slug_framework(name: str) -> str:
    """Match the slug used by generate_carousels.py + regenerate_carousels_1x1.py
    so canonical filenames are consistent across the pipeline."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unknown"


def auth_headers() -> dict:
    if not TOKEN:
        sys.exit("ERROR: PICKS_UPLOAD_TOKEN env var not set")
    return {"Authorization": f"Bearer {TOKEN}"}


def maybe_compress_to_jpg(path: Path) -> Path:
    if path.suffix.lower() != ".png" or path.stat().st_size <= MAX_UPLOAD_BYTES:
        return path
    try:
        from PIL import Image
    except ImportError:
        print(f"  ! {path.name} is {path.stat().st_size / 1024 / 1024:.1f} MB > 4.3 MB but Pillow not installed.")
        return path
    jpg_path = path.with_suffix(".jpg")
    if not jpg_path.exists() or jpg_path.stat().st_mtime < path.stat().st_mtime:
        Image.open(path).convert("RGB").save(jpg_path, "JPEG", quality=92, optimize=True)
    return jpg_path


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_9x16(campaign_dir: Path) -> list[dict]:
    """Walk campaign_dir for 9:16 PNGs. Returns slide descriptors."""
    out: list[dict] = []
    for f in sorted(campaign_dir.iterdir()):
        if not f.is_file():
            continue
        m = SLIDE_RE.match(f.name)
        if not m or m.group("fmt").lower() != "9x16":
            continue
        out.append({
            "carousel": int(m.group("c")),
            "slide": int(m.group("s")),
            "framework": m.group("fwk").upper(),
            "format": "9x16",
            "filename": f.name,
            "source_path": f,
        })
    return out


def discover_1x1(campaign_dir: Path, picked: set[int]) -> list[dict]:
    """Walk picks-1x1/ for 1:1 PNGs of picked carousels. Returns slide descriptors."""
    folder = campaign_dir / "picks-1x1"
    if not folder.is_dir():
        return []
    out: list[dict] = []
    for f in sorted(folder.iterdir()):
        if not f.is_file():
            continue
        m = SLIDE_RE.match(f.name)
        if not m or m.group("fmt").lower() != "1x1":
            continue
        cn = int(m.group("c"))
        if cn not in picked:
            continue
        out.append({
            "carousel": cn,
            "slide": int(m.group("s")),
            "framework": m.group("fwk").upper(),
            "format": "1x1",
            "filename": f.name,
            "source_path": f,
        })
    return out


# ---------------------------------------------------------------------------
# Upload (one slide / asset)
# ---------------------------------------------------------------------------

def upload_one(endpoint: str, brand: str, campaign: str, slide: dict) -> dict | None:
    src: Path = slide["source_path"]
    upload_path = maybe_compress_to_jpg(src)
    canonical_name = (
        f"{slide['carousel']:02d}-{slug_framework(slide['framework'])}-"
        f"{slide['format']}-{slide['slide']:02d}{upload_path.suffix.lower()}"
    )
    mime = "image/jpeg" if upload_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"

    for attempt in range(3):
        try:
            with upload_path.open("rb") as fp:
                r = requests.post(
                    f"{BASE_URL}{endpoint}",
                    headers=auth_headers(),
                    files={"file": (canonical_name, fp, mime)},
                    data={"brand": brand, "campaign": campaign, "name": canonical_name},
                    timeout=180,
                )
            if r.status_code == 200:
                body = r.json()
                size_kb = upload_path.stat().st_size / 1024
                print(f"  ok [{slide['format']:>4}] {canonical_name} ({size_kb:.0f} KB)")
                return {
                    "carousel": slide["carousel"],
                    "slide": slide["slide"],
                    "framework": slide["framework"],
                    "format": slide["format"],
                    "filename": canonical_name,
                    "url": body["url"],
                    "bytes": upload_path.stat().st_size,
                }
            print(f"  ! upload {canonical_name} HTTP {r.status_code} attempt {attempt + 1}/3")
        except requests.RequestException as e:
            print(f"  ! upload {canonical_name} error attempt {attempt + 1}/3: {e}")
        time.sleep(2 * (attempt + 1))
    print(f"  XX giving up on {canonical_name}")
    return None


# ---------------------------------------------------------------------------
# Phase: preview
# ---------------------------------------------------------------------------

def phase_preview(args, copy_script: dict, campaign_dir: Path) -> str:
    slides_on_disk = discover_9x16(campaign_dir)
    if not slides_on_disk:
        sys.exit(f"ERROR: no 9:16 slides found in {campaign_dir}")

    by_carousel: dict[int, list[dict]] = {}
    for s in slides_on_disk:
        by_carousel.setdefault(s["carousel"], []).append(s)

    expected = {c["carousel"]: c for c in copy_script["carousels"]}
    print(f"\n→ Discovered {len(slides_on_disk)} 9:16 slide(s) across {len(by_carousel)} carousel(s).")
    for cn, slides in sorted(by_carousel.items()):
        if cn not in expected:
            print(f"  ! carousel {cn} on disk but not in copy-script.json — skipping")
            continue
        want = len(expected[cn]["slides"])
        have = len(slides)
        status = "ok" if want == have else f"WARN (want {want}, have {have})"
        print(f"  c{cn:02d} {expected[cn]['framework']:5s} — {have}/{want} slides — {status}")

    print(f"\n→ Uploading slides to {BASE_URL} ...")
    uploaded: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {
            ex.submit(upload_one, "/api/upload/carousel-slide", args.brand_slug, args.campaign_slug, s): s
            for s in slides_on_disk
        }
        for fut in as_completed(futs):
            res = fut.result()
            if res:
                uploaded.append(res)

    if not uploaded:
        sys.exit("ERROR: no slides uploaded successfully")

    by_key: dict[tuple[int, int], dict] = {(u["carousel"], u["slide"]): u for u in uploaded}

    carousels_out = []
    for c in copy_script["carousels"]:
        cn = c["carousel"]
        slides_out = []
        for s in c["slides"]:
            sn = s["slide"]
            up = by_key.get((cn, sn))
            if not up:
                continue
            slides_out.append({
                "carousel": cn,
                "slide": sn,
                "framework": c["framework"],
                "format": "9x16",
                "role": s.get("role", ""),
                "label": s.get("label", s.get("role", "")),
                "filename": up["filename"],
                "url": up["url"],
                "headline": s.get("headline", "")[:240] or None,
            })
        if not slides_out:
            continue
        carousels_out.append({
            "carousel": cn,
            "framework": c["framework"],
            "product": c.get("product"),
            "slide_count": len(slides_out),
            "slides": slides_out,
        })

    manifest = {
        "id": f"{args.brand_slug}/{args.campaign_slug}",
        "brand_slug": args.brand_slug,
        "brand_name": args.brand_name,
        "campaign_slug": args.campaign_slug,
        "campaign_title": args.campaign_title,
        "product_focus": copy_script.get("product_focus") or copy_script.get("campaign", ""),
        "tone": copy_script.get("tone"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "client_message": args.client_message or None,
        "recipient_label": args.recipient or None,
        "carousels": carousels_out,
    }

    print(f"\n→ Posting CarouselSet manifest...")
    r = requests.post(
        f"{BASE_URL}/api/upload/carousel-set",
        headers={**auth_headers(), "Content-Type": "application/json"},
        data=json.dumps(manifest),
        timeout=60,
    )
    if r.status_code != 200:
        sys.exit(f"ERROR: manifest upload failed (HTTP {r.status_code}): {r.text}")
    body = r.json()
    public_url = body["public_url"]

    Path("carousel-set-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nok DONE\n")
    print(f"  Public client link: {public_url}")
    print(f"  Manifest URL:       {body['manifest_url']}")
    print(f"  Local copy:         {Path('carousel-set-manifest.json').resolve()}\n")
    return public_url


# ---------------------------------------------------------------------------
# Phase: deliverables
# ---------------------------------------------------------------------------

def phase_deliverables(args, copy_script: dict, campaign_dir: Path) -> tuple[str, list[dict]]:
    if not args.carousels:
        sys.exit("ERROR: --carousels required for deliverables phase (e.g. --carousels 1,2)")
    picked = {int(x.strip()) for x in args.carousels.split(",") if x.strip()}

    slides_9x16 = [s for s in discover_9x16(campaign_dir) if s["carousel"] in picked]
    slides_1x1 = discover_1x1(campaign_dir, picked)
    all_slides = slides_9x16 + slides_1x1

    if not all_slides:
        sys.exit(f"ERROR: no slides found for picked carousel(s) {sorted(picked)}")

    counts: dict[str, int] = {}
    for s in all_slides:
        counts[s["format"]] = counts.get(s["format"], 0) + 1
    summary = " · ".join(f"{k}:{v}" for k, v in counts.items())
    print(f"\n→ Picked carousel(s): {sorted(picked)} | slides: {len(all_slides)} ({summary})")
    print(f"→ Uploading to {BASE_URL}/api/upload/carousel-deliverable-asset ...")

    uploaded: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {
            ex.submit(upload_one, "/api/upload/carousel-deliverable-asset",
                      args.brand_slug, args.campaign_slug, s): s
            for s in all_slides
        }
        for fut in as_completed(futs):
            res = fut.result()
            if res:
                uploaded.append(res)

    if not uploaded:
        sys.exit("ERROR: no slides uploaded successfully")

    fmt_rank = {"9x16": 0, "1x1": 1}
    uploaded.sort(key=lambda a: (a["carousel"], fmt_rank.get(a["format"], 9), a["slide"]))

    deliverable = {
        "id": f"{args.brand_slug}/{args.campaign_slug}",
        "brand_slug": args.brand_slug,
        "brand_name": args.brand_name,
        "campaign_slug": args.campaign_slug,
        "campaign_title": args.campaign_title,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "client_message": args.client_message or None,
        "assets": uploaded,
    }

    print(f"\n→ Posting CarouselDeliverable manifest ({len(uploaded)} assets)...")
    r = requests.post(
        f"{BASE_URL}/api/upload/carousel-deliverable",
        headers={**auth_headers(), "Content-Type": "application/json"},
        data=json.dumps(deliverable),
        timeout=60,
    )
    if r.status_code != 200:
        sys.exit(f"ERROR: deliverable manifest upload failed (HTTP {r.status_code}): {r.text}")
    body = r.json()
    public_url = body["public_url"]

    Path("carousel-deliverable-manifest.json").write_text(
        json.dumps(deliverable, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nok DONE\n")
    print(f"  Public client link: {public_url}")
    print(f"  Manifest URL:       {body['manifest_url']}")

    # Build local→remote path map for Drive uploader
    local_assets = []
    for s in all_slides:
        match = next(
            (u for u in uploaded if (u["carousel"], u["slide"], u["format"]) == (s["carousel"], s["slide"], s["format"])),
            None,
        )
        if match:
            local_assets.append({
                "carousel": s["carousel"],
                "slide": s["slide"],
                "framework": s["framework"],
                "format": s["format"],
                "source_path": s["source_path"],
                "filename": match["filename"],
            })
    return public_url, local_assets


# ---------------------------------------------------------------------------
# Drive push (deliverables only)
# ---------------------------------------------------------------------------

def push_to_drive(args, brand_dir: Path, copy_script: dict, assets: list[dict]) -> str | None:
    """Upload to Drive at ESTRATEGIA IA / CARRUSELES /
    Filename: carrusel_{framework}_{producto}_{formato}_slide_{NN}.png"""
    brand_dna_path = brand_dir / "brand-dna.json"
    if not brand_dna_path.exists():
        print(f"\n! Drive: brand-dna.json not found at {brand_dna_path}")
        return None
    try:
        dna = json.loads(brand_dna_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"\n! Drive: error reading brand-dna.json: {e}")
        return None

    folder_id = dna.get("_drive_folder_id") or dna.get("_drive_folder_url")
    if not folder_id:
        print("\n! Drive: brand-dna.json has no `_drive_folder_id`. Add the cliente folder URL there.")
        return None

    try:
        import importlib.util
        candidates = [
            Path(__file__).parent / "drive_uploader.py",
            brand_dir.parent / "drive_uploader.py",
        ]
        mod_path = next((p for p in candidates if p.exists()), None)
        if not mod_path:
            print("\n! Drive: drive_uploader.py not found in references/ or brand folder.")
            return None
        spec = importlib.util.spec_from_file_location("drive_uploader", mod_path)
        drive_uploader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(drive_uploader)  # type: ignore
    except Exception as e:
        print(f"\n! Drive: failed to import drive_uploader: {e}")
        return None

    try:
        service = drive_uploader.get_drive_service()
        cliente_id = drive_uploader.extract_folder_id(folder_id)

        print("\n→ Navigating Drive...")
        estrategias = drive_uploader.find_child_folder(service, cliente_id, "ESTRATEGIAS DE CONTENIDO")
        if not estrategias:
            print("! Drive: 'ESTRATEGIAS DE CONTENIDO' not found in cliente folder")
            return None
        print("    ok ESTRATEGIAS DE CONTENIDO")

        month_substring = (args.drive_month or drive_uploader.current_month_name_es()).upper()
        month_folder = drive_uploader.find_child_folder_by_substring(service, estrategias["id"], month_substring)
        if not month_folder:
            print(f"! Drive: no month folder containing '{month_substring}' under ESTRATEGIAS DE CONTENIDO")
            return None
        print(f"    ok {month_folder['name']}")

        estrategia_ia = drive_uploader.get_or_create_folder(service, month_folder["id"], "ESTRATEGIA IA", None)
        print("    ok ESTRATEGIA IA")
        carruseles = drive_uploader.get_or_create_folder(service, estrategia_ia["id"], "CARRUSELES", None)
        print("    ok CARRUSELES")
    except SystemExit as e:
        print(f"! Drive: {e}")
        return None
    except Exception as e:
        print(f"! Drive: navigation error: {e}")
        return None

    product_slug = drive_uploader.derive_product_slug(args.campaign_slug)
    # Display-friendly product name for subfolder labels (falls back to slug if missing)
    product_display = (copy_script.get("product_focus") or product_slug).strip().replace("/", "-")
    target_id = carruseles["id"]

    print(f"\n→ Uploading {len(assets)} files to CARRUSELES (subcarpeta por carrusel)...")
    ok = fail = 0
    # Cache: (carousel_num, framework) -> subfolder Drive ID. Avoids re-querying
    # Drive for the same subfolder when uploading multiple slides of one carousel.
    subfolder_cache: dict[tuple[int, str], tuple[str, str]] = {}

    for a in assets:
        src = Path(a["source_path"])
        if not src.exists():
            print(f"  ! local file missing: {src}")
            fail += 1
            continue

        cn = a["carousel"]
        fwk = a["framework"]
        sub_key = (cn, fwk)
        if sub_key not in subfolder_cache:
            folder_name = f"{cn:02d} - {fwk} - {product_display}".replace("/", "-")
            try:
                sub = drive_uploader.get_or_create_folder(service, target_id, folder_name, None)
                subfolder_cache[sub_key] = (sub["id"], folder_name)
                print(f"    + carpeta: {folder_name}")
            except Exception as e:
                print(f"    XX subcarpeta '{folder_name}': {e}")
                fail += 1
                continue

        parent_id, folder_name = subfolder_cache[sub_key]
        ext = src.suffix.lstrip(".") or "png"
        mime = "image/jpeg" if ext.lower() in ("jpg", "jpeg") else "image/png"
        fmt_safe = a["format"].replace(":", "x")
        name = f"{fmt_safe}_slide_{a['slide']:02d}.{ext}"
        try:
            drive_uploader.upload_or_update_file(service, parent_id, name, src, mime)
            print(f"    ok {folder_name}/{name}")
            ok += 1
        except Exception as e:
            print(f"    XX {folder_name}/{name}: {e}")
            fail += 1

    drive_url = f"https://drive.google.com/drive/folders/{target_id}"
    print(f"\n  Drive uploaded: {ok} | failed: {fail}")
    print(f"  CARRUSELES folder: {drive_url}")
    print(f"  Estructura: {len(subfolder_cache)} subcarpeta(s) por carrusel, cada una con sus 9:16 + 1:1")
    return drive_url


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description="Upload carousels to estrategia-ia.")
    p.add_argument("--phase", choices=["preview", "deliverables"], required=True)
    p.add_argument("--brand-slug", required=True)
    p.add_argument("--brand-name", required=True)
    p.add_argument("--campaign-slug", required=True)
    p.add_argument("--campaign-title", required=True)
    p.add_argument("--carousels", default=None, help="(deliverables) comma-separated picked carousel numbers, e.g. '1,2'")
    p.add_argument("--client-message", default="", help="Message shown above the gallery")
    p.add_argument("--recipient", default="", help="Optional admin-only recipient label")
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--no-open", action="store_true")
    p.add_argument("--no-drive", action="store_true",
                   help="(deliverables) skip Drive auto-upload. Default behavior pushes to "
                        "Google Drive at ESTRATEGIA IA/CARRUSELES. Use this only for local tests.")
    p.add_argument("--drive-month", default=None)
    p.add_argument("--campaign-dir", default=".", help="Campaign folder (default: cwd)")
    p.add_argument("--brand-dir", default=None, help="Brand folder (default: <campaign-dir>/../..)")
    args = p.parse_args()

    campaign_dir = Path(args.campaign_dir).resolve()
    brand_dir = Path(args.brand_dir).resolve() if args.brand_dir else campaign_dir.parent.parent

    copy_script_path = campaign_dir / "copy-script.json"
    if not copy_script_path.exists():
        sys.exit(f"ERROR: {copy_script_path} not found")
    with open(copy_script_path, encoding="utf-8") as f:
        copy_script = json.load(f)

    drive_url = None
    if args.phase == "preview":
        public_url = phase_preview(args, copy_script, campaign_dir)
    else:
        public_url, assets = phase_deliverables(args, copy_script, campaign_dir)
        # Drive auto-upload corre por default; --no-drive lo saltea (tests locales).
        if not args.no_drive:
            drive_url = push_to_drive(args, brand_dir, copy_script, assets)
        else:
            print("\n(Drive: skipped — --no-drive flag set)")

    print()
    if not args.no_open:
        try:
            os.system(f'cmd //c start {public_url}')
            if drive_url:
                os.system(f'cmd //c start {drive_url}')
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
