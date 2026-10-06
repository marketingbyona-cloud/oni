"""Saca tramos de la voz final (trabadas, repeticiones, frases que no van) y vuelve a sacar los tiempos.

    python vo_cortar.py reel1 33.75-37.80 [a-b ...]      (segundos de pub/<marca>/<reel>/vo.wav ORIGINAL)

- La primera vez guarda la voz original en ana/<reel>/vo_antes_corte.wav y SIEMPRE corta desde
  esa copia: podés volver a correrlo con otros tramos sin acumular cortes.
- Empalmes con fundido cruzado de 20 ms. Elegí a y b en silencio real (hueco.py).
- Conserva el formato del wav (int16): escribir enteros como float satura el audio y después
  Whisper entiende cualquier cosa ("ojos sátenes" por "zuecos Atenas").
- Reescribe ana/<reel>/vo_final.json (palabras nuevas; tramos corridos) -> después corré armar.py.
Después de cortar: revisá que ninguna toma del plan haya quedado de 0.1 s (las anclas se juntan).
"""
import json, pathlib, shutil, sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import ANA, ASSETS, run, whisper  # noqa: E402

if len(sys.argv) < 3:
    raise SystemExit(__doc__)
reel = sys.argv[1]
cortes = sorted(tuple(float(v) for v in a.split("-")) for a in sys.argv[2:])
ana = ANA / reel
out = ASSETS / reel / "vo.wav"
orig = ana / "vo_antes_corte.wav"
if not orig.exists():
    shutil.copy(out, orig)
meta_orig = ana / "vo_final_antes_corte.json"
if not meta_orig.exists():
    shutil.copy(ana / "vo_final.json", meta_orig)
SR, x = wavfile.read(orig)
tipo = x.dtype
x = x.astype(np.float64)
F = int(0.02 * SR)
partes, pos = [], 0
for a, b in cortes:
    partes.append(x[pos: int(a * SR)])
    pos = int(b * SR)
partes.append(x[pos:])
y = partes[0]
for p in partes[1:]:
    fade = np.linspace(1, 0, F)
    y = np.concatenate([y[:-F], y[-F:] * fade + p[:F] * (1 - fade), p[F:]])
wavfile.write(out, SR, np.clip(np.round(y), -32768, 32767).astype(np.int16) if tipo == np.int16 else y.astype(tipo))


def corrido(t):
    d = 0.0
    for a, b in cortes:
        if t >= b:
            d += b - a
        elif t > a:
            return a - d
    return t - d


tmp = ana / "w16.wav"
run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-ar", "16000", "-ac", "1", str(tmp)])
segs, _ = whisper().transcribe(str(tmp), language="es", word_timestamps=True, condition_on_previous_text=False)
ws = [{"w": w.word.strip(), "t": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
tmp.unlink()
z = y / (32768.0 if tipo == np.int16 else 1.0)
h = SR // 100; n = len(z) // h
e = 20 * np.log10(np.sqrt((z[: n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
thr = np.percentile(e, 90) - 28
for w in ws:
    ia, ib = int(w["t"] * 100), max(int(w["t"] * 100) + 1, int((w["e"] - 0.05) * 100))
    q = [k for k in range(ia, min(ib, n)) if e[k] < thr - 6]
    if q:
        w["t"] = round(next((k for k in range(q[-1], min(ib, n)) if e[k] > thr), q[-1]) / 100, 3)
M = json.load(open(meta_orig, encoding="utf-8"))
piezas = [{**p, "at": round(corrido(p["at"]), 3)} for p in M["pieces"]]
d = len(y) / SR
json.dump({"dur": round(d, 3), "pieces": piezas, "cuts": cortes, "words": ws}, open(ana / "vo_final.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(f"{reel}: {len(x) / SR:.2f} s -> {d:.2f} s (cortes {cortes})")
print(" ".join(f"{w['w']}@{w['t']:.2f}" for w in ws))
