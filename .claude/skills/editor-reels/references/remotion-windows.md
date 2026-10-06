# Entorno: instalación, Remotion, Windows y trampas conocidas

## Instalar (una vez por máquina)

- **ffmpeg y ffprobe** en el PATH (`ffmpeg -version`).
- **Python 3.11+** con:
  `pip install faster-whisper numpy scipy pillow pillow-heif noisereduce playwright`
  (Playwright usa el Chrome que trae Remotion; si no lo encuentra: `python -m playwright install chromium`).
- **Node 18+** y un repo de Remotion 4.x con `@remotion/google-fonts` y `@remotion/renderer`:
  `npx create-video@latest` o el repo de la agencia (`remotion-editor`). `npm i @remotion/google-fonts`.
- **curl** (viene con Windows 10+).
- Whisper `large-v3` se descarga solo la primera vez (~3 GB): hacelo con tiempo.

## Por qué bundle propio + public propio + entry propio

El repo de Remotion de la agencia lo usan varias sesiones de Claude a la vez. Pasó:
- alguien dejó un symlink/junction en `public/` y el bundler de Remotion falla en Windows con **EPERM**
  al copiarlo → todo bundle que use ese public se rompe;
- otra sesión dejó una plantilla a medio editar con error de sintaxis → **el bundle de `src/index.ts`
  se rompe para todos**;
- renders simultáneos borran la caché de webpack ("Webpack config change detected") y el navegador no
  llega a conectar (timeout 25 s).
Solución (la que usa `render_todo.py`):
1. assets de la marca en una carpeta pública PROPIA (`pub/<marca>/`), nunca en `public/` del repo;
2. `entry.tsx` propio que registra solo las composiciones de la marca;
3. `npx remotion bundle <entry> --public-dir=<pub> --out-dir=<bundle> --bundle-cache=false` una vez,
   y `npx remotion render <bundle> <Comp> ...` (con reintentos) todas las veces que haga falta;
4. no tocar archivos de otras sesiones/marcas.

## Comandos de render (los que usa render_todo.py)
```
npx remotion render <bundle> <Comp> out.mp4 --codec=h264 --crf=17 --jpeg-quality=95 --audio-codec=aac --audio-bitrate=256k --timeout=240000 --concurrency=5
```
- `--timeout=240000`: con videos 60 fps y la PC cargada, el default no alcanza.
- `--concurrency` 3–5 según la PC (más no siempre es más rápido si hay otros procesos).
- TEMP/TMP a un disco con lugar: el C: se llenó a 0 bytes con temporales de render una vez.
- Cuadros sueltos: `stills.mjs` con `renderStill` y UN navegador abierto (`openBrowser`) para todos.

## Windows
- Consola: los scripts reconfiguran stdout a UTF-8 (si no, las tildes salen "�" o rompen con
  UnicodeEncodeError).
- Rutas: usar `/` o `pathlib`; en bash de Git, `D:\` es `/d/`.
- No dejes procesos a medias: una conversión cortada deja un MP4 roto (ffprobe sin duración) y después
  falla todo con un error raro ("could not convert string to float"). `convertir.py` y `armar.py` lo
  detectan.
- Abrir carpeta con el archivo seleccionado: `explorer.exe /select,"C:\...\video.mp4"`.
- Los celulares graban con rotación −90° en metadatos: ffmpeg la aplica al recodificar.
- Fotos HEIC: `pillow-heif` + `ImageOps.exif_transpose`.

## CPU / RAM compartidas
- La PC suele estar al 100% por otras sesiones: Whisper large-v3 a prioridad baja tardó horas. Usá
  `small` para descartar tomas mudas y `large-v3` solo para las voces.
- Nunca dos Whisper large-v3 en paralelo (se quedó sin RAM).
- Renders largos en segundo plano; mientras, revisá hojas de control o escribí planes.

## Errores frecuentes
| Síntoma | Causa | Arreglo |
|---|---|---|
| `EPERM` al hacer bundle | symlink en el public | public propio |
| Bundle roto por archivo ajeno | plantilla de otra sesión con error | entry propio |
| `Timeout ... browser` | PC cargada / caché borrada | bundle previo + reintentos + `--timeout` |
| Cuadros negros al final | la última toma termina con el cierre | la última toma sigue 0.5 s debajo |
| Cuadros negros entre tomas | sin premount | `premountFor` 20–30 |
| `could not convert string to float` | MP4 roto (conversión cortada) | borrarlo y reconvertir |
| Audio saturado tras cortar | wav int16 escrito como float | conservar el dtype (vo_cortar.py lo hace) |
| Cuadros de control "viejos" | stills.mjs saltea los que existen | control.py borra la carpeta antes |
| Fuente que no aparece | no está en Google Fonts | FontFace + delayRender |
| `startFrom` deprecado | Remotion ≥ 4.0.319 | `trimBefore` |
