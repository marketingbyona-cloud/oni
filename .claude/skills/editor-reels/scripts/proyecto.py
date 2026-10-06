"""Configuración de un proyecto de reels (una marca, una jornada). Todos los scripts la usan.

Busca `proyecto.json`:
  1. en la ruta de la variable de entorno PROYECTO (el .json o su carpeta), o
  2. en la carpeta actual.

Las rutas relativas del json se resuelven desde la carpeta donde está el json.
Ver assets/proyecto.ejemplo.json para todos los campos.
"""
import json, os, pathlib, re, subprocess, sys, unicodedata

if hasattr(sys.stdout, "reconfigure"):  # tildes en la consola de Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _buscar():
    p = os.environ.get("PROYECTO")
    p = pathlib.Path(p) if p else pathlib.Path.cwd()
    if p.is_dir():
        p = p / "proyecto.json"
    if not p.exists():
        raise SystemExit("No encuentro proyecto.json. Copiá assets/proyecto.ejemplo.json a la carpeta de la jornada "
                         "(y corré los scripts desde ahí) o definí PROYECTO=<ruta al json>.")
    return p


_P = _buscar()
C = json.load(open(_P, encoding="utf-8"))
BASE = _P.parent


def _ruta(v):
    q = pathlib.Path(v)
    return q if q.is_absolute() else (BASE / q).resolve()


MARCA = C["marca"]                                  # slug: carpeta de assets dentro del public (pub/<marca>/)
PREFIJO = C.get("prefijo", MARCA.capitalize())     # ids de composición: <Prefijo>1, <Prefijo>Extra1...
RAIZ = _ruta(C.get("raiz", "."))                    # carpetas reel1/, crudos/, ana/, tmp/
PUB = _ruta(C.get("pub", "../pub"))                 # carpeta pública propia (render con --public-dir)
ASSETS = PUB / MARCA                                # lo que la plantilla lee con staticFile("<marca>/...")
BUNDLE = _ruta(C.get("bundle", "../bundle"))
REMOTION = _ruta(C["remotion"])                     # repo de Remotion (node_modules)
PLANTILLA = REMOTION / C.get("plantilla", f"src/templates/{MARCA}")
ENTREGA = _ruta(C["entrega"]) if C.get("entrega") else RAIZ / "ENTREGA"
TMP = _ruta(C.get("tmp", "./tmp"))
ANA = RAIZ / "ana"
WHISPER = {"modelo": "large-v3", "rapido": "small", "hilos": 0, **C.get("whisper", {})}
FPS = int(C.get("fps", 30))
for d in (TMP, ANA, ASSETS):
    d.mkdir(parents=True, exist_ok=True)


def comp_id(clave):
    """reel3 -> <Prefijo>3, extra2 -> <Prefijo>Extra2, promo -> <Prefijo>Promo"""
    m = re.match(r"^reel(\d+)$", clave)
    if m:
        return f"{PREFIJO}{m.group(1)}"
    m = re.match(r"^([a-z]+)(\d*)$", clave)
    return PREFIJO + (m.group(1).capitalize() + m.group(2) if m else clave)


def clave_de(comp):
    """<Prefijo>3 -> reel3, <Prefijo>Extra2 -> extra2"""
    m = re.match(rf"^{PREFIJO}(\d+)$", comp)
    if m:
        return f"reel{m.group(1)}"
    m = re.match(rf"^{PREFIJO}([A-Z][a-z]+)(\d*)$", comp)
    return (m.group(1).lower() + m.group(2)) if m else comp


def norm(s):
    """palabra normalizada: minúscula, sin tildes ni signos (para anclas y comparaciones)"""
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9ñ]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def dur(f):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None  # archivo roto o a medio escribir


def lufs(f, a=None, b=None):
    cmd = ["ffmpeg"] + (["-ss", str(a), "-to", str(b)] if a is not None else []) + ["-i", str(f), "-af", "loudnorm=print_format=json", "-f", "null", "-"]
    m = run(cmd).stderr
    j = json.loads(m[m.rindex("{"): m.rindex("}") + 1])
    return float(j["input_i"]), float(j["input_tp"])


_WM = {}


def whisper(modelo=None):
    """faster-whisper en CPU (int8). Uno solo por vez: dos large-v3 juntos se quedan sin RAM."""
    from faster_whisper import WhisperModel
    modelo = modelo or WHISPER["modelo"]
    if modelo not in _WM:
        _WM[modelo] = WhisperModel(modelo, device="cpu", compute_type="int8", cpu_threads=int(WHISPER["hilos"]) or 0)
    return _WM[modelo]
