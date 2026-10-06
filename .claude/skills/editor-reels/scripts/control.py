"""Hojas de control visual. Tres modos:

    python control.py plan Mudra3 [paso=1.25]       # ANTES de renderizar: cuadros desde el bundle
    python control.py chk Mudra3:120,345 Mudra6:534  # cuadros puntuales (para verificar un arreglo)
    python control.py final ruta/video.mp4 [paso=0.5] [desde] [hasta]   # el MP4 terminado, con ffmpeg

Todas dibujan las guías de la safe zone de Instagram (verde): y = 250 px, y = 1500 px y la
columna de botones (x > 940 en la mitad de abajo), y el tiempo de cada cuadro.
Salidas en ana/control/: <comp>_N.jpg (8 x 2 por hoja), chk.jpg, <video>_N.jpg (9 x 3).

Cómo revisar (con Read sobre cada hoja):
  - ¿algún texto/placa/pastilla/precio toca el PRODUCTO o una CARA? -> cambiar zona/altura o la toma
  - ¿algo importante fuera de la safe zone?
  - ¿subtítulo que aparece un instante solo (resto de una frase) o tomas de 0.1 s?
  - ¿el gancho se lee y no tapa lo que se muestra?
  - Si una placa parece rozar algo, hacé zoom (recorte) antes de dar por buena la toma.
El modo "final" es el que manda: 1 cuadro cada 1.25 s NO alcanza (se escaparon placas sobre pies
en un plano entero caminando); sobre el video final usá 0.5 s.
"""
import json, pathlib, shutil, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import ANA, BUNDLE, REMOTION, PLANTILLA, FPS, clave_de, dur  # noqa: E402

OUT = ANA / "control"
OUT.mkdir(parents=True, exist_ok=True)
STILLS = pathlib.Path(__file__).parent / "stills.mjs"
try:
    F22 = ImageFont.truetype("arial.ttf", 22)
    F18 = ImageFont.truetype("arial.ttf", 18)
except OSError:
    F22 = F18 = ImageFont.load_default()


def guias(im):
    d = ImageDraw.Draw(im)
    W, H = im.size
    k = W / 1080
    d.line((0, 250 * k, W, 250 * k), fill=(0, 255, 0), width=max(1, int(6 * k)))
    d.line((0, 1500 * k, W, 1500 * k), fill=(0, 255, 0), width=max(1, int(6 * k)))
    d.line((940 * k, 1000 * k, 940 * k, H), fill=(0, 255, 0), width=max(1, int(6 * k)))
    return im


def cuadros(comp, frames):
    d = OUT / "_stills" / comp
    shutil.rmtree(d, ignore_errors=True)  # nunca reusar cuadros de un bundle viejo
    r = subprocess.run(["node", str(STILLS), str(REMOTION), str(BUNDLE), str(d), comp, *map(str, frames)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        print(r.stderr[-1500:])
        raise SystemExit("falló el render de cuadros (¿bundle armado? ¿id de composición?)")
    return d


def hoja(ims, labels, cols, W, H, salida):
    s = Image.new("RGB", (cols * (W + 4), ((len(ims) + cols - 1) // cols) * (H + 4)), "white")
    for i, (im, lab) in enumerate(zip(ims, labels)):
        im = guias(im.convert("RGB").resize((W, H)))
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 0, 9 * len(lab) + 8, 24), fill="black")
        dr.text((3, 1), lab, fill="yellow", font=F22)
        s.paste(im, ((i % cols) * (W + 4), (i // cols) * (H + 4)))
    s.save(salida, quality=84)
    return salida


def modo_plan(comp, paso=1.25):
    clave = clave_de(comp)
    txt = (PLANTILLA / "cfg" / f"{clave}.ts").read_text(encoding="utf-8")
    total = json.loads(txt[txt.index("= ") + 2: txt.rindex(";")])["total"]
    ts, t = [], 0.4
    while t < total - 0.2:
        ts.append(round(t, 2)); t += paso
    d = cuadros(comp, [round(x * FPS) for x in ts])
    ims = [Image.open(d / f"f{round(x * FPS):04d}.jpg") for x in ts]
    for n, i in enumerate(range(0, len(ims), 16)):
        print(hoja(ims[i:i + 16], [f"{x:.1f}" for x in ts[i:i + 16]], 8, 216, 384, OUT / f"{comp}_{n + 1}.jpg"))


def modo_chk(args):
    celdas = []
    for a in args:
        comp, frs = a.split(":")
        frs = [int(x) for x in frs.split(",")]
        d = cuadros(comp, frs)
        celdas += [(Image.open(d / f"f{fr:04d}.jpg"), f"{comp} {fr / FPS:.1f}") for fr in frs]
    print(hoja([c[0] for c in celdas], [c[1] for c in celdas], 8, 270, 480, OUT / "chk.jpg"))


def modo_final(video, paso=0.5, desde=0.0, hasta=None):
    video = pathlib.Path(video)
    hasta = hasta or dur(video)
    tmp = OUT / f"_f_{video.stem}"
    shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    for old in OUT.glob(f"{video.stem}_*.jpg"):
        old.unlink()
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(desde), "-to", str(hasta), "-i", str(video), "-vf", f"fps=1/{paso},scale=216:384", str(tmp / "f%04d.jpg")], check=True)
    fs = sorted(tmp.glob("f*.jpg"))
    ims = [Image.open(f) for f in fs]
    labs = [f"{desde + i * paso + paso / 2:.1f}" for i in range(len(fs))]
    for n, i in enumerate(range(0, len(ims), 27)):
        print(hoja(ims[i:i + 27], labs[i:i + 27], 9, 216, 384, OUT / f"{video.stem}_{n + 1}.jpg"))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    modo, args = sys.argv[1], sys.argv[2:]
    if modo == "plan":
        modo_plan(args[0], float(args[1]) if len(args) > 1 else 1.25)
    elif modo == "chk":
        modo_chk(args)
    elif modo == "final":
        modo_final(args[0], *(float(a) for a in args[1:]))
    else:
        raise SystemExit(__doc__)
