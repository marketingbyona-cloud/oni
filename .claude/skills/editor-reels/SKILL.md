---
name: editor-reels
description: >-
  Editor profesional de reels/TikToks de marcas (9:16) con Remotion + Python: toma una jornada de
  contenido (Drive con carpetas "Reel N", "Crudos", voces en off .m4a y guion), la web de la marca, y
  entrega los videos editados con voz limpia, subtítulos palabra por palabra, motion gráficos (gancho,
  placas de producto, precios, pastillas, listas, la tienda real en un celular), música propia y
  control de calidad cuadro por cuadro. Usala SIEMPRE que pidan editar, armar, cortar o corregir reels,
  videos para Instagram/TikTok, "jornada de contenido", "uní los videos según el guion", "con los
  crudos armá extras", voz en off, subtítulos, motion gráficos, placas de precio, música para reels,
  o correcciones del tipo "se traba la voz", "el gráfico tapa el producto", "la música satura", aunque
  no digan "skill" ni "Remotion".
---

# Editor de reels de marcas

Esta skill condensa decenas de reels entregados a la agencia (Mudra, Blessed, Ambos Up!doc, Mirana,
GEMA, Bohemian, JUCA, Arte Para Pocos…) y **todas las correcciones** que hizo el cliente interno
(Agus). El objetivo no es "un video", es un video que no vuelva con correcciones: voz que no se traba,
gráficos que nunca tapan el producto, música con energía y datos correctos.

## Las reglas de oro (cada una salió de una corrección real)

1. **Ningún gráfico tapa el producto ni una cara.** Cada toma del plan dice dónde está el producto
   (`zone` top/mid/low) y los textos van a la zona libre. Si no hay zona libre, se cambia la toma.
2. **Safe zone de Instagram:** nada importante arriba de 250 px, abajo de 1500 px (medí la ÚLTIMA línea)
   ni en la columna derecha de botones en la mitad de abajo.
3. **La voz no se traba, no se corta, arranca bien y se escucha.** Se corta por silencio real medido
   en la onda (nunca por los tiempos de Whisper); cada toma se nivela aparte; `islas.py` sobre cada
   voz para encontrar repeticiones y frases a medio decir; la música baja 10 dB bajo la voz.
4. **Lo que se dice, se ve.** Cuando nombra un producto, se ve ese producto; cuando dice "tienda
   online", se ve la web real en un celular con el precio marcado y el toque en "Agregar al carrito".
5. **Dinamismo pegado al texto:** golpes de zoom en palabras clave, entradas con barrido/zoom/flash,
   precio grande cuando dice el precio, palabra grande, listas que se tildan, efectos suaves. Pero los
   planos de producto duran ≥ 1 s (cortes de 0.5 s sobre zapatos "son muy rápidos").
6. **Música con energía** (116–124 BPM, nada de lo-fi), **un estilo distinto por video**, sin saturar.
7. **Datos de la web, no del guion.** Precios, % transferencia, cuotas, envío: si no coinciden, manda
   la web y se avisa. Nunca inventar un precio.
8. **Estilo de la marca, plano**: colores y tipografías de su web. Subtítulos sin fondo ni contorno.
   Nada de 3D/cromado ("horrible, irreal").
9. **Variar la edición** entre los reels de una tanda (gancho, transiciones, gráficos, música).
10. **Revisar antes de entregar:** hojas de control con guías de safe zone sobre el video TERMINADO,
    un cuadro cada 0.5 s, mirando cada uno. Transcribir el video final donde se tocó la voz.
11. **Entrega ordenada:** carpeta de la marca en el Escritorio, `Reel N - Modelo/` + `Extras/`, versiones
    viejas reemplazadas, carpeta abierta, mensaje corto con duraciones, cambios y diferencias de datos.

El detalle y el porqué de cada regla está en `references/control-calidad.md`: **leelo antes de la
primera edición** y repasá su checklist antes de cada entrega.

## Mapa de la skill

| Necesitás… | Leé |
|---|---|
| El paso a paso completo (Drive → entrega) con comandos | `references/flujo.md` |
| Todo sobre voz: varias tomas, gancho a cámara, testimonio, ElevenLabs, limpieza, verificación | `references/voz.md` |
| Dónde y cómo poner cada gráfico, recetas de animación, catálogo de recursos de otras marcas | `references/motion-graficos.md` |
| Estilos de música, ducking, efectos, bugs de audio | `references/musica-sonido.md` |
| Correcciones aprendidas + checklist de entrega | `references/control-calidad.md` |
| Instalar, Remotion en Windows, repo compartido, errores frecuentes | `references/remotion-windows.md` |
| Paleta, tipografías y condiciones de cada marca conocida | `references/marcas.md` |
| Otros formatos (encuesta, al ritmo, testimonio, vlog, gags de UI falsa, marca personal) | `references/formatos.md` |

## Scripts (`scripts/`, Python salvo stills.mjs)

Todos leen `proyecto.json` de la carpeta actual (o `PROYECTO=<ruta>`). Corré `python <script>.py` sin
argumentos para ver su ayuda.

| Script | Para qué |
|---|---|
| `drive_bajar.py` | lista (`--ver`) y baja una carpeta pública de Drive con subcarpetas y el guion (Docs → .txt) |
| `analizar.py` | hojas de contacto de cada carpeta, qué se oye en cada toma, transcripción de voces en off; `--fotos` HEIC→JPG |
| `convertir.py` | tomas 4K/HEVC → 1080x1920 60 fps (para cámara lenta suave) |
| `vo.py` | arma la voz de un reel con sus tomas: nivel por toma, pausas largas acortadas en silencio real, verificación |
| `islas.py` | transcribe isla por isla y marca ¿REPITE? / ¿CORTADA? (trabadas que Whisper esconde) |
| `hueco.py` | energía cada 10 ms entre dos tiempos: dónde está el silencio para cortar |
| `vo_cortar.py` | saca tramos de la voz (siempre desde el original) y re-sincroniza palabras |
| `limpiar_voz.py` | limpieza de tomas a cámara: ruido, compuerta suave, nivel por frase, EQ, -15 LUFS |
| `web_tienda.py` | capturas de la tienda como celular (+ cajas de nombre/precio/botón); `--buscar` URLs |
| `musica.py` | música propia por estilo, con hits y agachada bajo la voz; `--estilos` |
| `armar.py` | plan → configuración de la plantilla + música + efectos; avisa tomas cortas y gráficos encimados |
| `render_todo.py` | bundle propio, render con reintentos, -15 LUFS, verificación y copia a la entrega |
| `control.py` | hojas de control con guías: `plan` (desde el bundle), `chk` (cuadros puntuales), `final` (MP4) |
| `stills.mjs` | cuadros sueltos con renderStill (lo usa control.py) |
| `proyecto.py`, `voz_comun.py` | módulos compartidos (config, islas de habla, nivel por isla, compuerta) |

`assets/`: `plantilla/` (ReelMarca.tsx, tema.ts, entry.tsx, cfg/), `proyecto.ejemplo.json`,
`planes.ejemplo.py` (reel con voz, promos, encuesta, montaje al ritmo, comentados).

## Flujo en una mirada

```
python drive_bajar.py --ver <link>  &&  python drive_bajar.py <link>      # 1. material (¿es la marca correcta?)
# 2. web: tema.ts, logo, fotos, condiciones; web_tienda.py (mirá cada captura)
python analizar.py reel1 reel2 ... crudos/videos ; python analizar.py --fotos crudos/fotos   # 3. MIRÁ las hojas
python vo.py reel1 <tomas de voz en orden> ; python islas.py reel1                             # 4. voz + trabadas
python convertir.py reel1 <nros de las tomas elegidas>                                         # 5. tomas
# 6. planes.py: tomas ancladas a palabras, zona de cada toma, gráficos, web, cierre, estilo
python armar.py reel1 ; python render_todo.py --bundle ; python control.py plan Marca1         # 7. revisar ANTES
python render_todo.py Marca1 ... ; python control.py final out/Marca1.mp4                      # 8. render + revisar
# 9. abrir la carpeta de entrega, mandar los videos, mensaje con notas
```

## El plan de un reel (lo central de la edición)

`planes.py` describe cada reel con **anclas a palabras de la voz** (no segundos): si la voz cambia, todo
se reacomoda solo. Ejemplo mínimo (ver `assets/planes.ejemplo.py` para todo):

```python
PLANES["reel1"] = {
    "hook": {"kicker": "Primavera · Verano", "lines": ["El calzado tendencia", "que no te puede", "faltar"], "hi": 2, "to": "presento-0.1", "y": 0.56},
    "shots": [
        (0, "9693", 0.0, L),                                   # zuecos a cámara: textos abajo
        ("presento-0.1", "9675", 0.2, z("low", entra="whip")),
        ("encanta-0.1", "9652", 0.3, z("top", rate=0.6)),      # pies: textos arriba, cámara lenta
        ("48-0.1", "9675", 2.0, z("low", punch=["48"])),
        ("ingresa-0.15", "9685", 0.3, T),                      # debajo del celular
    ],
    "tags": [("presento+0.4", "encanta-0.2", "Zuecos Atenas", "Marrón · Negro", "$48.750")],
    "prices": [("48-0.1", "transferencia+0.9", "$48.750", "pagando con transferencia")],
    "web": ("ingresa-0.15", "atenas"),
    "end": {"img": "zuecos_atenas_3.jpg", "name": "Zuecos Atenas", "price": "$48.750", "old": "$65.000", "lines": [...], "cta": "mudracalzados.com"},
    "style": "nudisco",
}
```
Criterio de edición:
- una toma nueva cada 1.5–3 s, alternando plano entero / detalle / en la mano;
- cada gráfico entra en la palabra que lo justifica;
- gancho en los primeros 2–4 s sobre la toma con más fuerza;
- tienda desde "ingresá…" hasta el cierre.

## Cómo trabajar con el usuario

- Escribe en castellano rioplatense, corto y a veces en mayúsculas ("Y EL VIDEO?", "ABRILO EN
  CARPETA"): respondé igual de directo. Si pregunta "¿ya está?", decí el estado real (renderizando, X
  de Y, cuánto falta) sin adornar.
- Leé con cuidado a qué video se refiere una corrección. "Reels 2" puede ser de otra marca de la misma
  tanda: confirmalo mirando cuál tiene el problema.
- Cuando corrige algo en un video, buscá el mismo problema en TODOS los de la tanda y corregilos.
- Avisá diferencias de datos (web vs guion), productos sin página, audio con datos mal dichos.
- Descargar audios de ElevenLabs o hacer clic en "Generar" solo si lo pide. Voz: Franco.
- No borres ni reemplaces material ajeno; en el repo compartido tocá solo tu carpeta de la marca.
- Si la tarea es larga, renderizá en segundo plano y avisá avances cortos.

## Probado

El flujo completo de esta skill (voz con `vo.py`, `islas.py`, `armar.py` con todos los gráficos,
bundle propio, `control.py plan/chk/final`, render con -15 LUFS y copia a la entrega) se probó de
punta a punta sobre el Reel 6 de Mudra (oct 2026). `islas.py` detecta la trabada real del Reel 1
("…a 48.700 pesos" / "…a 48.750 pesos pagando por transferencia" → ¿REPITE?).
