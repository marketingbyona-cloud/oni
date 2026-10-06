# Control de calidad y correcciones aprendidas

Cada regla de este archivo salió de una corrección real del cliente interno (Agus, agencia Genera
Impacto) sobre reels ya entregados. Están con su porqué para que se entienda la intención y se
aplique en casos nuevos, no solo en el ejemplo. Antes de entregar, recorré el checklist del final.

## Contenido
1. Producto y caras: nunca tapados
2. Safe zone de Instagram
3. Voz: que no se trabe, no se corte, se escuche
4. Ritmo y dinamismo
5. Música
6. La tienda online
7. Textos, datos y marca
8. Estilo visual (lo que NO le gusta)
9. Entrega
10. Checklist antes de entregar

---

## 1. Producto y caras: nunca tapados

- **"Algunas animaciones tapan el zapato"** y después **"el gráfico tapa el zapato… nunca tapes con
  gráfica el producto"**. Es la corrección más repetida.
  - Causa: textos a altura fija. En un plano entero caminando los pies quedan a 0.60–0.75 del alto;
    una placa a 0.585 se los tapaba.
  - Solución: en cada toma del plan se marca dónde está el producto (`zone`: top/mid/low) y los
    textos van a la zona libre. Si no alcanza, alturas propias por toma (`y={"cap": .., "chip": ..}`)
    o por elemento (`{"y": ..}`). Si en la toma no hay lugar libre de producto Y de cara, **se cambia
    la toma**, no se achica el texto.
- **Caras**: tampoco se tapan. El título del gancho sobre la cara de quien habla a cámara se mueve
  arriba de la cabeza y se achica (`size`), o se elige otra toma para el gancho.
- **"Cuando habla de un producto se ve el producto, no su cara"** (JUCA): nada de burbujas con la
  cara de la modelo; mientras se nombra un modelo, se ve el modelo (puesto, de cerca, foto de la web).
- Un precio grande o una pastilla sobre una toma donde el producto ocupa toda la pantalla: elegí
  otra toma para ese momento (la de piernas con el calzado abajo es ideal para precios arriba).

## 2. Safe zone de Instagram (1080x1920)

**"Tenés que tener en cuenta las safe zone siempre de instagram"**: había títulos a y 0.06–0.08 y
subtítulos a 0.765.
- Nada importante arriba de **250 px** (y < 0.13): barra de Reels.
- Nada importante abajo de **1500 px** (y > 0.78): usuario, copy, audio.
- En la mitad de abajo (y > ~1000) dejar libre la columna derecha de **140 px** (me gusta, comentar,
  compartir).
- Margen lateral mínimo 60 px. Subtítulos con 140 px a cada lado.
- Ojo con textos de 2 líneas: medí dónde termina la SEGUNDA línea (subtítulos a 0.722 con 2 líneas
  terminaban en 1529 px).
- `control.py` dibuja las guías verdes en todas las hojas de control.

## 3. Voz: que no se trabe, no se corte, se escuche

- **"Se corta al hablar o no arranca al principio"**:
  - un gancho grabado con el mic de la cámara sonaba 29 dB más bajo que la voz en off → cada toma se
    nivela por separado (`vo.py`, -16 LUFS);
  - el recorte de pausas era agresivo → solo se acortan silencios > 0.7 s medidos en la onda, dejando
    0.30 s después y 0.25 s antes.
- **"Reels 1 la voz en off se traba y repite, luego lo dice bien, borrá lo que dice mal"**: Whisper
  sobre la voz entera fusionó los dos intentos y no se vio. Solo apareció con `islas.py` (transcribe
  isla por isla, sin VAD). **Siempre** correr `islas.py` sobre cada voz armada y sobre cada toma con
  voz, antes de planear.
- **"La voz se traba, dice cosas del crudo que no van"** (GEMA): los tiempos de Whisper no sirven para
  cortar (fin de palabra temprano: se comía "pesos", "online"; con VAD omite muletillas como "ok,
  dale"; a veces viene corrido 0.5 s). Se corta por islas de habla en la onda.
- **"No cortes la voz para estirarla"** (JUCA): meter o sacar pausas dentro de una frase "rompe el
  audio". La voz va entera con su ritmo y la imagen se adapta a la voz.
- **"Hay momentos donde habla y no se escucha"** (Ambos): la música solo bajaba 6 dB → ahora baja
  10 dB y además se le saca la banda 1–4 kHz bajo la voz; frases dichas lejos del micrófono se nivelan
  por isla (-4 a +9 dB). La voz tiene que quedar > 20 dB sobre la música en 300 Hz–4 kHz.
- **Frases a medio decir** ("aparte, no, sí…", arranques trabados, repeticiones): se borran cortando
  en silencio real (`hueco.py` para encontrar el silencio, `vo_cortar.py` para cortar). Después de
  cortar, re-transcribir solo la unión para confirmar.
- **"Gracias." / "Subtítulos por…" al final de una transcripción** suele ser alucinación de Whisper
  sobre silencio: medí la energía antes de creerle.
- **Que nunca se la vea hablar sin sonido**: una toma a cámara usada como imagen mientras suena otra
  cosa queda rarísima. Las tomas sincronizadas usan `sync` (la imagen arranca donde arranca su audio);
  las tomas de recurso se transcriben (`analizar.py` → tomas.json) para no usar partes donde habla.
- **Voz sin ruido**: ambiente y manipulación (ropa, zapatos) se limpian (`limpiar_voz.py`); compuerta
  suave (-10 dB), no -20 (suena a corte).
- **Precios dichos mal en el audio** (dijo "cinco por ciento" y era 15%): se corta la palabra y el
  dato correcto va en pantalla. Nunca dejes un dato mal dicho.
- **Verificación final**: transcribir el video TERMINADO en la zona tocada y comparar con el guion.

## 4. Ritmo y dinamismo

- **"Ponele más dinamismo sobre lo que dice"** (Ambos): los reels quedaban planos (tomas largas,
  pausas enteras, textos quietos). Recursos aprobados, siempre pegados a la palabra:
  - golpes de zoom en palabras clave (`punch`), entradas con barrido/zoom/destello (`entra`),
  - palabra grande que salta cuando se dice (`pops`), lista que se tilda cuando enumera (`checks`),
  - números grandes en precios/rankings, pasadas al tempo de la música, efectos suaves (whoosh, pop,
    tic) en cada gráfico (`sfx.wav`).
- **"Varía la edición en cada reel, me encanta"** (JUCA): no repetir el mismo recurso de un reel al
  otro dentro de la tanda (gancho, transición, tipo de gráfico, estilo musical).
- **No acelerar los planos de producto**: cortes de 0.5 s sobre zapatos le parecieron muy rápidos.
  Mínimo ~1 s por plano de producto (salvo un montaje al ritmo buscado). Cámara lenta (0.55–0.7) en
  planos de producto queda muy bien ("más lento cuando se ve el producto", Bohemian).
- Después de cortar la voz, revisar que ninguna toma haya quedado de 0.1 s (las anclas se juntan):
  `armar.py` avisa.
- Un montaje de "varios modelos" con anclas muy juntas dejó tomas de 0.18 s: repartir las tomas a lo
  largo de la frase entera, ~0.7–1 s cada una.

## 5. Música

- **"Música más movida y mejor"**: nada de lo-fi ni R&B lento. 116–124 BPM, bombo en negras, bajo con
  groove y bombeo, hats con dinámica, fills.
- **"Hay músicas muy aburridas"**: pads quietos no. Subida + golpe en los cambios (fin del gancho,
  precios, tienda), filtro que se abre en el gancho.
- **"Variá la música, diferentes"**: en una tanda, un estilo distinto por video.
- **"En todas la música arranca saturado"**: era un bug (filtro por bloques sin estado → chisporroteo
  de ~21 Hz en el gancho; saturación con picos > 1). Ya corregido en `musica.py`. Si escribís efectos
  o filtros por bloques, SIEMPRE pasá el estado (`zi`) de un bloque al siguiente.
- Sin marimba ni palmas de ruido filtrado: le sonaban a voces de fondo.
- Música propia sintetizada (sin derechos de terceros).
- Sin música cuando lo piden (vlog "sin música").

## 6. La tienda online

- **"Te dejo el link para que cuando diga lo de la web, la muestres"** y **"a ninguno le grabaste la
  pantalla de la web"**: cada vez que la voz dice "tienda online"/"en la web", se ve la web REAL:
  captura de la página del producto en un celular bien armado (marco, isla, barras), con scroll, el
  precio con transferencia marcado y el toque en "Agregar al carrito", sobre la toma difuminada.
- La captura entra ENTERA de ancho (sin recortes), sin carteles emergentes ni botón de WhatsApp.
- Fondo detrás del celular: la toma real difuminada, no un color plano.
- Siempre una toma debajo del celular (para el difuminado).

## 7. Textos, datos y marca

- **Precios y condiciones**: los de la WEB mandan. Si el guion dice otra cosa (20% vs 25%, 3 cuotas vs
  3 y 6, envío desde $280.000 vs $200.000), usá la web y avisá la diferencia en la entrega. Si la web
  muestra montos contradictorios (dos mínimos de envío distintos), no lo uses.
- **No inventar precios**: si el reel habla de un precio que la web todavía no muestra, no lo pongas
  en pantalla (y si se dice, evaluá cortarlo y avisar).
- Precios del guion de la agencia = precio con transferencia redondeado ($29.741,50 → $29.740).
- Formato de precio: "$48.750" (punto de miles, sin decimales). `armar.py` une "48 .750" → "$48.750",
  "81 mil" → "$81.000", "25 %" → "25%" y saca "pesos".
- Nombres de producto: verificados contra la web (no adivinar: si no estás seguro, describí sin
  nombre). Corregí las transcripciones con `FIX` (zuecos, no "suecos"; la marca bien escrita;
  voseo: podés, querés, ingresá).
- **Mostrar la marca no es lo mismo que nombrarla**: en el caso "sin nombrar la marca", igual se
  muestra (no taparla).
- **Sin CTA tipo "comentá X"** cuando no lo piden (lo rechazó en la marca personal). En una encuesta
  ("¿cuál te llevás?") sí tiene sentido.
- Sin la palabra "oferta" en un lanzamiento (Bohemian). Para marcas de lujo (Arte Para Pocos): nunca
  descuentos ni urgencia falsa.
- Subtítulo de texto blanco sobre ropa blanca no se lee: sombra de color "dura" o texto de color con
  halo blanco.

## 8. Estilo visual (lo que NO le gusta)

- Subtítulos con fondo/pastilla o con contorno negro: rechazados. Van sin fondo, con sombra suave.
- Texto 3D extruido, cromados, "WordArt": **"NO, horrible, irreal"**. Si pide "más profesional" se
  mejora dentro del estilo plano de la marca, mostrando primero UN cuadro de muestra.
- Contorno en el título del vlog: "NO SIN BORDE, SOLO PASTEL COMO ESE COLOR". Igualá la referencia
  que manda, sin agregar adornos.
- Tomas de celular filmando un monitor: no; grabación de pantalla nativa.
- Emojis chicos (💸) se ven como manchas en el render: evitalos o usalos grandes.

## 9. Entrega

- Todo ordenado en una carpeta del Escritorio (o en D: con acceso directo si C: no tiene lugar):
  `MARCA\Reel N - Modelo\MARCA-ReelN-Modelo.mp4` y `Extras\`. Nombres descriptivos.
- Reemplazar las versiones viejas (no dejar v1/v2 mezcladas en la entrega).
- Abrir la carpeta al terminar ("ABRILO EN CARPETA") y mandar los videos.
- En el mensaje: duración de cada uno, qué se corrigió, y las diferencias de datos detectadas
  (web vs guion), en castellano rioplatense y corto.
- Si pide "sacalo así todo largo", no recortes duración por tu cuenta: preguntá antes de acortar un
  video que él no pidió acortar.

## 10. Checklist antes de entregar

Voz
- [ ] `islas.py` sobre cada voz armada: ninguna isla marcada ¿REPITE?/¿CORTADA? sin resolver.
- [ ] `vo.py` dice "palabras que difieren: ninguna" (o las diferencias son correcciones buscadas).
- [ ] La voz arranca en el primer segundo y ninguna toma suena más baja que otra.
- [ ] Datos dichos = datos de la web.

Imagen
- [ ] `control.py plan` antes de renderizar y `control.py final` (cada 0.5 s) sobre el MP4: ningún
      texto/placa/precio toca producto ni cara; todo dentro de la safe zone.
- [ ] Zoom (recorte) sobre cada placa dudosa antes de darla por buena.
- [ ] Ninguna toma < 0.6 s salvo montaje al ritmo; planos de producto ~1 s o más.
- [ ] El gancho se lee y no tapa lo que muestra. No queda un subtítulo "colgado" al terminar el gancho.
- [ ] La tienda aparece cuando se la nombra, entera, con precio marcado.
- [ ] El cierre no muestra cuadros negros (la última toma sigue debajo).

Audio
- [ ] -15 LUFS integrado, pico ≤ -1 dBTP (render_todo.py lo hace y lo informa).
- [ ] La música no arranca saturada ni chisporrotea; cada video de la tanda con estilo distinto.
- [ ] Efectos audibles pero sin tapar palabras.

Entrega
- [ ] 1080x1920, H.264, AAC, se abre y se reproduce entero.
- [ ] Carpeta ordenada, versiones viejas reemplazadas, carpeta abierta, mensaje con notas.
