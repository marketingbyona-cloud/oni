"""Arma un reel a partir de su plan: configuración para la plantilla + música + efectos.

    python armar.py reel3            # uno
    python armar.py reel1 reel2 extra1 ...

Lee planes.py (en la carpeta del proyecto: PLANES[clave] y FIX) y ana/<voz>/vo_final.json.
Escribe:
  <plantilla>/cfg/<clave>.ts      (export const CFG_<CLAVE>: ReelCfg = {...})
  <plantilla>/cfg/index.ts        (todas las cfg -> ids de composición, se regenera solo)
  pub/<marca>/<clave>/musica.wav  (musica.py con el estilo del plan; hits en gancho, precios, tienda)
  pub/<marca>/<clave>/sfx.wav     (whoosh en entradas, pop en placas/precios, tic en listas)

ANCLAS (todo lo que tiene tiempo se ancla a palabras de la voz, no a segundos):
  "presento"        comienzo de la 1ra vez que se dice "presento" (sin tildes ni mayúsculas)
  "lua#2"           la 2da vez
  "48-0.1"          0.1 s antes;  "gratis+0.6"  0.6 s después
  3.5               segundos (en extras sin voz, o para el comienzo: 0)
Si cambiás la voz (vo.py / vo_cortar.py) las anclas se re-ubican solas: por eso se usan.

Avisos que imprime (prestales atención, son errores que ya pasaron):
  - toma de menos de 0.6 s (salvo montaje "ritmo"): parpadeo o "cortes muy rápidos"
  - toma estirada por falta de material (rate < 0.5) o desde ajustado
  - placa/pastilla/precio superpuestos en el tiempo
"""
import json, pathlib, re, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import ANA, ASSETS, C, MARCA, PLANTILLA, RAIZ, TMP, comp_id, dur, norm  # noqa: E402
import numpy as np  # noqa: E402
from scipy.io import wavfile  # noqa: E402

sys.path.insert(0, str(RAIZ))
from planes import PLANES, FIX  # noqa: E402

AQUI = pathlib.Path(__file__).parent
WEB = C.get("web", {})


def armar(clave):
    P = PLANES[clave]
    vo_de = P.get("vo_de", clave)
    if P.get("vo", True):
        V = json.loads((ANA / vo_de / "vo_final.json").read_text(encoding="utf-8"))
    else:
        V = {"dur": P["dur"], "words": [], "pieces": []}
    W = V["words"]
    avisos = []
    (ASSETS / clave).mkdir(parents=True, exist_ok=True)

    def at(a):
        if isinstance(a, (int, float)):
            return float(a)
        m = re.match(r"^([^#+\-]+)(?:#(\d+))?([+\-][\d.]+)?$", a)
        if not m:
            raise SystemExit(f"{clave}: ancla mal escrita '{a}'")
        w, n, off = m.group(1), int(m.group(2) or 1), float(m.group(3) or 0)
        hits = [x for x in W if norm(x["w"]) == norm(w)]
        if len(hits) < n:
            raise SystemExit(f"{clave}: no encuentro '{w}' #{n} en la voz (¿Whisper la escribió distinto? mirá vo_final.json)")
        return hits[n - 1]["t"] + off

    end_t0 = round(at(P["end_at"]) if "end_at" in P else V["dur"] + 0.3, 3)
    total = round(end_t0 + P.get("end_len", 3.6), 3)

    # ── tomas: cada una dura hasta la siguiente; la última hasta el cierre
    shots = []
    for i, s in enumerate(P["shots"]):
        t0 = at(s[0])
        t1 = at(P["shots"][i + 1][0]) if i + 1 < len(P["shots"]) else end_t0
        src = s[1] if "/" in s[1] else f"{clave}/{s[1]}"
        foto = src.lower().endswith((".jpg", ".jpeg", ".png"))
        sh = {"src": src if src.endswith(".mp4") or foto else src + ".mp4", "from": float(s[2]), "t0": round(t0, 3), "t1": round(t1, 3)}
        sh.update(s[3] if len(s) > 3 else {})
        if "punch" in sh:
            sh["punch"] = sorted(round(at(x), 3) for x in sh["punch"])
        sync = sh.pop("sync", None)
        ritmo = sh.pop("ritmo", False)
        if t1 - t0 < 0.6 and not ritmo:
            avisos.append(f"toma {src} dura {t1 - t0:.2f} s (< 0.6): ¿anclas muy juntas? (si es montaje al ritmo, poné ritmo=True)")
        if t1 <= t0:
            raise SystemExit(f"{clave}: la toma {i} ({src}) termina antes de empezar: anclas fuera de orden")
        if sync:  # la toma suena en la voz: la imagen arranca donde arranca su audio (labios en sincro)
            piece = next(p for p in V["pieces"] if p["src"] == sync)
            sh["from"] = round(piece["from"] + (t0 - piece["at"]), 3)
        clip = ASSETS / sh["src"]
        if not clip.exists():
            raise SystemExit(f"falta {clip} (convertir.py / analizar.py --fotos)")
        if not foto:
            d = dur(clip)
            if d is None:
                raise SystemExit(f"{clip} está roto (conversión cortada): borralo y volvé a convertir")
            need = (t1 - t0) * sh.get("rate", 1)
            if sync and sh["from"] + need > d - 0.05:
                raise SystemExit(f"{clave}: la toma sincronizada {sh['src']} no alcanza ({sh['from']}+{need:.2f} > {d:.2f}); cortala antes")
            if sh["from"] + need > d - 0.05:
                nf = max(0.0, d - 0.05 - need)
                sh["from"] = round(nf, 2)
                if need > d:
                    sh["rate"] = round(max(0.3, (d - 0.1) / (t1 - t0)), 3)
                    avisos.append(f"{sh['src']} no alcanza: rate {sh['rate']} (cámara lenta forzada; mejor otra toma o partirla)")
        shots.append(sh)

    # ── subtítulos con el texto corregido
    words = []
    for w in W:
        txt, k = w["w"], norm(w["w"])
        if k in FIX:
            if FIX[k] is None:
                continue
            pre = re.match(r"^[¿¡]*", txt).group(0)
            post = re.search(r"[,.!?:;]*$", txt).group(0)
            txt = pre + FIX[k] + post
        words.append({"w": txt, "t": w["t"], "e": w["e"]})
    res = []
    for w in words:  # "48" ".750" -> "$48.750" · "81" "mil" -> "$81.000" · "25" "%" -> "25%"
        prev = res[-1]["w"] if res else ""
        if res and re.match(r"^\.\d{3}", w["w"]) and re.match(r"^\$?\d+$", prev):
            res[-1] = {"w": "$" + prev.lstrip("$") + w["w"], "t": res[-1]["t"], "e": w["e"]}
        elif res and norm(w["w"]) == "mil" and re.match(r"^\$?\d+$", prev):
            res[-1] = {"w": "$" + prev.lstrip("$") + ".000" + re.search(r"[,.!?:;]*$", w["w"]).group(0), "t": res[-1]["t"], "e": w["e"]}
        elif res and w["w"].startswith("%") and re.match(r"^\$?\d+$", prev):
            res[-1] = {"w": prev + w["w"], "t": res[-1]["t"], "e": w["e"]}
        else:
            res.append(w)
    words = [w for w in res if norm(w["w"]) != "pesos"]  # el precio ya lleva $
    # tartamudeos ("y y", "la la"): una sola vez
    words = [w for i, w in enumerate(words) if not (i and norm(w["w"]) == norm(words[i - 1]["w"]) and len(norm(w["w"])) <= 3)]

    T = lambda a: round(at(a), 3)  # noqa: E731
    extra = lambda x, n: x[n] if len(x) > n else {}  # noqa: E731
    cfg = {
        "dir": f"{MARCA}/",
        "total": total,
        "vo": f"{vo_de}/vo.wav" if P.get("vo", True) else None,
        "music": f"{clave}/musica.wav",
        "words": words,
        "shots": shots,
        "hook": {**P["hook"], "to": T(P["hook"]["to"])},
        "tags": [{**{k: v for k, v in {"name": t[2], "sub": t[3], "price": t[4], "t0": T(t[0]), "t1": T(t[1])}.items() if v is not None}, **extra(t, 5)} for t in P.get("tags", [])],
        "chips": [{"text": c[2], "t0": T(c[0]), "t1": T(c[1]), **extra(c, 3)} for c in P.get("chips", [])],
        "prices": [{"big": p[2], "small": p[3], "t0": T(p[0]), "t1": T(p[1]), **extra(p, 4)} for p in P.get("prices", [])],
        "pops": [{"text": p[2], "t0": T(p[0]), "t1": T(p[1]), **extra(p, 3)} for p in P.get("pops", [])],
        # la lista entra con su primer ítem (si no, queda una tarjeta vacía en pantalla)
        "checks": [{"title": c[2], "t0": max(T(c[0]), round(min(T(it[0]) for it in c[3]) - 0.05, 3)), "t1": T(c[1]), "items": [{"text": it[1], "at": T(it[0])} for it in c[3]], **extra(c, 4)} for c in P.get("checks", [])],
        "end": {"t0": end_t0, **P["end"]},
    }
    if "captions_off" in P:  # tramos sin subtítulos (p. ej. cuando el texto ya está en pantalla)
        cfg["captionsOff"] = [[T(a), T(b)] for a, b in P["captions_off"]]
    if not cfg["vo"]:
        del cfg["vo"]

    # ── la tienda en un celular (captura real de web_tienda.py): scroll al producto, marca del precio, toque en comprar
    if P.get("web"):
        wa, key = P["web"]
        w0 = T(wa)
        d = end_t0 - w0
        if d < 2.2:
            avisos.append(f"la tienda queda solo {d:.1f} s en pantalla (mejor 3-4 s)")
        B = json.load(open(ASSETS / "web" / f"{key}.json", encoding="utf-8"))
        sw, sh_ = B["_size"]
        vis = (1060 - 28 - 112) / ((520 - 28) / sw)  # alto de captura visible en la pantalla del celular (PW 520, PH 1060, borde 14, barra 112)
        k = min(1.0, d / 3.6)
        web = {"t0": w0, "t1": end_t0, "img": f"web/{key}.png", "sw": sw, "sh": sh_, "url": WEB.get("url_visible", WEB.get("base", "").split("//")[-1].strip("/"))}
        if "comprar" in B and "nombre" in B:
            y1 = B["nombre"]["y"] - 140
            y2 = max(y1, B["comprar"]["y"] + B["comprar"]["h"] + 160 - vis)
            web["scroll"] = [[0, 0], [0.45 * k, 0], [1.15 * k, y1], [2.0 * k, y1], [2.6 * k, y2]]
            if "transferencia" in B and WEB.get("etiqueta"):
                tr = B["transferencia"]
                web["marks"] = [{"t": 1.3 * k, "x": 30, "y": tr["y"] - 6, "w": tr["x"] + tr["w"] - 20, "h": tr["h"] + 12, "label": WEB["etiqueta"]}]
            web["taps"] = [{"t": 2.9 * k, "x": B["comprar"]["x"] + B["comprar"]["w"] / 2, "y": B["comprar"]["y"] + B["comprar"]["h"] / 2}]
        else:  # inicio / categoría: baja mostrando banners y productos
            web["scroll"] = [[0, 0], [0.5 * k, 0], [1.9 * k, min(2000, sh_ * 0.3)]]
        web["scroll"] = [[round(a, 3), round(b)] for a, b in web["scroll"]]
        cfg["web"] = web
        for kind in ("tags", "chips", "prices", "pops", "checks"):  # lo que estaba en pantalla se va cuando entra el celular
            for o in cfg[kind]:
                if o["t0"] < w0 < o["t1"]:
                    o["t1"] = w0

    # ── superposiciones en el tiempo entre gráficos
    graf = [(k, o) for k in ("tags", "chips", "prices", "pops", "checks") for o in cfg[k]]
    for i, (ka, a) in enumerate(graf):
        for kb, b in graf[i + 1:]:
            if a["t0"] < b["t1"] - 0.05 and b["t0"] < a["t1"] - 0.05 and "y" not in a and "y" not in b and ka == kb:
                avisos.append(f"dos {ka} a la vez ({a.get('text', a.get('name', a.get('big')))} / {b.get('text', b.get('name', b.get('big')))}): se pisan")

    # ── efectos de sonido
    fx = efectos(cfg, total)
    if fx:
        cfg["sfx"] = f"{clave}/sfx.wav"

    out = PLANTILLA / "cfg" / f"{clave}.ts"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"// generado por armar.py: no editar a mano (editá planes.py y volvé a correr)\nimport type {{ ReelCfg }} from \"../ReelMarca\";\nexport const CFG_{clave.upper()}: ReelCfg = " + json.dumps(cfg, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    indice()

    # ── música: tramos con voz (para agacharse) y golpes en los cambios
    voz = []
    for w in W:
        if voz and w["t"] - voz[-1][1] < 0.5:
            voz[-1][1] = w["e"]
        else:
            voz.append([w["t"], w["e"]])
    hits = sorted({cfg["hook"]["to"], *[p["t0"] for p in cfg["prices"]], *([cfg["web"]["t0"]] if cfg.get("web") else [])} | set(T(h) for h in P.get("hits", [])))
    tl = TMP / f"{clave}.json"
    json.dump({"total": total, "voz": voz, "hits": [h for h in hits if 1.0 < h < end_t0], "end": end_t0}, open(tl, "w"))
    (ASSETS / clave).mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(AQUI / "musica.py"), str(tl), P.get("style", "nudisco"), str(ASSETS / clave / "musica.wav")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip() or r.stderr[-500:])
    for a in avisos:
        print("  AVISO:", a)
    print(f"{clave} ({comp_id(clave)}): {len(shots)} tomas, total {total:.2f} s, cierre en {end_t0:.2f} s" + (f", tienda desde {cfg['web']['t0']:.2f} s" if cfg.get("web") else ""))


def efectos(cfg, total):
    """whoosh en entradas con barrido/zoom, pop en precios/pops, pop suave en placas/pastillas, tic en listas.
    Picos a -9 dBFS: se oyen sin tapar la voz."""
    sr = 48000
    n = int((total + 1) * sr)
    y = np.zeros(n)
    rng = np.random.default_rng(7)
    from scipy.signal import butter, sosfilt

    def put(t, x, g):
        i = int(t * sr)
        if 0 <= i < n:
            m = min(len(x), n - i)
            y[i:i + m] += g * x[:m]

    def whoosh(d=0.32):
        k = int(d * sr)
        ruido = rng.standard_normal(k)
        out = np.zeros(k)
        zi = np.zeros((2, 2))  # estado del filtro entre bloques: sin chisporroteo
        for i in range(0, k, 256):
            fc = 400 + 5000 * np.sin(np.pi * min(1, i / k)) ** 2
            out[i:i + 256], zi = sosfilt(butter(2, [max(100, fc * 0.5), min(16000, fc * 1.6)], "band", fs=sr, output="sos"), ruido[i:i + 256], zi=zi)
        return out * np.sin(np.pi * np.linspace(0, 1, k)) ** 1.5

    def pop(f0=520):
        k = int(0.09 * sr)
        t = np.arange(k) / sr
        fr = f0 * (1.6 - 0.6 * t / t[-1])
        return np.sin(2 * np.pi * np.cumsum(fr) / sr) * np.exp(-t / 0.025)

    def tic():
        t = np.arange(int(0.05 * sr)) / sr
        return (np.sin(2 * np.pi * 1900 * t) + 0.5 * np.sin(2 * np.pi * 3100 * t)) * np.exp(-t / 0.008)

    for sh in cfg["shots"]:
        if sh.get("entra") in ("zoom", "whip"):
            put(sh["t0"] - 0.16, whoosh(), 0.11)
        elif sh.get("entra") == "flash":
            put(sh["t0"] - 0.02, pop(300), 0.18)
    for o in cfg["prices"] + cfg["pops"]:
        put(o["t0"], pop(560), 0.2)
    for o in cfg["tags"] + cfg["chips"]:
        put(o["t0"], pop(760), 0.11)
    for o in cfg["checks"]:
        for it in o["items"]:
            put(it["at"] + 0.13, tic(), 0.14)
    if cfg.get("web"):
        put(cfg["web"]["t0"] - 0.1, whoosh(0.4), 0.12)
    if not np.any(y):
        return None
    y = y / max(1e-9, np.abs(y).max()) * 0.35
    clave = cfg["music"].split("/")[0]
    wavfile.write(ASSETS / clave / "sfx.wav", sr, (y * 32767).astype(np.int16))
    return True


def indice():
    """cfg/index.ts con todas las configuraciones -> ids de composición (no hay que editarlo a mano)."""
    cfgs = sorted(p.stem for p in (PLANTILLA / "cfg").glob("*.ts") if p.stem != "index")
    lines = ['import type { ReelCfg } from "../ReelMarca";']
    lines += [f'import {{ CFG_{c.upper()} }} from "./{c}";' for c in cfgs]
    lines += ["", "/** generado por armar.py: id de composición -> configuración */", "export const CFGS: Record<string, ReelCfg> = {"]
    lines += [f"  {comp_id(c)}: CFG_{c.upper()}," for c in cfgs]
    lines += ["};", ""]
    (PLANTILLA / "cfg" / "index.ts").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    for c in sys.argv[1:]:
        armar(c)
