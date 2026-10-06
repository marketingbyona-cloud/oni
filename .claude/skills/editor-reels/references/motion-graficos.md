# Motion gráficos: catálogo, recetas y criterios

Todo lo que se dibuja encima del video. Primero los criterios (dónde y cuándo), después los
componentes de la plantilla de la skill (`assets/plantilla/ReelMarca.tsx`), después el catálogo
ampliado de recursos que se usaron en otras marcas, con los números para rehacerlos.

## Contenido
1. Criterios generales
2. Alturas por zona (la tabla que evita tapar el producto)
3. Componentes de la plantilla
4. Qué recurso usar en cada momento
5. Catálogo ampliado (otras marcas) con recetas
6. Convenciones de animación en Remotion
7. Audio dentro de Remotion

---

## 1. Criterios generales

- **Pegado a lo que se dice.** Cada gráfico entra en la palabra que lo justifica (ancla), no "cada
  tantos segundos". El precio aparece cuando dice el precio; la pastilla "taco de 10 cm" cuando dice
  el taco; el nombre del producto cuando lo presenta.
- **Nunca sobre el producto ni sobre una cara.** La altura sale de la zona de la toma activa.
- **Dentro de la safe zone** (250 px arriba, 1500 px abajo, columna derecha libre abajo).
- **Uno por vez.** Dos pastillas o una pastilla y una placa a la misma altura se pisan. armar.py avisa.
  Excepción buscada: chip "zuecos" + subtítulos en zonas distintas.
- **Subtítulos**: Poppins (o la de la marca) blanca 64 px, peso 700, SIN fondo ni contorno, sombra
  suave; la palabra que suena en el color de acento; grupos de hasta 4 palabras; se esconden cuando
  el mismo texto está en pantalla (precio, palabra grande, lista) y antes de que termine el gancho.
- **Estilo de la marca, plano.** Colores y tipografías de la web. Nada de 3D, cromado, WordArt.
- **Variedad dentro de la tanda**: no repetir el mismo gancho/transición/gráfico en todos los reels.

## 2. Alturas por zona (fracción de 1920)

| Zona de la toma | Producto | Subtítulos | Placa | Precio grande | Pastilla |
|---|---|---|---|---|---|
| `top` | abajo (pies, zapatos en el piso) | 0.14 | 0.225 | 0.225 | 0.345 |
| `mid` | plano entero, persona sentada | 0.50 | 0.585 | 0.55 | 0.40 |
| `low` | en la mano a la altura del pecho | 0.70 | 0.555 | 0.655 | 0.60 |
| con el celular (tienda) | — | 0.70 | 0.5 | 0.5 | 0.5 |

- En `mid` mirá dónde está la cara: con la persona sentada, 0.40 puede caer en la cara; usá `y`.
- Plano entero caminando: los pies van de 0.60 a 0.75 → nada entre 0.59 y 0.78 en esa toma.
- Pastilla con un subtítulo de 2 líneas arriba (0.14–0.215): pastilla a 0.235, no a 0.20.
- Título del gancho de 3 líneas + kicker ≈ 0.17 del alto: a `y` 0.15 ocupa 0.15–0.32.

## 3. Componentes de la plantilla (`ReelMarca.tsx`)

| Componente | Qué es | Receta |
|---|---|---|
| `Take` | la toma | empuje `zoom` [1, 1.06] inOut(quad) + golpe 1.05→1 en 6 cuadros; grade `contrast(1.04) saturate(1.05) brightness(1.02)`; `rate` para cámara lenta |
| `entra: "zoom"` | entrada con zoom | escala 1.28→1 y blur 10→0 en 6–8 cuadros + whoosh |
| `entra: "whip"` | barrido | escala 1.2→1, desplazamiento 110 px→0 y blur 18→0 en 6–7 cuadros + whoosh |
| `entra: "flash"` | destello | capa blanca 0.85→0 en 6 cuadros + pop grave |
| `punch` | golpe de zoom en palabra | resorte d20/s420/m0.4, alterna 1→1.14 y 1.14→1 (efecto jump cut) |
| `Shade` | sombra para leer | gradiente 0.38 arriba → 0 al 26% … 0 al 56% → 0.42 abajo |
| `Hook` | gancho | kicker en pastilla (30 px mayúscula, espaciado 2) + líneas 84 px peso 800, la línea `hi` en caja de acento; cada línea entra 4 cuadros después con back(1.6); sale en 7 cuadros hacia arriba |
| `Captions` | subtítulos | grupos ≤ 4 palabras (cortan en puntuación o pausa > 0.45 s); cada palabra entra con back(2.2) en 5 cuadros, escala 0.7→1; la que suena en acento |
| `ProductTag` | placa de producto | tarjeta blanca 0.96, radio 24, mín 470 px, a 60 px del borde; sub en mayúscula 22 px color `sec`; nombre en tipografía de títulos 66 px; precio 44 px peso 800 + "con transferencia" verde; entra deslizando 90 px |
| `InfoChip` | pastilla | acento, 38 px peso 600, radio pleno; resorte d11/s240/m0.5 |
| `PriceStamp` | precio/beneficio grande | tarjeta blanca, 110 px peso 800, nota 32 px verde; golpe de escala 1.6→0.96→1 en 9 cuadros, rotación −2° |
| `Pop` | palabra grande | caja de acento, 132 px peso 900; escala 0.4→1.12→1 en 8 cuadros, rotación −6°→−2° |
| `CheckList` | lista que se tilda | tarjeta blanca; cada ítem entra a su tiempo (back(1.8)) con círculo verde y tilde dibujado (dashoffset 24→0) + tic |
| `Phone` | tienda en celular | 520x1060, radio 74, isla, barra de estado y URL; captura con scroll por keyframes inOut(cubic); marca del precio (borde 4 px verde + etiqueta "25% OFF"); toque en "Agregar al carrito" (punto que se hunde + anillo que se expande); fondo: la toma con blur 18 y velo 0.36; sube 260 px con resorte d16/s140/m0.7 |
| `End` | cierre | fondo de la marca que se abre desde el centro (clipPath 9 cuadros), logo, foto del producto 660x590 radio 28, nombre 82 px, precio viejo tachado + precio 60 px, nota verde, condiciones en pastillas, CTA en pastilla negra; la última toma sigue 0.5 s debajo |

## 4. Qué recurso usar en cada momento

| Momento del guion | Recurso |
|---|---|
| Primeros 2–4 s | `Hook` sobre una toma con fuerza (producto a cámara, movimiento); kicker con la línea/temporada |
| "Te presento los X" | `ProductTag` con nombre, color/variante y precio; `entra: "whip"` en la toma |
| Dato corto (color, taco, uso, "cómodos") | `InfoChip` |
| Precio / descuento / cuotas / envío | `PriceStamp` (uno por beneficio) + `punch` en el número |
| Palabra fuerte ("¡VOLVIERON!", "AHORA", "2x1") | `Pop` |
| Enumeración ("primero… segundo… tercero", "3 y 6 cuotas") | `CheckList` o pastillas numeradas "1 · …" |
| "Varios modelos" / "toda la colección" | montaje rápido (0.7–1 s por toma) con pastilla del nombre de cada modelo |
| "Ingresá a la tienda online" | `web` (celular con la página real) hasta el cierre |
| Cambio de bloque del guion | `entra` en la toma (zoom/flash) + golpe de la música (hit) |
| Final | `End` con producto, precio y condiciones |

## 5. Catálogo ampliado (otras marcas) con recetas

Recursos que se usaron y gustaron en otras marcas. Rutas de referencia del repo de la agencia
(`remotion-editor/src/templates/…`), por si lo tenés; si no, las recetas alcanzan para rehacerlos.

**Subtítulos y títulos**
- *Subtítulo aprobado con sombra en capas* (JUCA, `juca/JucaReel.tsx:418`): grupo entra con resorte
  d14/s210/m0.45 (escala 0.86→1); palabra clave 1.06x en color de marca; sombra triple
  `0 .03s .08s rgba(0,0,0,.4), 0 .05s .25s rgba(0,0,0,.4), 0 .08s .7s rgba(0,0,0,.35)` (s = tamaño);
  la palabra que suena "rebota" −8% del tamaño (sin cambiar el ancho de la línea).
- *Subtítulo con blur y giro* (marca personal, `marca_ia/kit.tsx:251`): palabra entra con blur 8→0,
  escala 0.55→1 y rotación ±6° alternada.
- *Karaoke* (`app/kit.tsx:194`): toda la frase visible al 30% y cada palabra se ilumina al decirse:
  la línea no se mueve.
- *Título que se arma con la voz* (`JucaResena.tsx:187`): cada palabra sube 110% desde una máscara
  (`overflow:hidden`) cuando se dice; resorte d16/s200/m0.5.
- *Título en arco con SVG textPath* (vlog, `vlog/VlogDia.tsx:54`): `<path d="M0 y A R R 0 0 1 W y">` con
  R≈3600 y `<textPath startOffset="50%" textAnchor="middle">`; cada línea entra con back(1.8) en 8
  cuadros; color pastel #FFFDCC sin borde, sombra suave; 2–3 estrellas SVG que titilan
  (`1+0.07·sin`).
- *Subrayado tipo marcador* (marca personal): barra inclinada naranja que se dibuja (scaleX) 6–16
  cuadros después de la palabra.
- *Slam* (Arte Para Pocos, `app/kit.tsx:125`): palabra en Anton, escala 1.6→1 y blur 10→0 en 5
  cuadros con back(1.8), más un eco que crece 1→1.2 y se desvanece.

**Producto y precio**
- *Precio colgante* (GEMA, `gema/GemaReel.tsx:148`): etiqueta rotada −4° que se balancea
  `sin(f/18)·1.5°`, entra desde −10°, serif 900 132 px.
- *Badge de promo* (GEMA): escala 0.5→1 con pulso `1+0.025·sin(f/7)`, −3°.
- *Swatches de colores* (GEMA): círculos de 110 px con borde blanco 6 px que caen de a uno (4 cuadros).
- *Regla de altura* (JUCA `HeightRule`): barra de 5 px que crece al lado del taco en 16 cuadros +
  pastilla "+ altura"; *contador* 0→12 cm (`JucaResena.tsx:238`).
- *Pila de polaroids / fotos que caen* (`JucaMadeFotos.tsx:189`, Blessed Lookbook): caen desde −0.8H
  rotadas, resorte d14/s170/m0.7, flash de 2 cuadros; la última llena la pantalla y corta a video.
- *Grilla de productos con elección* (`JucaEleccion.tsx:764`): 3x3 que aparece desde el centro; marca
  "♥ MI FAVORITO" con anillo; zoom ×4.6 hacia esa tarjeta.
- *Lupa en vivo* (`JucaDetalles.tsx:117`): el mismo video dentro de un círculo 0.23W a 2.2x sobre el
  detalle, anillo blanco + color, mango a 45°.
- *Duelo "¿este o este?"* (`JucaDuelo.tsx`): dos mitades que entran de los costados en 9 cuadros, línea
  central con chip "o"; grilla numerada + "comentá tu número".
- *Checkout que se tilda* (Blessed Reel6): tarjeta de compra con "6 cuotas", "15% OFF" y barra de envío
  que se completa al llegar al mínimo.

**Transiciones y cámara**
- *Whip con blur direccional* (`app/pro.tsx:109`, `JucaLookbook.tsx:152`): SVG `feGaussianBlur
  stdDeviation="70 0" edgeMode="duplicate"`, entra en 6 cuadros, sale en 4, desplazamiento 0.35–0.45W.
- *Cortes al ritmo* (Bohemian DropV2, Sweet): `BEAT = 60/BPM`; corte cada 2 tiempos; pulso
  `1+0.018·exp(-fase·9)` en cada negra; transición de 10 cuadros centrada en el beat.
- *Cámara en mano falsa* (JUCA `handheldAt`): suma de senos en x/y/rotación con sobre-escala para que
  no se vea el borde.
- *Jump cuts de testimonio* (AmbosReel): alternar 1.12 / 1.02 de escala y origen 30%/40% en cada corte;
  en la palabra clave zoom ×1.32 con sacudón de 14 px y flash de 3 cuadros.
- *8 tipos de corte* (`ClipFinal.tsx:182`): golpe, difuminado, latigazo, negro, flash, sacudón, giro,
  glitch (4–7 cuadros).
- *Cámara lenta*: clips convertidos a 60 fps y `rate` 0.5–0.7 (no interpolar en Remotion).

**Texturas y luz** (con moderación; para marcas editoriales/lujo)
- *Grano*: SVG `feTurbulence fractalNoise`, semilla nueva cada 2 cuadros, overlay 0.07.
- *Halation*: copia del video con blur 22, contraste 2.2, `mix-blend-mode: screen` a 0.28.
- *Light leak*: dos gradientes radiales naranjas que se mueven, screen, opacidad baja.
- *B/N + grano + Anton* (Arte Para Pocos): `grayscale(1) contrast(1.28) brightness(.95)`.

**Interfaces y pantallas**
- *Celular 3D titanio* (`JucaEleccion.tsx:388`): perspectiva 2600, sube 0.55H con rotateX 26°→2.5° y
  rotateY −16°, flota `sin(t·2.1)·6`.
- *Scroll de web a pantalla completa* (`app/pro.tsx:300`): paradas (`STOPS`) con blur vertical
  proporcional a la velocidad (`min(42, v·0.09)`), cartel "ENTRÁ A LA WEB".
- *ScreenCam* (marca personal `kit.tsx:466`): grabación de pantalla con cámara por keyframes
  `[cuadro, x, y, escala]`, motion blur según velocidad, marcas naranjas.
- *Gags de interfaz falsa* (Arte Para Pocos, el formato que más gustó): pausa con ícono, cartel
  "[silencio incómodo]", escaneo a B/N, notificaciones, buscador que escribe, comentario "precio??",
  sello "YA SABÉS." — uno por frase del guion. Ver `formatos.md`.

## 6. Convenciones de animación en Remotion

```tsx
const f = (s: number) => Math.round(s * 30);                       // segundos -> cuadros
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const Seg = ({ from, to, pre = 0, children }) => (                  // un tramo entre dos segundos
  <Sequence from={f(from)} durationInFrames={Math.max(1, f(to) - f(from))} premountFor={pre}>{children}</Sequence>);
// entrada: spring({ frame, fps: 30, config: { damping: 14, stiffness: 190, mass: 0.6 } })
// salida: interpolate(frame, [dur - 7, dur], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) })
```
- Dentro de un `Sequence`, `useCurrentFrame()` es RELATIVO al comienzo del tramo. Si un componente usa
  tiempos absolutos (como `it.at`), restale el comienzo (ya falló con un cursor y una pila de
  notificaciones).
- `premountFor` 20–30 en las tomas de video (evita cuadros negros al cortar).
- Videos siempre `<OffthreadVideo muted>`; `trimBefore` (Remotion ≥ 4.0.319; antes `startFrom`).
- Cargá solo los pesos de fuente que usás (cargar todo = 48 pedidos por cuadro).
- Blur de fondo caro: para fondos fijos, pre-difuminá el clip con ffmpeg en vez de CSS blur por cuadro.
- Fuentes que no están en Google Fonts: `new FontFace(...)` + `delayRender/continueRender`.

## 7. Audio dentro de Remotion

- La plantilla usa pistas ya mezcladas: `vo.wav` + `musica.wav` (agachada bajo la voz) + `sfx.wav`.
- **Audio por tramos** (testimonios con jump cuts, voces de varias tomas sin pre-mezclar):
```tsx
const volume = (fr: number) => Math.min(interpolate(fr, [0, 2], [0, 1], clamp), interpolate(fr, [dur - 3, dur], [1, 0], clamp)) * (seg.gain ?? 1);
<Sequence from={f(seg.t)} durationInFrames={dur}><Audio src={staticFile(seg.src)} trimBefore={f(seg.from)} volume={volume} /></Sequence>
```
- Efectos: whoosh 0.16–0.22 s ANTES del corte; pop 1 cuadro después de que arranca el resorte
  (ojo y oído llegan juntos); volúmenes 0.16–0.42.
