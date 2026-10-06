"""Funciones de audio compartidas por los scripts de voz.

Idea central (aprendida a los golpes): los tiempos de Whisper NO sirven para cortar audio.
El final de palabra viene temprano (se come "pesos", "online"), con VAD se saltea muletillas
y a veces viene corrido medio segundo. Para cortar se usa la ONDA: "islas de habla" medidas
por energía en la banda de la voz; Whisper solo para saber QUÉ se dice.
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt

H_S = 0.01  # cuadros de 10 ms


def leer(p, sr_obj=None):
    sr, x = wavfile.read(p)
    x = x.astype(np.float64)
    if x.ndim > 1:
        x = x.mean(1)
    if np.abs(x).max() > 2:  # int16/int32 -> -1..1
        x /= 32768.0 if np.abs(x).max() < 40000 else 2147483648.0
    return sr, x


def escribir(p, sr, x, bits=16):
    x = np.clip(x, -1, 1)
    if bits == 16:
        wavfile.write(p, sr, (x * 32767).astype(np.int16))
    else:
        wavfile.write(p, sr, x.astype(np.float32))


def energia(x, sr, banda=(120, 4000)):
    """dB por cuadro de 10 ms en la banda de la voz."""
    y = sosfiltfilt(butter(4, list(banda), "band", fs=sr, output="sos"), x)
    h = int(sr * H_S)
    m = len(y) // h
    return 20 * np.log10(np.sqrt((y[: m * h].reshape(m, h) ** 2).mean(1)) + 1e-9)


def islas(x, sr, union=0.22, minimo=0.09):
    """Tramos con voz separados por silencio real. Umbral = max(piso + 12 dB, pico - 32 dB);
    une huecos < 220 ms (pausas dentro de la frase) y descarta ruiditos < 90 ms.
    Devuelve [(a, b)] en segundos, el umbral y la envolvente."""
    e = energia(x, sr)
    piso, pico = np.percentile(e, 10), np.percentile(e, 98)
    thr = max(piso + 12, pico - 32)
    on = e > thr
    segs, i, m = [], 0, len(e)
    while i < m:
        if on[i]:
            j = i
            while j < m and on[j]:
                j += 1
            segs.append([i, j]); i = j
        else:
            i += 1
    unidas = []
    for s in segs:
        if unidas and s[0] - unidas[-1][1] < union / H_S:
            unidas[-1][1] = s[1]
        else:
            unidas.append(s)
    return [(a * H_S, b * H_S) for a, b in unidas if (b - a) * H_S >= minimo], thr, e


def corte_seguro(e, thr, t, hacia=+1, limite=None, silencio=0.06):
    """Corre t (s) hacia adelante (+1) o atrás (-1) hasta encontrar `silencio` s de silencio real.
    Así un corte nunca cae en medio de una palabra."""
    w = int(silencio / H_S)
    i = int(t / H_S)
    while 0 < i < len(e) - w:
        tramo = e[i:i + w] if hacia > 0 else e[i - w:i]
        if (tramo <= thr).all():
            break
        if limite is not None and (i * H_S - limite) * hacia >= 0:
            break
        i += hacia
    return i * H_S


def nivel_por_isla(x, sr, isl, rango=(-4, 9)):
    """Lleva cada isla al nivel mediano (frases dichas lejos del micrófono quedaban 8-10 dB abajo
    y se perdían bajo la música). Ganancia constante por isla, rampas de 60 ms en los silencios."""
    vb = sosfiltfilt(butter(4, [150, 4000], "band", fs=sr, output="sos"), x)
    h = int(0.02 * sr)
    niv = []
    for a, b in isl:
        seg = vb[int(a * sr): int(b * sr)]
        if len(seg) < 3 * h:
            niv.append(None); continue
        fr = 20 * np.log10(np.sqrt((seg[: len(seg) // h * h].reshape(-1, h) ** 2).mean(1)) + 1e-12)
        niv.append(np.percentile(fr, 80))
    ok = [v for v in niv if v is not None]
    if not ok:
        return x, []
    obj = np.median(ok)
    t = np.arange(len(x)) / sr
    xs, ys, cambios = [0.0], [1.0], []
    for (a, b), v in zip(isl, niv):
        gd = 0.0 if v is None else float(np.clip(obj - v, *rango))
        g = 10 ** (gd / 20)
        xs += [max(xs[-1] + 1e-3, a - 0.06), a, b, b + 0.06]
        ys += [ys[-1], g, g, g]
        if abs(gd) >= 3:
            cambios.append((round(a, 2), round(gd, 1)))
    xs.append(t[-1] + 1); ys.append(ys[-1])
    return x * np.interp(t, xs, ys), cambios


def compuerta(x, sr, rango=45, pre=0.08, post=0.3, atenua_db=-10):
    """Baja el ambiente ENTRE frases (no lo mata: -10 dB; a -20 suena a corte)."""
    h = int(0.01 * sr)
    m = len(x) // h
    e = 20 * np.log10(np.sqrt((x[: m * h].reshape(m, h) ** 2).mean(1)) + 1e-12)
    on = e > np.percentile(e, 95) - rango
    g = np.zeros(m)
    for i in np.where(on)[0]:
        g[max(0, i - int(pre / 0.01)): i + int(post / 0.01) + 1] = 1
    att = 10 ** (atenua_db / 20)
    g = np.convolve(att + (1 - att) * g, np.ones(5) / 5, mode="same")
    gs = np.repeat(g, h)
    gs = np.concatenate([gs, np.full(len(x) - len(gs), gs[-1])])
    return x * gs
