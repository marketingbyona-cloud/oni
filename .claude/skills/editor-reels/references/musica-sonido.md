# Música y sonido

La música se genera por script (`scripts/musica.py`): no tiene derechos de terceros, dura
exactamente lo que el video y se agacha sola bajo la voz. `armar.py` la llama con el estilo del plan.

## Estilos (`python musica.py --estilos`)

| Estilo | BPM | Carácter | Bueno para |
|---|---|---|---|
| nudisco | 120 | acordes stab en contratiempo, bajo de octavas, batería disco | producto con onda, moda |
| popdance | 118 | pluck arpegiado, sub-bajo, clap pop | promos, tono alegre |
| deep | 122 | keys, bajo saw, house | botas, cuero, tono más elegante |
| funky | 116 | pluck + slap bass, disco | beneficios, lo cotidiano |
| techhouse | 124 | stabs, bajo rodante, rim | montajes al ritmo, "lo más pedido" |
| afro | 120 | keys, log drum, toms y shaker | reposiciones, verano |
| electropop | 124 | supersaw brillante, sub | encuestas, juegos |
| latin | 122 | montuno de piano, tumbao, clave 3-2 | tono festivo |
| progressive | 121 | supersaw + bajo rodante, house | promos, CTA fuertes |

**Regla:** en una tanda, un estilo distinto por video. Si hay más videos que estilos, cambiá la
semilla y el tono (agregá una entrada en `STYLES` con otra progresión de `PROG`).

## Qué hace el generador (y por qué)
- Bombo en negras, bajo con bombeo (sidechain simulado), acordes que respiran, hats con dinámica,
  fill cada 8 compases: **"más movida"**.
- **Hits**: subida (riser) de 1.6 s + golpe en el fin del gancho, cada precio grande y la entrada de la
  tienda (más los `hits` extra del plan): la música acompaña los cambios.
- Gancho más liviano (sin batería completa) con **filtro que se abre** hasta el primer hit.
- **Bajo la voz**: −10 dB y −50% en la banda 1–4 kHz, con rampas de 120 ms.
- **Nivel**: medido en las partes sin voz y llevado a −16 LUFS; sin voz en todo el video, −15 LUFS.
- Fundido final de ~1.8 s; golpe al abrir el cierre.

## Bugs que ya pasaron (no repetir)
- **Chisporroteo / "arranca saturado"**: filtrar por bloques con `sosfilt` sin pasar el estado del
  filtro reinicia el filtro en cada bloque → clic cada bloque (21 Hz con bloques de 2048 a 48 kHz).
  Cualquier filtro que cambia en el tiempo: `out[i:i+B], zi = sosfilt(sos, x[i:i+B], zi=zi)`.
  El mismo bug estaba en los whoosh y risers de la librería vieja: en la skill están corregidos.
- **Saturación**: la mezcla entraba a `tanh` con picos > 1. Normalizar a 0.9 ANTES de la curva suave.
- Medición: energía > 3 kHz en el gancho (antes del primer hit) casi nula. Con el bug era 13x mayor.

## Efectos de sonido (`sfx.wav`, lo arma `armar.py`)
- whoosh (ruido con banda que barre) 0.16 s antes de cada `entra` zoom/whip y al entrar la tienda,
- pop grave en `entra: "flash"`, pop medio en precios y palabras grandes, pop agudo suave en placas y
  pastillas, tic en cada ítem de una lista,
- todo normalizado a −9 dBFS de pico: se oye sin tapar palabras.

## Mezcla final
- `render_todo.py` lleva cada video a −15 LUFS integrado con limitador (pico ≤ −1 dBTP) sin
  recodificar el video. Remotion mezcla más bajo (salía −19 LUFS).
- Extras sin voz: la música sola a −15 LUFS.

## Cuándo NO poner música
- Si lo piden ("sin música", vlog hablado). Si el audio original del video es el protagonista
  (testimonio emotivo), música muy baja o ninguna.
