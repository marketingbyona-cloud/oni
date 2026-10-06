# Flujo completo de una jornada de contenido (Drive -> reels entregados)

El encargo típico: "te dejo el Drive de la jornada y la web, entrá a Reel 1, uní los videos según el
guion y editalo como profesional, así con todas las carpetas; dejame todo ordenado en el Escritorio y
con Crudos armá 3 videos extras". Este archivo es la receta paso a paso. Los scripts están en
`scripts/` de la skill; corrélos desde la carpeta del proyecto (donde está `proyecto.json`).

## Contenido
0. Preparar el proyecto
1. Bajar el Drive y leer el guion
2. Estilo y datos de la marca (web)
3. Analizar el material
4. Armar las voces
5. Convertir tomas
6. Escribir los planes
7. Armar, controlar, renderizar
8. Extras con crudos
9. Entregar
10. Cambios después de la entrega

---

## 0. Preparar el proyecto

```
D:\Proyectos\<marca>\
  jornada\            <- raíz: proyecto.json, planes.py, reel1/ reel2/ crudos/ guion/ ana/ tmp/ out/
  pub\<marca>\        <- carpeta pública PROPIA (lo que la plantilla lee con staticFile)
  bundle\             <- bundle propio de Remotion
<repo remotion>\src\templates\<marca>\   <- ReelMarca.tsx, tema.ts, entry.tsx, cfg/
```
1. Copiá `assets/proyecto.ejemplo.json` a `jornada/proyecto.json` y completá: marca, prefijo,
   rutas, web (base, páginas, etiqueta del precio), entregas.
2. Copiá `assets/plantilla/*` a `<repo>/src/templates/<marca>/` y editá **solo** `tema.ts`.
3. Copiá `assets/planes.ejemplo.py` a `jornada/planes.py` (después lo reescribís).
4. Trabajá en un disco con lugar (el C: se llenó una vez con temporales de render): `tmp` del proyecto.

## 1. Bajar el Drive y leer el guion

```
python drive_bajar.py --ver <link>     # mirá la estructura primero
python drive_bajar.py <link>           # baja todo (carpetas normalizadas: reel1, reel2, crudos/...)
```
- Si la carpeta no es pública, pedí que la compartan "cualquiera con el link" (el conector de Drive
  devuelve base64 y no sirve para videos de 4K).
- **Verificá que sea la marca correcta**: una vez llegó la carpeta de otra marca con la misma estructura
  "Reel N". Mirá el guion (`guion/*.txt`) y los nombres de los productos antes de bajar 10 GB.
- Si falla alguna descarga, volvé a correr el mismo comando (saltea lo ya bajado).
- Leé el guion entero. Anotá por reel: idea, producto(s), frases clave, precios, CTA, condiciones.

## 2. Estilo y datos de la marca (web)

- Abrí la web (navegador): colores de botones/barras, tipografías (títulos y texto), logo, tono.
  Pasalo a `tema.ts`. Si la tipografía no está en Google Fonts, cargala como TTF (`FontFace`).
- Logo: PNG transparente en `pub/<marca>/img/logo.png` (si es blanco, va sobre una placa de color).
- Fotos de producto de la web para placas/cierre: `pub/<marca>/img/`.
- **Condiciones reales** (transferencia, cuotas, envío gratis): anotalas en `proyecto.json` →
  `condiciones`. La web manda sobre el guion; las diferencias se avisan en la entrega.
- Productos: nombre exacto + URL. `python web_tienda.py --buscar "zuecos atenas"` encuentra URLs en
  Tiendanube. Cargalas en `web.paginas` y capturá: `python web_tienda.py`. **Mirá cada PNG**.

## 3. Analizar el material

```
python analizar.py reel1 reel2 reel3 reel4 reel5 crudos/videos
python analizar.py --fotos crudos/fotos
```
- Mirá TODAS las hojas (`ana/<carpeta>/sheet_XX.jpg`) con Read: dónde está el producto, la cara, qué
  toma es plano entero / detalle / en la mano, cuáles tiemblan o están desenfocadas.
- `tomas.json`: qué se oye en cada toma (para encontrar tomas habladas a cámara y no usar partes de
  recurso donde habla alguien del equipo).
- `vo.json`: transcripción de las voces en off (.m4a). Cada reel suele traer varias tomas de voz:
  identificá cuál dice cada parte del guion y cuál es la toma buena de cada frase.

## 4. Armar las voces

```
python vo.py reel1 Reel_1_mudra.m4a Reel_1_2.m4a "IMG_7900.MOV:0.2-4.4"
python islas.py reel1            # OBLIGATORIO: busca trabadas y repeticiones
python hueco.py reel1 33.4 38.2  # si hay que cortar: dónde está el silencio exacto
python vo_cortar.py reel1 33.75-37.80
```
- Orden de los argumentos = orden del guion. Un gancho hablado a cámara (.MOV) va como toma con su
  tramo; después se usa con `sync` para que la imagen quede en sincro con su audio.
- Ver `voz.md` para todos los casos (tomas a cámara, testimonio con jump cuts, limpieza de ruido).

## 5. Convertir tomas

```
python convertir.py reel1 9693 9675 9666 ...     # solo las que vas a usar
python convertir.py reel1 9679:0.62              # horizontal: centro del recorte
```
- 1080x1920 a 60 fps (permite cámara lenta suave). Los originales 4K/100 fps HEVC son pesados para
  Remotion: siempre trabajá con las conversiones.

## 6. Escribir los planes (`planes.py`)

Es el trabajo de edición propiamente dicho. Por reel:
1. **Gancho** (primeros 2–4 s): la frase del guion que engancha, en 2–3 líneas, la clave en caja.
   Elegí una toma de arranque con fuerza (producto a cámara, movimiento) y ubicá el gancho donde no
   tape producto ni cara.
2. **Tomas ancladas a palabras**: cuando la voz nombra algo, se ve eso. Una toma nueva cada 1.5–3 s
   (planos de producto ≥ 1 s). Variá planos: entero → detalle → en la mano → caminando.
3. **Zona de cada toma** (`top`/`mid`/`low`): dónde está el producto. Esto decide dónde van TODOS los
   textos mientras dura la toma.
4. **Gráficos** pegados a lo que se dice: placa de producto cuando lo presenta, pastillas con datos
   (color, taco, uso), precio grande cuando dice el precio, palabra grande en la palabra fuerte,
   lista que se tilda si enumera, golpes de zoom en las palabras clave.
5. **Tienda** cuando dice "tienda online/la web": `web` desde esa palabra hasta el cierre.
6. **Cierre**: foto del producto de la web, nombre, precio (y precio de lista tachado), condiciones,
   URL.
7. **Música**: un estilo distinto por video (`python musica.py --estilos`).
Ver `motion-graficos.md` para las alturas, recetas y qué recurso usar en cada caso.

## 7. Armar, controlar, renderizar

```
python armar.py reel1 reel2 ...          # cfg + música + efectos (leé los AVISOS)
python render_todo.py --bundle           # bundle propio (cada vez que cambian cfg, plantilla o assets)
python control.py plan Mudra1            # hojas de control desde el bundle (cada 1.25 s)
python control.py chk Mudra1:345,512     # cuadros puntuales para verificar un arreglo
python render_todo.py Mudra1 Mudra2 ...  # render + -15 LUFS + copia a la entrega
python control.py final out/Mudra1.mp4   # el video terminado, cada 0.5 s: ESTA es la revisión que manda
```
- Mirá cada hoja con Read. Si algo toca producto o cara: corregí el plan (zona, `y`, otra toma),
  `armar.py`, `--bundle`, `control.py chk` del cuadro, y recién ahí renderizá.
- Render de ~30–60 s de video tarda 2–4 min por reel con la PC libre; con la PC cargada, más. Lanzá la
  tanda en segundo plano y avisá cuánto falta.
- Un render que falla por timeout se reintenta solo (3 veces).

## 8. Extras con crudos

"Con la carpeta crudos armá 3 videos extras": sin guion, sin voz (o con un audio que manden). Ideas
que funcionaron (ver `formatos.md`):
- **Encuesta** "¿Cuál te llevás?": 5 modelos numerados (placas "Opción N"), "comentá tu número 👇".
- **Beneficios**: "¿Estabas esperando para renovar tus zapatos?" + 25% OFF / cuotas / envío en precios
  grandes + montaje de modelos con su nombre + tienda.
- **Lo más pedido**: montaje al ritmo de la música (un corte cada 2 tiempos), placa con nombre y precio
  por modelo.
Plan con `"vo": False`, `"dur"` y `"end_at"` en segundos; tiempos en segundos.

## 9. Entregar

- `render_todo.py` copia cada video a `entrega/<ruta de proyecto.json "entregas">`.
- Abrí la carpeta (`explorer.exe /select,"<archivo>"`) y mandá los videos.
- Mensaje corto: qué hay (tabla video / duración), qué se corrigió y diferencias de datos detectadas.

## 10. Cambios después de la entrega

- Leé el pedido con cuidado: "4 y 5 faltan y los extras" = faltan videos; "se corta al hablar" = voz;
  "tapa el zapato" = gráficos. Si dice "reels 2" puede ser de OTRA marca de la misma tanda: confirmá
  de qué marca habla (mirando cuál reel 2 tiene ese problema) antes de tocar.
- Corregí en el plan/voz, nunca a mano en el cfg (lo pisa `armar.py`).
- Re-renderizá solo lo que cambió, reemplazá en la entrega y volvé a revisar con `control.py final`.
- Si el problema que marcó puede estar en los otros videos de la tanda, revisalos TODOS (él no va a
  marcar cada uno).
