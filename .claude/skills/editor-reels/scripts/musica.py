"""Música propia para los reels (sintetizada: sin derechos de terceros), una base distinta por video.

    python musica.py <timeline.json> <estilo> <salida.wav>
    python musica.py --estilos                       # lista los estilos

timeline.json (lo escribe armar.py): {"total": s, "voz": [[a, b], ...], "hits": [s, ...], "end": s}

Lo que Agus pidió (y por qué está así):
  - "Música más movida, nada de lo-fi ni R&B lento": 116-124 BPM, bombo en negras, bajo con
    bombeo (sidechain), acordes que respiran, hats con dinámica, fill cada 8 compases, subida +
    golpe en los cambios (hits: fin del gancho, precios, la tienda), filtro que se abre en el gancho.
  - "Variá la música, diferentes": en una tanda, cada video con un estilo distinto.
  - "Arranca saturado": era un BUG. El filtro del gancho se aplicaba por bloques sin pasar el
    estado del filtro de un bloque al siguiente (chisporroteo de ~21 Hz). Acá todos los filtros
    por bloques pasan `zi` (estado). Y se normaliza ANTES de la saturación suave.
  - "Habla y no se escucha": debajo de la voz la base baja 10 dB y además se le saca la banda
    de 1-4 kHz (donde se entienden las palabras). El nivel se mide en las partes SIN voz (-16 LUFS).
  - Sin marimba ni palmas de ruido filtrado: sonaban a voces de fondo.
"""
import sys, json, wave, subprocess, pathlib
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt

SR = 48000
rng = np.random.default_rng(31)


def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, a, b, o=3): return sosfilt(butter(o, [a, b], "band", fs=SR, output="sos"), x)
def midi(n): return 440 * 2 ** ((n - 69) / 12)
def tt(d): return np.arange(int(d * SR)) / SR


def _barrido(x, fcs, tipo, orden=2, B=256):
    """Filtro que cambia de frecuencia en el tiempo, CON estado entre bloques (sin chisporroteo)."""
    out = np.zeros(len(x))
    zi = None
    for i in range(0, len(x), B):
        sos = butter(orden, fcs(i / len(x)), tipo, fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + B], zi = sosfilt(sos, x[i:i + B], zi=zi)
    return out


def whoosh(dur=0.45, up=True):
    n = int(dur * SR)
    x = hp(rng.standard_normal(n), 300)
    out = _barrido(x, lambda r: min(600 * (12 ** (r if up else 1 - r)), 20000), "low")
    return out * np.sin(np.pi * np.arange(n) / n) ** 2


def riser(dur):
    n = int(dur * SR)
    out = _barrido(rng.standard_normal(n), lambda r: 500 * (16 ** r), "high")
    t = np.arange(n) / SR
    return (out * 0.5 + 0.4 * np.sin(2 * np.pi * np.cumsum(200 * 4 ** (t / dur)) / SR)) * (t / dur) ** 2


if sys.argv[1:2] == ["--estilos"]:
    ESTILOS_SOLO = True
elif len(sys.argv) < 4:
    raise SystemExit(__doc__)
else:
    ESTILOS_SOLO = False
if not ESTILOS_SOLO:
    TLP, style, OUTWAV = pathlib.Path(sys.argv[1]), sys.argv[2], pathlib.Path(sys.argv[3])
    reel = TLP.stem
    TL = json.load(open(TLP))
    DUR = TL["total"]
    N = int(DUR * SR)


def put(buf, t, s, g=1.0):
    i = int(t * SR)
    if i < 0:
        s = s[-i:]; i = 0
    if i >= len(buf):
        return
    n = min(len(s), len(buf) - i)
    buf[i:i + n] += g * s[:n]


def saw(f0, t, det=0.0):
    return 2 * ((f0 * (1 + det) * t) % 1) - 1


def supersaw(m, d, cut=3000, v=1.0):
    t = tt(d); f0 = midi(m)
    x = sum(saw(f0, t, dd) for dd in (-0.012, -0.005, 0, 0.005, 0.012)) / 5
    env = np.minimum(1, t / 0.01) * np.exp(-t / max(0.08, d * 0.6))
    return lp(x, cut) * env * v


def stab(notes, d=0.18, cut=3200):
    out = sum(supersaw(m, d, cut) for m in notes) / len(notes)
    return out


def pluck(m, d=0.25, cut=4200):
    t = tt(d); f0 = midi(m)
    x = 0.6 * saw(f0, t) + 0.4 * np.sign(np.sin(2 * np.pi * f0 * t)) * 0.5
    return lp(x, cut) * np.exp(-t / 0.09)


def keys_chord(notes, d):
    t = tt(d); out = np.zeros(len(t))
    for m in notes:
        f0 = midi(m)
        out += np.sin(2 * np.pi * f0 * t + 0.8 * np.sin(2 * np.pi * 2 * f0 * t) * np.exp(-t / 0.3))
    return lp(out / len(notes), 3500) * np.minimum(1, t / 0.005) * np.exp(-t / 0.5)


def pad(notes, d):
    t = tt(d); out = np.zeros(len(t))
    for m in notes:
        out += sum(saw(midi(m), t, dd) for dd in (-0.006, 0.006)) / 2
    env = np.minimum(1, t / 0.25) * np.clip((d - t) / 0.3, 0, 1)
    return lp(out / len(notes), 1800) * env


def bass(m, d, kind="sub"):
    t = tt(d); f0 = midi(m)
    if kind == "saw":
        x = lp(saw(f0, t) * 0.7 + np.sin(2 * np.pi * f0 * t), 650)
    elif kind == "log":  # bajo tipo "log drum": golpe con caída de afinación
        x = np.sin(2 * np.pi * f0 * (1 + 0.6 * np.exp(-t / 0.03)) * t) * np.exp(-t / 0.22)
        return lp(x, 900) * np.minimum(1, t / 0.003)
    else:
        x = np.sin(2 * np.pi * f0 * t) + 0.25 * np.sin(4 * np.pi * f0 * t)
    return x * np.minimum(1, t / 0.004) * np.minimum(1, np.clip((d - t) / 0.02, 0, 1))


def kick():
    t = tt(0.3)
    body = np.sin(2 * np.pi * (48 + 120 * np.exp(-t / 0.022)) * t) * np.exp(-t / 0.16)
    click = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.003) * 0.3
    return np.tanh(2.2 * body + click)


def snare():
    t = tt(0.22)
    tone = 0.6 * np.sin(2 * np.pi * 200 * t) * np.exp(-t / 0.05) + 0.3 * np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.03)
    noise = bp(rng.standard_normal(len(t)), 1800, 7000) * np.exp(-t / 0.07) * 0.55
    return lp(tone + noise, 8000)


def hat(open_=False):
    t = tt(0.22 if open_ else 0.04)
    return hp(rng.standard_normal(len(t)), 8000) * np.exp(-t / (0.07 if open_ else 0.011))


def shaker():
    t = tt(0.07)
    return hp(rng.standard_normal(len(t)), 6000) * np.sin(np.pi * np.clip(t / 0.07, 0, 1)) ** 2


def tom(f0):
    t = tt(0.25)
    return np.sin(2 * np.pi * f0 * (1 + 0.5 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.12)


def rim():
    t = tt(0.06)
    return bp(rng.standard_normal(len(t)), 1800, 5500) * np.exp(-t / 0.012) * 0.6 + np.sin(2 * np.pi * 1000 * t) * np.exp(-t / 0.006) * 0.4


def impact():
    t = tt(1.2)
    return np.tanh(1.5 * np.sin(2 * np.pi * (38 + 70 * np.exp(-t / 0.04)) * t) * np.exp(-t / 0.35)) + 0.25 * lp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.25)


# (bpm, acordes [(notas, raíz)], bajo, instrumento armónico, tipo de batería)
PROG = {
    "Am": [([57, 60, 64, 67], 45), ([53, 57, 60, 64], 41), ([55, 59, 62, 67], 43), ([52, 55, 59, 64], 40)],
    "Dm": [([62, 65, 69, 72], 38), ([58, 62, 65, 69], 34), ([60, 64, 67, 70], 36), ([57, 60, 64, 67], 33)],
    "F": [([65, 69, 72, 76], 41), ([62, 65, 69, 72], 38), ([60, 64, 67, 72], 36), ([58, 62, 65, 69], 34)],
    "Em": [([64, 67, 71, 74], 40), ([60, 64, 67, 71], 36), ([62, 66, 69, 72], 38), ([59, 62, 66, 69], 35)],
    "Gm": [([67, 70, 74, 77], 43), ([63, 67, 70, 74], 39), ([65, 69, 72, 75], 41), ([62, 65, 69, 72], 38)],
    "C": [([64, 67, 72, 76], 36), ([62, 67, 71, 74], 43), ([64, 69, 72, 76], 45), ([65, 69, 72, 77], 41)],
    "Bm": [([62, 66, 71, 74], 35), ([62, 67, 71, 74], 43), ([62, 66, 69, 74], 38), ([61, 64, 69, 73], 45)],
}
STYLES = {
    "nudisco": (120, "F", "octave", "stab", "disco"),
    "popdance": (118, "Am", "sub", "pluck", "pop"),
    "deep": (122, "Dm", "saw", "keys", "house"),
    "funky": (116, "Em", "slap", "pluck", "disco"),
    "techhouse": (124, "Gm", "rolling", "stab", "tech"),
    "afro": (120, "Am", "log", "keys", "afro"),
    "electropop": (124, "C", "sub", "supersaw", "pop"),
    "latin": (122, "Bm", "tumbao", "montuno", "latin"),
    "progressive": (121, "Dm", "rolling", "supersaw", "house"),
}
if ESTILOS_SOLO:
    for k, v in STYLES.items():
        print(f"{k:12s} {v[0]} BPM · tono {v[1]} · bajo {v[2]} · {v[3]} · batería {v[4]}")
    sys.exit()
if style not in STYLES:
    raise SystemExit(f"estilo '{style}' no existe: {', '.join(STYLES)}")
bpm, prog, btype, harm, drum = STYLES[style]
CH = PROG[prog]
BEAT = 60 / bpm
BAR = 4 * BEAT
S16 = BEAT / 4

harmony = np.zeros(N); low = np.zeros(N); drums = np.zeros(N); perc = np.zeros(N)
nbars = int(np.ceil(DUR / BAR)) + 1
hits = TL.get("hits", [])
first_hit = hits[0] if hits else 2 * BAR
for b in range(nbars):
    t0 = b * BAR
    notes, root = CH[(b // 2) % 4] if style in ("deep", "afro") else CH[b % 4]
    sec = b % 8
    full = t0 >= first_hit - 0.05 or t0 >= 2 * BAR  # el primer tramo (hook) va más liviano
    # armonía
    if harm == "stab":
        for k in ([0.5, 1.5, 2.5, 3.5] if drum == "disco" else [0, 0.75, 1.5, 2.5, 3.25]):
            put(harmony, t0 + k * BEAT, stab(notes, 0.16), 0.3)
        put(harmony, t0, pad(notes, BAR), 0.14)
    elif harm == "pluck":
        pattern = [0, 2, 1, 3, 2, 0, 3, 1]
        for k in range(16):
            if k % 2 == 0 or b % 2:
                put(harmony, t0 + k * S16, pluck(notes[pattern[k % 8] % len(notes)] + 12), 0.2)
        put(harmony, t0, pad(notes, BAR), 0.18)
    elif harm == "supersaw":  # acordes en contratiempo, brillantes
        for k in [0.5, 1.5, 2.5, 3.5]:
            put(harmony, t0 + k * BEAT, stab(notes, 0.3, 5200), 0.26)
        put(harmony, t0, pad(notes, BAR), 0.2)
        if b % 2:
            for k, m in zip([0, 0.75, 1.5, 2.5, 3], [0, 2, 1, 3, 2]):
                put(harmony, t0 + k * BEAT, pluck(notes[m] + 12, 0.2, 5000), 0.16)
    elif harm == "montuno":  # piano sincopado
        for k in [0, 0.75, 1.5, 2.25, 2.75, 3.5]:
            put(harmony, t0 + k * BEAT, keys_chord(notes, BEAT * 0.5), 0.26)
        put(harmony, t0, pad(notes, BAR), 0.08)
    else:  # keys
        for k in ([0, 1.5, 2.5] if drum != "afro" else [0, 0.75, 2, 2.75]):
            put(harmony, t0 + k * BEAT, keys_chord(notes, BEAT * 1.2), 0.32)
        put(harmony, t0, pad(notes, BAR), 0.12)
    # bajo
    for k in range(16):
        tk = t0 + k * S16
        if btype == "octave" and k % 2 == 0:
            put(low, tk, bass(root - 12 + (12 if k % 4 == 2 else 0), S16 * 1.6, "saw"), 0.42)
        elif btype == "sub" and k in (2, 6, 10, 14):
            put(low, tk, bass(root - 12, BEAT * 0.45), 0.6)
        elif btype == "saw" and k in (2, 5, 6, 10, 13, 14):
            put(low, tk, bass(root - 12, S16 * 1.4, "saw"), 0.5)
        elif btype == "slap" and k in (0, 3, 6, 8, 10, 11, 14):
            put(low, tk, bass(root - 12 + (12 if k in (3, 11) else 0), S16 * 1.2, "saw"), 0.45)
        elif btype == "rolling" and k % 4 != 0:
            put(low, tk, bass(root - 12, S16 * 0.9, "saw"), 0.42)
        elif btype == "tumbao" and k in (3, 6, 11, 14):
            put(low, tk, bass(root - 12 + (7 if k in (6, 14) else 0), BEAT * 0.6), 0.55)
        elif btype == "log" and k in (3, 6, 11, 14):
            put(low, tk, bass(root - 12 + (7 if k == 11 else 0), BEAT, "log"), 0.55)
    # batería
    for k in range(4):
        tb = t0 + k * BEAT
        if full or k in (0, 2):
            put(drums, tb, kick(), 0.95)
        if not full:
            continue
        if drum in ("pop",) and k in (1, 3):
            put(drums, tb, snare(), 0.42)
        if drum in ("disco", "house", "tech") and k in (1, 3):
            put(drums, tb, snare() if drum == "disco" else rim(), 0.32 if drum == "disco" else 0.28)
        put(drums, tb + BEAT / 2, hat(open_=drum in ("disco", "house", "tech")), 0.16)
        for s in range(4):
            vel = [0.07, 0.04, 0.1, 0.05][s]
            if sec >= 4 or drum in ("tech", "disco"):
                put(perc, tb + s * S16, hat(), vel * 1.4)
        if drum == "afro":
            for s, f0 in [(1, 180), (3, 140)]:
                put(perc, tb + s * S16, tom(f0), 0.16)
            put(perc, tb + 2 * S16, shaker(), 0.1)
        if drum == "latin":
            for s, f0, g in [(1, 230, 0.12), (3, 230, 0.16), (2, 165, 0.1)]:
                put(perc, tb + s * S16, tom(f0), g)
            put(perc, tb + S16 * 2, shaker(), 0.09)
            # clave 3-2 (en semicorcheas de dos compases)
            pos = (b % 2) * 16 + k * 4
            for c in (0, 6, 12, 20, 24):
                if pos <= c < pos + 4:
                    put(perc, t0 + (c % 16) * S16, rim(), 0.22)
        if drum == "pop" and sec >= 4:
            put(perc, tb + 3 * S16, shaker(), 0.1)
    # fill cada 8 compases
    if sec == 7 and full:
        for s in range(8, 16):
            put(perc, t0 + s * S16, tom(220 - s * 6) if drum != "tech" else snare(), 0.12 + 0.01 * s)

# bombeo (sidechain): armonía y bajo respiran con cada negra
t = np.arange(N) / SR
ph = (t % BEAT) / BEAT
pump = 0.35 + 0.65 * np.clip(ph / 0.35, 0, 1) ** 1.5
harmony *= pump
low *= 0.5 + 0.5 * np.clip(ph / 0.25, 0, 1)

mus = harmony + low + drums + perc
# intro: filtro que se abre durante el gancho (hasta el primer cambio)
k = int(min(first_hit, DUR) * SR)
if k > SR // 2:
    seg = mus[:k].copy()
    out = np.zeros_like(seg)
    B = 256
    zi = np.zeros((1, 2))
    for i in range(0, k, B):
        fc = 700 * (14 ** (i / k))
        out[i:i + B], zi = sosfilt(butter(2, min(fc, 18000), "low", fs=SR, output="sos"), seg[i:i + B], zi=zi)
    mus[:k] = out
# sin saturar: se normaliza ANTES de la curva suave (antes entraba con picos > 1)
mus = mus / (np.abs(mus).max() + 1e-9) * 0.9
mus = np.tanh(mus * 1.05) / np.tanh(1.05)

# voz: la base baja 10 dB mientras habla y además se le saca la banda de 1-4 kHz
env = np.zeros(N)
for a, b in TL["voz"]:
    env[int(max(0, a - 0.08) * SR): int((b + 0.15) * SR)] = 1
w = int(0.12 * SR)
env = np.convolve(env, np.ones(w) / w, mode="same")
banda = sosfiltfilt(butter(2, [1000, 4000], "band", fs=SR, output="sos"), mus)
mus = (mus - 0.5 * env * banda) * 10 ** (-10 * env / 20)

fx = np.zeros(N)
for h in hits:
    put(fx, h - 1.6, riser(1.6), 0.16)
    put(fx, h, impact(), 0.3)
put(fx, TL["end"] - 0.3, whoosh(0.4), 0.18)
put(fx, TL["end"], impact(), 0.18)

mix = mus + fx
fo = int(min(1.8, DUR / 5) * SR)
mix[-fo:] *= np.linspace(1, 0, fo) ** 1.3
mix /= np.max(np.abs(mix)) / 0.8
tmp = TLP.with_name(f"{reel}_musica_raw.wav")
y = (np.clip(np.stack([mix, mix], 1), -1, 1) * 32767).astype(np.int16)
with wave.open(str(tmp), "wb") as wv:
    wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(y.tobytes())


def _lufs(p):
    m = subprocess.run(["ffmpeg", "-i", str(p), "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(json.loads(m[m.rindex("{"): m.rindex("}") + 1])["input_i"])


# nivel: medido en las partes SIN voz y llevado a -16 LUFS (bajo la voz queda ~13 dB abajo);
# sin voz en todo el video (extras con texto), -15 LUFS
libre = env < 0.05
if TL["voz"] and libre.sum() > SR * 2:
    tmp2 = TLP.with_name(f"{reel}_musica_libre.wav")
    y2 = (np.clip(np.stack([mix[libre], mix[libre]], 1), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(tmp2), "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(y2.tobytes())
    g = -16 - _lufs(tmp2)
    tmp2.unlink()
else:
    g = (-22 if TL["voz"] else -15) - _lufs(tmp)
OUTWAV.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", f"volume={g:.2f}dB,alimiter=limit=0.85:attack=2:release=50:level=false", str(OUTWAV)], check=True)
tmp.unlink(missing_ok=True)
print(f"música {reel} ({style}, {bpm} BPM): {DUR:.1f}s")
