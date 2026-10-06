"""Limpia una toma con voz grabada con el celular (a cámara, testimonio, gancho hablado).

    python limpiar_voz.py <entrada .MOV/.m4a/.wav> <salida.wav> [desde hasta]

Cadena (la de los reels que quedaron bien):
  1. reducción de ruido espectral con el perfil de los silencios REALES de la toma (noisereduce)
  2. compuerta suave entre frases (-10 dB; a -20 suena a corte)
  3. nivel por isla de habla (-4 a +9 dB): frases dichas lejos del micrófono no se pierden
  4. EQ (corte 90 Hz, -2 dB en 250 Hz, +2.5 dB en 3.5 kHz) + nivelador dinámico suave
  5. compresor y nivel final -15 LUFS medido en el tramo que se usa (desde-hasta), limitador

Si la toma se usa sincronizada con la imagen, NO le cambies la duración: esto no corta nada.
"""
import pathlib, sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import TMP, run, lufs  # noqa: E402
from voz_comun import compuerta, islas, nivel_por_isla  # noqa: E402

SR = 48000
if len(sys.argv) < 3:
    raise SystemExit(__doc__)
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
a = float(sys.argv[3]) if len(sys.argv) > 3 else None
b = float(sys.argv[4]) if len(sys.argv) > 4 else None
raw = TMP / f"{src.stem}_48k.wav"
run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_f32le", str(raw)])
x = wavfile.read(raw)[1].astype(np.float64)
import noisereduce as nr  # noqa: E402
h = int(0.02 * SR)
m = len(x) // h
e = 20 * np.log10(np.sqrt((x[: m * h].reshape(m, h) ** 2).mean(1)) + 1e-12)
quietos = np.where(e < np.percentile(e, 12))[0]
ruido = np.concatenate([x[i * h:(i + 1) * h] for i in quietos]) if len(quietos) > 10 else x[: int(0.3 * SR)]
y = nr.reduce_noise(y=x, sr=SR, y_noise=ruido, stationary=True, prop_decrease=0.85, n_std_thresh_stationary=1.5, freq_mask_smooth_hz=300, time_mask_smooth_ms=40, n_fft=2048)
y = compuerta(y, SR)
isl, _, _ = islas(y, SR)
y, cambios = nivel_por_isla(y, SR, isl)
if cambios:
    print("nivel por isla (s, dB):", cambios)
den = TMP / f"{src.stem}_den.wav"
wavfile.write(den, SR, y.astype(np.float32))
eq = TMP / f"{src.stem}_eq.wav"
run(["ffmpeg", "-v", "error", "-y", "-i", str(den), "-af", "highpass=f=90,lowpass=f=12000,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.0:g=2.5,dynaudnorm=f=200:g=11:m=6:p=0.85:r=0.6", "-c:a", "pcm_s24le", str(eq)])
i0 = lufs(eq, a, b)[0]
comp = TMP / f"{src.stem}_comp.wav"
run(["ffmpeg", "-v", "error", "-y", "-i", str(eq), "-af", f"volume={-20 - i0:.2f}dB,acompressor=threshold=-28dB:ratio=3:attack=5:release=90", "-c:a", "pcm_s24le", str(comp)])
i1 = lufs(comp, a, b)[0]
dst.parent.mkdir(parents=True, exist_ok=True)
run(["ffmpeg", "-v", "error", "-y", "-i", str(comp), "-af", f"volume={-15 - i1:.2f}dB,alimiter=limit=0.8:attack=3:release=40:level=false", "-ar", str(SR), "-c:a", "pcm_s16le", str(dst)])
for p in (raw, den, eq, comp):
    p.unlink(missing_ok=True)
print(f"{dst.name}: {lufs(dst, a, b)[0]:.1f} LUFS en el tramo")
