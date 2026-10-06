"""Muestra la energía de la voz cada 10 ms entre dos tiempos, para cortar EXACTO en silencio.

    python hueco.py reel1 33.4 38.2        # sobre pub/<marca>/reel1/vo.wav
    python hueco.py ruta/toma.wav 22.2 23.0

Cada valor es dB en la banda de voz; con * los cuadros por debajo del umbral de silencio.
Elegí el corte en el medio de una racha de * (mínimo 60 ms). Nunca cortes en un cuadro sin *.
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import ASSETS, TMP, run  # noqa: E402
from voz_comun import islas, leer  # noqa: E402

if len(sys.argv) < 4:
    raise SystemExit(__doc__)
arg, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
p = pathlib.Path(arg) if pathlib.Path(arg).exists() else ASSETS / arg / "vo.wav"
w = TMP / "hueco.wav"
run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-vn", "-ac", "1", "-ar", "16000", str(w)])
sr, x = leer(w)
_, thr, e = islas(x, sr)
seg = e[int(a * 100): int(b * 100)]
print(f"umbral de silencio {thr:.0f} dB · mínimo {seg.min():.0f} dB en {a + seg.argmin() / 100:.2f} s")
linea = []
for i, v in enumerate(seg):
    linea.append(f"{a + i / 100:.2f}:{v:.0f}{'*' if v <= thr else ''}")
    if len(linea) == 10:
        print("  ".join(linea)); linea = []
if linea:
    print("  ".join(linea))
