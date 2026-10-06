# Voz: voces en off, tomas a cámara, testimonios, limpieza y verificación

La voz es lo que más se nota cuando está mal. Las tres quejas que más se repitieron fueron "se traba",
"se corta / no arranca" y "habla y no se escucha". Todo lo de este archivo apunta a eso.

## Principios

1. **Cortar por la onda, no por Whisper.** Whisper dice QUÉ se dice. DÓNDE cortar lo dice la energía:
   "islas de habla" en la banda 120–4000 Hz, umbral = max(piso + 12 dB, pico − 32 dB), uniendo huecos
   < 220 ms y descartando ruiditos < 90 ms (`voz_comun.islas`). Un corte siempre cae en ≥ 60 ms de
   silencio real (+80 ms de cola).
2. **Transcribir isla por isla, sin VAD, para encontrar trabadas.** Sobre la voz entera, Whisper junta
   dos intentos de la misma frase en una sola y la repetición desaparece.
3. **Cada toma con su nivel.** Mic de cámara vs grabadora: hasta 29 dB de diferencia.
4. **No estirar ni comprimir dentro de las frases.** Solo se acortan silencios largos entre frases.
5. **Verificar siempre** el resultado transcribiéndolo y comparando contra las tomas originales.

## Casos

### Voz en off en una o varias tomas (.m4a del celular)
```
python analizar.py reel1                 # vo.json: qué dice cada toma
python vo.py reel1 toma_buena_1.m4a toma_buena_2.m4a
python islas.py reel1
```
- Si una toma tiene la frase dicha dos veces, quedate con la mejor: tramo `archivo:desde-hasta`.
- `vo.py` acorta solo silencios > 0.7 s (deja 0.30 + 0.25 s). Una voz de 25.7 s quedó en 23.9 s sin
  tocar ninguna frase.
- Si `islas.py` marca **¿REPITE?** (la isla empieza igual que la siguiente): casi siempre se borra la
  primera. **¿REPITE ADENTRO?**: una isla con la misma secuencia dos veces (se trabó sin pausa):
  `islas.py reel1 --palabras` para ver dónde, `hueco.py` para el silencio, `vo_cortar.py` para cortar.
- `vo_cortar.py` corta siempre desde la voz original guardada, así que podés repetir con otros tramos.

### Gancho hablado a cámara + voz en off
- El .MOV entra como toma de voz: `vo.py reel3 "IMG_7900.MOV:0.2-4.4" Reel_3_.m4a Reel_3_3.m4a`.
- Se le aplica `highpass + afftdn` y NO se le acortan pausas (la imagen tiene que seguir en sincro).
- En el plan, esa toma va con `sync="IMG_7900.MOV"`: armar.py calcula desde dónde mostrar el video
  para que los labios coincidan. Si la toma sincronizada no alcanza, cortala antes (armar.py avisa).

### Testimonio / habla a cámara con jump cuts (Ambos Reel 1, el que "ya estaba bien")
- Limpiá la toma: `python limpiar_voz.py IMG_6417.MOV pub/<marca>/audio/reel1_voz.wav 2.1 40.3`.
- Islas de la toma (`islas.py ruta/IMG_6417.MOV --palabras`): elegí las frases buenas, saltá
  muletillas y repeticiones; cada salto es un corte de imagen Y de audio a la vez (jump cut).
- En cada salto cambiá el encuadre (zoom 1.12 ↔ 1.02, origen 50% 30% ↔ 40%) para que el corte se vea
  intencional. Pausas apretadas (≈ 0.08 s entre islas).
- Para este formato la plantilla de la skill (una voz continua) no alcanza: armá una lista de tramos
  `{src, from, t, dur}` y reproducilos con `<Audio trimBefore volume=fade>` por tramo, con la toma en
  sincro (ver `motion-graficos.md`, "Audio por tramos").

### Tomas de recurso con gente hablando de fondo
- Todas las tomas van **muted** en la plantilla. La charla del equipo de fondo no se usa nunca.
- Si querés el audio ambiente de una toma, limpiala y verificá con `islas.py` que no haya voces.

### Voz generada (ElevenLabs)
- Voz **Franco - Business Seller**, modelo Eleven v4, estabilidad 50, similitud ~75. No la voz
  "Agustin" aunque aparezca en "Mis voces".
- Generar/descargar SOLO cuando el usuario lo pide. Si el clasificador bloquea el clic en "Generar",
  dejá el texto cargado y pedile el clic.
- Para cambiar la voz de un video ya armado sin perder la sincronía con subtítulos: encajar la voz
  nueva por tramos cortando solo en silencios; `atempo` con colchón de silencio (no rubberband sobre
  pedacitos: "suena robot"); si la voz nueva es mucho más lenta, generarla a velocidad 1.2.
- Usar la toma de ElevenLabs CONTINUA: recortar y reubicar frases hizo que "la voz se trabe".

## Limpieza (`limpiar_voz.py`)
1. noisereduce con el perfil de los silencios reales de la toma (12% más silencioso), prop 0.85.
2. Compuerta suave entre frases: -10 dB, 80 ms antes, 300 ms de cola.
3. Nivel por isla: cada frase al nivel mediano (-4 a +9 dB), rampas de 60 ms en los silencios.
4. EQ: highpass 90, lowpass 12k, -2 dB en 250 Hz, +2.5 dB en 3.5 kHz + dynaudnorm suave.
5. Compresor (-28 dB, 3:1) y nivel final -15 LUFS medido en el tramo usado, limitador 0.8.

## Voz audible sobre la música
- `musica.py` baja la base 10 dB bajo la voz y le resta la banda 1–4 kHz.
- Objetivo: voz > 20 dB sobre la música en 300 Hz–4 kHz. Si una frase igual se pierde, es la frase
  (dicha lejos del mic): nivel por isla.
- Efectos (whoosh, pop, tic) a -9 dBFS de pico: se oyen sin tapar palabras.

## Verificación final (siempre)
```
ffmpeg -ss 31 -t 9 -i out/Mudra1.mp4 -ac 1 -ar 16000 chk.wav
python -c "from faster_whisper import WhisperModel as W; m=W('large-v3',device='cpu',compute_type='int8'); print(' '.join(s.text for s in m.transcribe('chk.wav',language='es',vad_filter=False)[0]))"
```
La frase tiene que estar UNA vez, completa, sin "pe…" cortados.

## Rendimiento
- Whisper large-v3 en CPU int8: ~1–3 min por minuto de audio con la PC libre. Con la PC cargada por
  otras sesiones puede tardar mucho: usá `small` para descartar tomas mudas y `large-v3` solo para voces.
- No corras dos large-v3 a la vez (la PC se quedó sin RAM).
