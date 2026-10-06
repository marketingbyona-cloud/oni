# Formatos que funcionaron (más allá del reel de producto con voz en off)

Cada uno con su receta. La plantilla de la skill cubre directo los formatos 1–4; el resto se arma con
componentes nuevos siguiendo las recetas de `motion-graficos.md`.

## 1. Reel de producto con voz en off (el estándar de las jornadas)
Gancho → presentación con placa → usos/combinaciones con pastillas → beneficios/precio grande →
"ingresá a la tienda" con la web en el celular → cierre con producto y precio. 25–50 s.

## 2. Reel de promos / beneficios
"¿Esperabas para renovar tus zapatos? Este es el momento." → un precio grande por beneficio (25% OFF,
3 y 6 cuotas, envío gratis) sobre tomas de producto abajo → montaje "varios modelos" con el nombre de
cada uno → tienda (página de inicio) → cierre con las condiciones. Con voz o solo música + texto.

## 3. Encuesta "¿Cuál te llevás?" (extra con crudos, sin voz)
Gancho de 2 líneas → 5 modelos de ~2.5 s con placa "Opción N · nombre · precio" → foto grupal con
"comentá tu número 👇" (arriba de la cabeza, no sobre los zapatos) → tienda → cierre "Colección".

## 4. "Lo más pedido" al ritmo (extra con crudos, sin voz)
Corte cada 2 tiempos de la música (`B = 60/BPM·2`), 3 tomas por modelo con su placa (la placa entra
con la toma donde no tapa), estilo techhouse 124 BPM. Las tomas llevan `ritmo=True`.

## 5. Testimonio / habla a cámara con jump cuts (Ambos Reel 1, aprobado)
Toma limpia (`limpiar_voz.py`), frases elegidas por islas, cada salto = corte de imagen y audio con
cambio de encuadre (1.12 ↔ 1.02), pausas de ~0.08 s, palabra clave con zoom fuerte + sacudón + flash,
pastillas con emoji, sello ("ERROR") con golpe de escala 2.4→0.92→1. Subtítulos de hasta 3 palabras.

## 6. Un video por crudo (Bohemian)
Un crudo (vendedor hablando, o modelo) → su propio reel corto: título del lanzamiento en el estilo de
la web, cámara lenta en el producto, placa con nombre y precio, cierre con logo.

## 7. Vlog horizontal "un día grabando contenido para N marcas" (16:9)
Título del arranque como la referencia (TikTok): letras pastel #FFFDCC en arco (SVG textPath), máximo 3
estrellitas, SIN borde; edición tipo vlog con el audio original; sin música si lo piden; usar el video
original en máxima calidad. Si el video se acortó y pregunta por qué, ofrecé la versión entera.

## 8. Arte Para Pocos: guion sobrador + gags de interfaz falsa
Voz Franco (ElevenLabs). Cada frase dispara un gag: el video se congela con ícono de pausa, rebota como
un scroll, cartel "[silencio incómodo]" con grillos, línea de escaneo a B/N, carrusel de filtros que
cae en el logo, scroll a un posteo berreta de "oferta imperdible" que se rebobina, comentario "precio??"
y "YA SABÉS.". B/N, grano, Anton blanca, logo AP arriba. Nada de 3D.

## 9. Marca personal (blog/vlog de IA)
Instrument Serif + Inter, naranja como acento, chips mono con hora/herramienta, tarjetas crema,
grabaciones de pantalla nativas (`ffmpeg -f gdigrab -framerate 30 -draw_mouse 1 -i title="<ventana>"`),
ScreenCam con cámara por keyframes y marcas. Voz Franco continua (no recortar frases).

## 10. Caso de lanzamiento "sin nombrar la marca"
La voz no nombra la marca pero la imagen la muestra (no taparla). Sin CTA "comentá X". Capturas de las
placas/landing con Playwright.

## Ideas para variar dentro de una tanda
Gancho (pregunta / dato / "3 razones" / "¡volvieron!"), transiciones (whip / zoom / flash / corte
seco), gráfico estrella (placa / lista / precio colgante / lupa / duelo), estilo musical, color del
kicker. Que dos reels seguidos no arranquen igual.
