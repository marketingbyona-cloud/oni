"""Busca TRABADAS, REPETICIONES y frases a medio decir en una voz, transcribiendo isla por isla.

    python islas.py reel1                    # la voz armada: pub/<marca>/reel1/vo.wav
    python islas.py reel1 reel2 reel3        # varias
    python islas.py ruta/al/audio.m4a        # cualquier toma (también .MOV)
    python islas.py reel1 --palabras         # además, cada palabra con su tiempo

Por qué así: Whisper sobre la voz ENTERA fusiona los intentos ("los conseguís a 48... la mejor
parte es que los conseguís a 48.750") y la trabada no aparece. Cortando por islas de habla
(silencio real en la onda) y transcribiendo cada una SIN VAD, aparece todo lo que suena:
muletillas, "ok, dale", arranques fallidos, indicaciones del que filma.

Marcas:
  <<< ¿REPITE?   la isla empieza igual que la siguiente -> casi siempre hay que borrar la primera
  <<< ¿REPITE ADENTRO?  la misma secuencia de 3+ palabras dos veces dentro de la isla
  <<< ¿CORTADA?  la isla termina en "..." o en palabra cortada
Para borrar: hueco.py (dónde está el silencio exacto) + vo_cortar.py (corta y re-sincroniza).
Escribe ana/<nombre>/islas.json.
"""
import json, pathlib, sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import ANA, ASSETS, RAIZ, norm, run, whisper  # noqa: E402
from voz_comun import islas, leer  # noqa: E402


def fuente(arg):
    if (ASSETS / arg / "vo.wav").exists():  # nombre de reel -> su voz armada
        return ASSETS / arg / "vo.wav", arg
    for p in (pathlib.Path(arg), RAIZ / arg):
        if p.is_file():
            return p, p.stem
    raise SystemExit(f"no encuentro {arg}")


def repite_adentro(ws, n=3):
    ks = [norm(w) for w in ws if norm(w)]
    vistos = {}
    for i in range(len(ks) - n + 1):
        g = tuple(ks[i:i + n])
        if g in vistos and i - vistos[g] <= 14:
            return " ".join(g)
        vistos.setdefault(g, i)
    return None


def analizar(arg, con_palabras):
    src, nombre = fuente(arg)
    out = ANA / nombre
    out.mkdir(parents=True, exist_ok=True)
    wav = out / "isla_src.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    sr, x = leer(wav)
    isl, thr, _ = islas(x, sr)
    res = []
    for a, b in isl:
        a0, b0 = max(0, a - 0.05), min(len(x) / sr, b + 0.08)
        seg = x[int(a0 * sr): int(b0 * sr)]
        seg = (seg / max(1e-9, np.abs(seg).max()) * 0.9).astype(np.float32)
        segs, _ = whisper().transcribe(seg, language="es", vad_filter=False, condition_on_previous_text=False, word_timestamps=True)
        ws = [{"w": w.word.strip(), "t": round(a0 + w.start, 2), "e": round(a0 + w.end, 2)} for s in segs for w in s.words]
        res.append({"a": round(a, 2), "b": round(b, 2), "txt": " ".join(w["w"] for w in ws), "words": ws})
    wav.unlink(missing_ok=True)
    json.dump(res, open(out / "islas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n== {nombre}  ({src.name}, umbral {thr:.0f} dB, {len(res)} islas)")
    for i, r in enumerate(res):
        w = [norm(p) for p in r["txt"].split() if norm(p)]
        nx = [norm(p) for p in res[i + 1]["txt"].split() if norm(p)] if i + 1 < len(res) else []
        marcas = []
        if len(w) >= 2 and len(nx) >= 2 and (w[:2] == nx[:2] or (len(w) <= 6 and " ".join(w) in " ".join(nx))):
            marcas.append("¿REPITE?")
        rep = repite_adentro(r["txt"].split())
        if rep:
            marcas.append(f"¿REPITE ADENTRO? ({rep})")
        if r["txt"].rstrip().endswith(("...", "…", "-")):
            marcas.append("¿CORTADA?")
        print(f"{r['a']:7.2f}-{r['b']:7.2f}  {r['txt']}" + ("   <<< " + " ".join(marcas) if marcas else ""), flush=True)
        if con_palabras:
            print("            " + " ".join(f"{p['w']}[{p['t']:.2f}-{p['e']:.2f}]" for p in r["words"]))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    for a in args:
        analizar(a, "--palabras" in sys.argv)
