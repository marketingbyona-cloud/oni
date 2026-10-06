"""Análisis de las carpetas de la jornada: hojas de contacto, qué se dice en cada toma y voces en off.

    python analizar.py reel1 reel2 crudos/videos ...
    python analizar.py --fotos crudos/fotos         # HEIC/JPG -> pub/<marca>/fotos/fNNNN.jpg + hoja

Por carpeta escribe ana/<carpeta>/:
  sheet_XX.jpg  hojas de contacto: 6 tomas por hoja, 5 cuadros por toma, con número y duración.
                MIRALAS (Read) antes de elegir tomas: es la única forma de saber dónde está el
                producto, la cara, si la toma tiembla o si sirve.
  tomas.json    duración, tamaño, rotación y lo que se oye en cada toma (Whisper rápido, con VAD:
                sirve para encontrar tomas habladas a cámara y para NO usar partes donde habla
                alguien del equipo en tomas de recurso).
  vo.json       voces en off (.m4a/.mp3/.wav) transcriptas con el modelo grande y tiempos por palabra.

Whisper inventa "Gracias por ver el video" o "Subtítulos por..." en tomas mudas: ignoralo.
La PC suele estar cargada: el modelo rápido descarta tomas mudas, el grande solo para voces.
"""
import io, json, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import RAIZ, ANA, ASSETS, run, whisper  # noqa: E402

try:
    FONT = ImageFont.truetype("arial.ttf", 22)
except OSError:
    FONT = ImageFont.load_default()


def probe(f):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height:stream_side_data=rotation", "-of", "json", str(f)])
    j = json.loads(r.stdout)
    st = next((s for s in j.get("streams", []) if s.get("width")), {})
    rot = 0
    for sd in st.get("side_data_list", []) or []:
        rot = sd.get("rotation", rot)
    return float(j["format"]["duration"]), st.get("width"), st.get("height"), rot


def cuadros(f, d, n=5, h=300):
    ims = []
    for k in range(n):
        t = d * (0.06 + 0.88 * k / (n - 1))
        out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(f), "-frames:v", "1", "-vf", f"scale=-2:{h}", "-f", "image2pipe", "-vcodec", "mjpeg", "-"], capture_output=True).stdout
        try:
            ims.append(Image.open(io.BytesIO(out)).convert("RGB"))
        except Exception:
            ims.append(Image.new("RGB", (169, h), "gray"))
    return ims


def hojas(filas, out, pref="sheet"):
    for i in range(0, len(filas), 6):
        chunk = filas[i:i + 6]
        W = max(r.width for r in chunk)
        s = Image.new("RGB", (W, sum(r.height for r in chunk)), "white")
        y = 0
        for r in chunk:
            s.paste(r, (0, y)); y += r.height
        s.save(out / f"{pref}_{i // 6 + 1:02d}.jpg", quality=80)


def fotos(carpeta):
    """HEIC/JPG de la carpeta -> pub/<marca>/fotos/f<número>.jpg (1080 de ancho) + hoja con números."""
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        print("falta pillow-heif (pip install pillow-heif) para las fotos .HEIC")
    from PIL import ImageOps
    src = RAIZ / carpeta
    dst = ASSETS / "fotos"
    dst.mkdir(parents=True, exist_ok=True)
    thumbs = []
    for p in sorted(src.iterdir()):
        if p.suffix.lower() not in (".heic", ".jpg", ".jpeg", ".png", ".webp"):
            continue
        num = "".join(c for c in p.stem if c.isdigit())[-4:] or p.stem
        out = dst / f"f{num}.jpg"
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")  # respeta la rotación de la foto
        if not out.exists():
            im.copy().resize((1080, round(im.height * 1080 / im.width))).save(out, quality=90)
        th = im.copy(); th.thumbnail((200, 260))
        thumbs.append((num, th))
    cols = 10
    W, H = 200, 285
    s = Image.new("RGB", (cols * W, ((len(thumbs) + cols - 1) // cols) * H), "white")
    d = ImageDraw.Draw(s)
    for i, (num, th) in enumerate(thumbs):
        x, y = (i % cols) * W, (i // cols) * H
        s.paste(th, (x, y)); d.text((x + 4, y + 262), num, fill="black", font=FONT)
    out = ANA / carpeta.replace("/", "_")
    out.mkdir(parents=True, exist_ok=True)
    s.save(out / "fotos.jpg", quality=80)
    print(f"{len(thumbs)} fotos -> {dst} · hoja {out / 'fotos.jpg'}")


def carpeta_videos(carpeta):
    src = RAIZ / carpeta
    out = ANA / carpeta.replace("/", "_")
    out.mkdir(parents=True, exist_ok=True)
    movs = sorted(p for p in src.iterdir() if p.suffix.lower() in (".mov", ".mp4"))
    tomas, filas = [], []
    for f in movs:
        d, w, h, rot = probe(f)
        ims = cuadros(f, d)
        fila = Image.new("RGB", (sum(i.width for i in ims) + 8 * len(ims) + 230, ims[0].height + 10), "white")
        dr = ImageDraw.Draw(fila)
        dr.text((8, 10), f.stem.replace("IMG_", ""), fill="black", font=FONT)
        dr.text((8, 40), f"{d:.1f}s", fill="black", font=FONT)
        x = 230
        for im in ims:
            fila.paste(im, (x, 5)); x += im.width + 8
        filas.append(fila)
        tomas.append({"file": f.name, "dur": round(d, 2), "w": w, "h": h, "rot": rot})
        print(carpeta, f.name, round(d, 1), flush=True)
    if filas:
        hojas(filas, out)
    if tomas:
        rapido = whisper("small")
        for t in tomas:
            wav = out / "tmp.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src / t["file"]), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
            if not wav.exists() or wav.stat().st_size < 2000:
                t["habla"] = ""
                continue
            segs, _ = rapido.transcribe(str(wav), language="es", vad_filter=True, condition_on_previous_text=False)
            t["habla"] = " ".join(s.text.strip() for s in segs)[:400]
        json.dump(tomas, open(out / "tomas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    vos = {}
    audios = sorted(p for p in src.iterdir() if p.suffix.lower() in (".m4a", ".mp3", ".wav", ".aac", ".ogg"))
    if audios:
        grande = whisper()
        for f in audios:
            wav = out / "tmp.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-ac", "1", "-ar", "16000", str(wav)])
            segs, _ = grande.transcribe(str(wav), language="es", word_timestamps=True, condition_on_previous_text=False)
            ws = [(w.word.strip(), round(w.start, 2), round(w.end, 2)) for s in segs for w in s.words]
            vos[f.name] = ws
            print("VO", f.name, " ".join(w for w, _, _ in ws), flush=True)
        json.dump(vos, open(out / "vo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    (out / "tmp.wav").unlink(missing_ok=True)
    print("LISTO", carpeta, "->", out, flush=True)


if __name__ == "__main__":
    if not sys.argv[1:]:
        raise SystemExit(__doc__)
    if sys.argv[1] == "--fotos":
        for c in sys.argv[2:]:
            fotos(c)
    else:
        for c in sys.argv[1:]:
            carpeta_videos(c)
