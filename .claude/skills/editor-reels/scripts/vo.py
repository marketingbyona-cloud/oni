"""Arma la voz en off de un reel con una o varias tomas de audio (.m4a/.mp3 o el audio de un .MOV).

    python vo.py reel1 Reel_1_mudra.m4a Reel_1_2.m4a "IMG_7900.MOV:0.2-4.4" ...

Cada argumento es un archivo de la carpeta del reel (o una ruta), con un tramo opcional desde-hasta (s).
El orden de los argumentos es el orden en que suenan (seguí el guion).

Lo que hace, y por qué:
  - Cada toma se nivela POR SEPARADO a -16 LUFS. Un gancho grabado con el micrófono de la cámara
    llegó a sonar 29 dB más bajo que la voz en off: "no arranca al principio".
  - Las pausas largas (> 0.7 s) se acortan midiendo SILENCIO REAL en la onda (islas de habla),
    dejando 0.30 s después y 0.25 s antes. Nunca se corta adentro de una frase: meter o sacar
    pausas a lo bruto "rompe el audio" y suena trabado.
  - Las tomas de cámara (.MOV) no se acortan: su imagen tiene que seguir sincronizada con la boca.
  - Puntas: 0.25 s antes de la primera isla y 0.35 s después de la última. Tomas unidas con 0.25 s.
  - Limpieza final suave (afftdn leve + compresor + limitador).
  - VERIFICA: transcribe el resultado y compara con las tomas originales; lista palabras que
    falten. Si falta algo, no sigas: revisá el corte.

Escribe pub/<marca>/<reel>/vo.wav y ana/<reel>/vo_final.json {dur, pieces:[{src,from,at,len,gain_db}], words}.
Después corré islas.py <reel> para buscar trabadas/repeticiones (Whisper sobre la voz entera las esconde).
"""
import difflib, json, pathlib, re, sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import RAIZ, ANA, ASSETS, norm, run, lufs, whisper  # noqa: E402
from voz_comun import islas  # noqa: E402

SR = 48000
LARGA, DESPUES, ANTES = 0.70, 0.30, 0.25


def palabras(x, carpeta):
    tmp = carpeta / "w16.wav"
    y = (x / max(1e-9, np.abs(x).max()) * 0.9).astype(np.float32)
    wavfile.write(carpeta / "w48.wav", SR, y)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(carpeta / "w48.wav"), "-ar", "16000", str(tmp)])
    segs, _ = whisper().transcribe(str(tmp), language="es", word_timestamps=True, condition_on_previous_text=False)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]


def lufs_arr(x, carpeta):
    p = carpeta / "lufs_tmp.wav"
    wavfile.write(p, SR, x.astype(np.float32))
    v = lufs(p)[0]
    p.unlink()
    return v


def main(reel, args):
    ana = ANA / reel
    ana.mkdir(parents=True, exist_ok=True)
    pieces, meta, ref = [], [], []
    t_out = 0.0
    for arg in args:
        m = re.match(r"^(.*?)(?::(\d+(?:\.\d+)?-\d+(?:\.\d+)?))?$", arg)  # "archivo:desde-hasta" (sirve con C:\...)
        name, rng = m.group(1), m.group(2)
        src = pathlib.Path(name) if pathlib.Path(name).is_absolute() else RAIZ / reel / name
        mov = src.suffix.lower() in (".mov", ".mp4")
        af = "highpass=f=90,afftdn=nr=14:nf=-38" if mov else "highpass=f=70"
        tmp = ana / "vo_tmp.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-af", af, "-c:a", "pcm_f32le", str(tmp)])
        x = wavfile.read(tmp)[1].astype(np.float64)
        a0 = 0.0
        if rng:
            a, b = (float(v) for v in rng.split("-"))
            x = x[int(a * SR): int(b * SR)]
            a0 = a
        ref += [w for w, _, _ in palabras(x, ana)]
        isl, _, _ = islas(x, SR)
        if not isl:
            print(f"  {src.name}: sin voz, salteada"); continue
        keep = np.zeros(len(x), bool)
        s0, s1 = max(0.0, isl[0][0] - ANTES), min(len(x) / SR, isl[-1][1] + 0.35)
        keep[int(s0 * SR): int(s1 * SR)] = True
        if not mov:
            for (_, b1), (a2, _) in zip(isl, isl[1:]):
                if a2 - b1 > LARGA:
                    keep[int((b1 + DESPUES) * SR): int((a2 - ANTES) * SR)] = False
        y = x[keep]
        a0 += s0
        g = -16 - lufs_arr(y, ana)
        y *= 10 ** (g / 20)
        f = int(0.012 * SR)
        y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
        pieces += [y, np.zeros(int(0.25 * SR))]
        meta.append({"src": src.name, "from": round(a0, 3), "at": round(t_out, 3), "len": round(len(y) / SR, 3), "gain_db": round(g, 1)})
        t_out += len(y) / SR + 0.25
        print(f"  {src.name}: {len(x) / SR:.1f}s -> {len(y) / SR:.1f}s, ganancia {g:+.1f} dB", flush=True)
    v = np.concatenate(pieces[:-1])
    raw = ana / "vo_raw.wav"
    wavfile.write(raw, SR, v.astype(np.float32))
    out = ASSETS / reel / "vo.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af", "afftdn=nr=6:nf=-45,acompressor=threshold=-20dB:ratio=2.2:attack=8:release=140,alimiter=limit=0.9:level=false", "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(out)])
    x = wavfile.read(out)[1].astype(np.float64) / 32768
    ws = [{"w": w, "t": round(a, 3), "e": round(b, 3)} for w, a, b in palabras(x, ana)]
    # Whisper adelanta los comienzos después de una pausa: se corren al arranque real de la energía
    h = SR // 100; n = len(x) // h
    e = 20 * np.log10(np.sqrt((x[: n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    thr = np.percentile(e, 90) - 28
    for w in ws:
        ia, ib = int(w["t"] * 100), max(int(w["t"] * 100) + 1, int((w["e"] - 0.05) * 100))
        q = [k for k in range(ia, min(ib, n)) if e[k] < thr - 6]
        if q:
            w["t"] = round(next((k for k in range(q[-1], min(ib, n)) if e[k] > thr), q[-1]) / 100, 3)
    d = len(x) / SR
    json.dump({"dur": round(d, 3), "pieces": meta, "words": ws}, open(ana / "vo_final.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    a = [norm(w) for w in ref if norm(w)]
    b = [norm(w["w"]) for w in ws if norm(w["w"])]
    falta = [" ".join(a[i1:i2]) for op, i1, i2, _, _ in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes() if op in ("delete", "replace")]
    print(f"voz {d:.2f} s · tomas {[(m['src'], m['len'], m['gain_db']) for m in meta]}")
    print("palabras que difieren de las tomas originales:", falta if falta else "ninguna")
    print(" ".join(f"{w['w']}@{w['t']:.2f}" for w in ws))
    for p in ["vo_tmp.wav", "w16.wav", "w48.wav"]:
        (ana / p).unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2:])
