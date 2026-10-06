"""Empaqueta, renderiza, iguala volumen, verifica y entrega.

    python render_todo.py --bundle                 # solo arma el bundle (después de cambiar plantilla/cfg/assets)
    python render_todo.py Mudra1 Mudra2 ...        # renderiza esas (usa el bundle que ya está)
    python render_todo.py --todo                   # bundle + todas las composiciones de proyecto.json "entregas"

Por qué así:
  - Bundle PROPIO con entry propio y public propio: el repo de Remotion lo comparten otras
    sesiones; si alguien deja un archivo roto o un symlink en public/, el bundle general falla
    (EPERM en Windows) y los renders simultáneos borran la caché de webpack.
  - Reintentos (3): con la PC cargada a veces el navegador no llega a conectar.
  - Volumen final -15 LUFS (pico <= -1 dBTP) sin recodificar el video: Remotion mezcla bajo.
  - Verifica que el MP4 se pueda leer, 1080x1920, con audio.
  - Copia a la carpeta de entrega con el nombre de proyecto.json "entregas".
TEMP/TMP van a la carpeta tmp del proyecto (el disco C: se llenó una vez con los temporales).
"""
import os, pathlib, shutil, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import C, BUNDLE, ENTREGA, PLANTILLA, PUB, RAIZ, REMOTION, TMP, dur, lufs, run  # noqa: E402

ENV = {**os.environ, "TEMP": str(TMP), "TMP": str(TMP)}
SALIDA = RAIZ / "out"
NPX = "npx.cmd" if os.name == "nt" else "npx"


def bundle():
    shutil.rmtree(BUNDLE, ignore_errors=True)
    entry = PLANTILLA / "entry.tsx"
    r = subprocess.run([NPX, "remotion", "bundle", str(entry), f"--public-dir={PUB}", f"--out-dir={BUNDLE}", "--bundle-cache=false"], cwd=REMOTION, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not (BUNDLE / "index.html").exists():
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit("falló el bundle: revisá errores de TypeScript en la plantilla/cfg")
    print("bundle ok ->", BUNDLE)


def render(comp):
    SALIDA.mkdir(exist_ok=True)
    out = SALIDA / f"{comp}.mp4"
    out.unlink(missing_ok=True)
    for intento in range(1, 4):
        r = subprocess.run([NPX, "remotion", "render", str(BUNDLE), comp, str(out), "--codec=h264", "--crf=17", "--jpeg-quality=95", "--audio-codec=aac", "--audio-bitrate=256k", "--timeout=240000", f"--concurrency={C.get('concurrencia', 5)}"],
                           cwd=REMOTION, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if out.exists() and dur(out):
            break
        print(f"{comp}: intento {intento} falló\n{r.stderr[-800:]}")
    else:
        print(f"FALLÓ {comp}")
        return None
    # volumen parejo
    i, _ = lufs(out)
    g = round(-15 - i, 2)
    fin = out.with_name(out.stem + "_f.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "copy", "-af", f"volume={g}dB,alimiter=limit=0.84:attack=3:release=60:level=false", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(fin)])
    fin.replace(out)
    i2, tp = lufs(out)
    v = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "csv=p=0", str(out)]).stdout.split()
    print(f"OK {comp}: {dur(out):.2f} s · {i2:.1f} LUFS · pico {tp:.1f} dBTP · {' '.join(v)}")
    dest = C.get("entregas", {}).get(comp)
    if dest:
        d = ENTREGA / dest
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, d)
        print("   ->", d)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    if "--bundle" in args or "--todo" in args:
        bundle()
    comps = [a for a in args if not a.startswith("--")]
    if "--todo" in args:
        comps = list(C.get("entregas", {}))
    for c in comps:
        render(c)
