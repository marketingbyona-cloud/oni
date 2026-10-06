"""Baja una carpeta PÚBLICA de Google Drive (la jornada) con todas sus subcarpetas.

    python drive_bajar.py --ver <id_o_link>        # solo lista (título, carpetas, archivos, docs)
    python drive_bajar.py <id_o_link> [destino]    # baja todo a <destino> (por defecto la raíz del proyecto)

- Lista con la vista embebida de Drive (no hace falta login ni la API; la carpeta tiene que
  estar compartida "cualquiera con el link").
- Nombres de carpeta normalizados: "Reel 1 " -> reel1, "CRUDOS" -> crudos, "REEL 6" -> reel6.
  Subcarpetas anidadas: crudos/fotos, crudos/videos...
- Los Google Docs (guion) se bajan como .txt (export=txt) a <destino>/guion/.
- Se saltean carpetas de salida de la agencia ("finales", "editados", "entregas").
- Archivos con espacios -> guiones bajos. Si ya existe con tamaño > 0 no se vuelve a bajar.
- 3 descargas a la vez (más satura la conexión y Drive corta).

ANTES de editar: abrí el guion y fijate que sea de la marca correcta (una vez llegó la
carpeta de otra marca con la misma estructura "Reel N").
"""
import concurrent.futures as cf
import pathlib, re, subprocess, sys, unicodedata

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SALTEAR = {"finales", "final", "editados", "editado", "entregas", "entrega", "exportados"}


def fid(x):
    m = re.search(r"folders/([\w-]+)", x) or re.search(r"id=([\w-]+)", x)
    return m.group(1) if m else x.strip()


def slug(nombre):
    s = unicodedata.normalize("NFD", nombre.strip().lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s or "carpeta"


def listar(id_):
    h = subprocess.run(["curl", "-s", "-L", f"https://drive.google.com/embeddedfolderview?id={id_}"], capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout
    titulo = re.search(r"<title>([^<]*)</title>", h)
    items = []
    for m in re.finditer(r'<a href="([^"]+)"[^>]*>.*?flip-entry-title">([^<]+)</div>', h, re.S):
        url, nombre = m.group(1), m.group(2).strip()
        if "/drive/folders/" in url:
            items.append(("carpeta", fid(url), nombre))
        elif "docs.google.com/document/d/" in url:
            items.append(("doc", re.search(r"/d/([\w-]+)", url).group(1), nombre))
        elif "/file/d/" in url:
            items.append(("archivo", re.search(r"/file/d/([\w-]+)", url).group(1), nombre))
    return (titulo.group(1) if titulo else "?"), items


def arbol(id_, ruta=pathlib.Path("."), nivel=0, ver=False, out=None):
    titulo, items = listar(id_)
    if nivel == 0:
        print(f"Carpeta: {titulo}")
    out = [] if out is None else out
    for tipo, i, nombre in items:
        print("  " * (nivel + 1) + f"[{tipo}] {nombre}")
        if tipo == "carpeta":
            if slug(nombre) in SALTEAR:
                print("  " * (nivel + 2) + "(salteada)")
                continue
            arbol(i, ruta / slug(nombre), nivel + 1, ver, out)
        elif tipo == "doc":
            out.append(("doc", i, pathlib.Path("guion") / (re.sub(r'[\\/:*?"<>|]+', "-", nombre).strip() + ".txt")))
        else:
            out.append(("archivo", i, ruta / nombre.replace(" ", "_")))
    return out


def bajar(job, destino):
    tipo, i, rel = job
    f = destino / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    if f.exists() and f.stat().st_size > 0:
        return f"ya {rel}"
    url = f"https://docs.google.com/document/d/{i}/export?format=txt" if tipo == "doc" else f"https://drive.usercontent.google.com/download?id={i}&export=download&confirm=t"
    r = subprocess.run(["curl", "-s", "-L", "-f", "-o", str(f), url])
    ok = r.returncode == 0 and f.exists() and f.stat().st_size > 0
    if not ok and f.exists():
        f.unlink()  # nada de archivos a medias: los scripts siguientes fallarían raro
    return f"{'ok' if ok else 'FALLÓ'} {rel}"


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--ver"]
    if not args:
        raise SystemExit(__doc__)
    jobs = arbol(fid(args[0]))
    if "--ver" in sys.argv:
        sys.exit()
    if len(args) > 1:
        destino = pathlib.Path(args[1])
    else:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        from proyecto import RAIZ as destino
    print(f"\n{len(jobs)} archivos -> {destino}")
    fallas = []
    with cf.ThreadPoolExecutor(3) as ex:
        for msg in ex.map(lambda j: bajar(j, destino), jobs):
            print(msg, flush=True)
            if msg.startswith("FALLÓ"):
                fallas.append(msg)
    print("LISTO" if not fallas else f"LISTO con {len(fallas)} fallas: volvé a correr el mismo comando (saltea lo ya bajado)")
