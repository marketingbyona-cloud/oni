# editor-reels — cómo instalarla y usarla

Skill de Claude para editar reels de marcas (jornadas de contenido) con Remotion + Python.

## Instalar la skill
- **Claude Code / app de escritorio:** copiá la carpeta `editor-reels` a `%USERPROFILE%\.claude\skills\`
  (o abrí el archivo `.skill` y tocá "Save skill"). Claude la usa sola cuando le pedís editar reels.
- Para verificar: pedile "¿qué skills tenés para editar reels?".

## Instalar lo que usa (una vez)
1. ffmpeg y ffprobe en el PATH.
2. Python 3.11+: `pip install faster-whisper numpy scipy pillow pillow-heif noisereduce playwright`
3. Node 18+ y un proyecto de Remotion 4.x (`npx create-video@latest`, o el repo `remotion-editor` de la
   agencia) con `npm i @remotion/google-fonts`.
4. La primera transcripción baja el modelo Whisper large-v3 (~3 GB).

## Primer uso
Decile a Claude algo como: "Te paso el Drive de la jornada de <marca> y su web <url>. Editá los reels
según el guion, dejalos en el Escritorio en una carpeta <MARCA>, y con Crudos armá 3 extras."
Claude va a crear `proyecto.json`, copiar la plantilla al repo de Remotion, ajustar `tema.ts` con los
colores y tipografías de la web, y seguir el flujo de `references/flujo.md`.

## Qué hay adentro
- `SKILL.md`: reglas de oro y mapa de la skill.
- `references/`: flujo paso a paso, voz, motion gráficos, música, control de calidad (con todas las
  correcciones que pidió Agus), entorno/Windows, fichas de marcas, otros formatos.
- `scripts/`: el pipeline (Drive, análisis, voz, conversión, web, música, armado, render, control).
- `assets/`: plantilla de Remotion (ReelMarca + tema por marca), proyecto y planes de ejemplo.
