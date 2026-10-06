"""Pasa tomas de celular (4K, 60-100 fps, HEVC, rotadas) a 1080x1920 60 fps H.264 sin audio.

    python convertir.py reel1 9693 9675 ...        # verticales (busca IMG_9693.MOV en reel1/ o en cualquier carpeta)
    python convertir.py reel1 9679:0.62            # horizontal: recorte 9:16 con el centro en x = 62 %
    python convertir.py reel6 --todas crudos/videos  # todas las tomas de una carpeta

Escribe pub/<marca>/<reel>/<número>.mp4. Si ya existe y se puede leer, no lo rehace.
- 60 fps a propósito: permite cámara lenta suave (rate 0.55-0.7) en las tomas de producto.
- ffmpeg endereza solo la rotación de los metadatos del celular.
- Si un proceso se corta a mitad, el .mp4 queda roto (ffprobe sin duración): este script lo
  detecta y lo rehace. Si armar.py dice "could not convert string to float", es eso.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import RAIZ, ASSETS, run, dur  # noqa: E402


def size(f):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height:stream_side_data=rotation", "-of", "json", str(f)])
    s = json.loads(r.stdout)["streams"][0]
    rot = next((d.get("rotation", 0) for d in s.get("side_data_list", []) or []), 0)
    w, h = s["width"], s["height"]
    return (h, w) if abs(rot) == 90 else (w, h)


def buscar(reel, nro):
    exts = (".mov", ".mp4")
    d = RAIZ / reel
    if d.is_dir():
        p = next((p for p in d.iterdir() if p.stem.endswith(nro) and p.suffix.lower() in exts), None)
        if p:
            return p
    return next((p for p in RAIZ.rglob("*") if p.stem.endswith(nro) and p.suffix.lower() in exts and "pub" not in p.parts), None)


def convertir(reel, arg):
    nro, _, cx = arg.partition(":")
    src = buscar(reel, nro)
    if src is None:
        print("NO ENCUENTRO", nro); return
    out = ASSETS / reel / f"{nro}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and dur(out) and not cx:
        print("ya", out.name); return
    w, h = size(src)
    if w > h:
        c = float(cx or 0.5)
        vf = f"scale=-2:1920:flags=lanczos,crop=1080:1920:'min(max(iw*{c}-540,0),iw-1080)':0,fps=60"
    else:
        vf = "scale=1080:1920:flags=lanczos,fps=60"
    r = run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-an", str(out)])
    print(("ok" if dur(out) else "FALLÓ"), out.name, f"{w}x{h}", r.stderr[-200:] if r.returncode else "")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    reel = sys.argv[1]
    if sys.argv[2] == "--todas":
        for p in sorted((RAIZ / sys.argv[3]).iterdir()):
            if p.suffix.lower() in (".mov", ".mp4"):
                convertir(reel, "".join(c for c in p.stem if c.isdigit())[-4:])
    else:
        for a in sys.argv[2:]:
            convertir(reel, a)
