"""Planes de edición de cada reel (copiar a la carpeta del proyecto como planes.py).

Un plan = qué toma va en cada momento de la voz y qué gráfico aparece, anclado a PALABRAS.
armar.py lo convierte en la configuración de la plantilla (y genera música y efectos).

ANCLAS: "palabra", "palabra#2" (2da vez), "palabra-0.1" / "palabra+0.3", o segundos (0, 3.5).
        Sin tildes ni mayúsculas: "transferencia", "podes", "interes".

TOMA:  (ancla, "nro" | "reelX/nro" | "fotos/fNNNN.jpg", desde_s, {opciones})
  zone   dónde está el PRODUCTO, para poner los textos en otro lado (lo más importante del plan):
         "top" = producto abajo (pies, zapatos en el piso)  -> textos ARRIBA (0.14-0.35)
         "mid" = plano entero / persona sentada             -> textos sobre el torso (0.40-0.59)
         "low" = producto en la mano a la altura del pecho -> textos ABAJO (0.60-0.70)
         Si en esa toma ninguna zona queda libre de producto Y de cara: cambiá la toma.
  y      alturas propias de la toma cuando la zona no alcanza: y={"cap": 0.14, "chip": 0.235}
  rate   cámara lenta (0.55-0.7 en planos de producto; los clips son de 60 fps)
  zoom   [desde, hasta] empuje durante la toma (por defecto [1.0, 1.06])
  origin centro del zoom ("50% 70%" = hacia los pies)
  entra  "zoom" | "whip" | "flash": entrada con energía (va con su efecto de sonido)
  punch  ["palabra", ...]: golpe de zoom cuando se dice esa palabra (palabras clave, precios)
  sync   "IMG_7900.MOV": la toma suena en la voz (habla a cámara): labios sincronizados solos
  ritmo  True: montaje al ritmo, permite tomas < 0.6 s sin aviso

PLACA DE PRODUCTO (tags): (desde, hasta, nombre, sub|None, precio|None, {y})
PASTILLA (chips):         (desde, hasta, texto, {y, side: "left"})
PRECIO GRANDE (prices):   (desde, hasta, grande, chico, {y})     — los subtítulos se ocultan mientras está
PALABRA GRANDE (pops):    (desde, hasta, "TEXTO", {y})           — "pop" de la palabra que se dice
LISTA QUE SE TILDA (checks): (desde, hasta, título|None, [(ancla, "ítem"), ...], {y})
TIENDA EN CELULAR (web):  (ancla, "clave de web_tienda")         — desde la ancla hasta el cierre
CIERRE (end): {img, name, price, old?, nota?, lines: [...], cta}
style: estilo de música (python musica.py --estilos). UNO DISTINTO POR VIDEO en la tanda.
"""

# correcciones de los subtítulos (clave = palabra normalizada -> texto; None = no mostrar)
FIX = {
    "moodle": "Mudra", "mudra": "Mudra", "suecos": "zuecos", "atenas": "Atenas",
    "puedes": "podés", "pones": "ponés", "sabes": "sabés", "quieres": "querés", "obtienes": "obtenés",
    "ingresa": "Ingresá", "aprovecha": "aprovechá", "corre": "corré", "mira": "mirá", "presta": "prestá",
    "latinoline": "a la tienda online", "latino": "la tienda", "line": "online",
}

LINEAS_CIERRE = ["6 cuotas sin interés", "Envíos a todo el país"]
T, M, L = {"zone": "top"}, {"zone": "mid"}, {"zone": "low"}


def z(zone, **kw):
    return {"zone": zone, **kw}


PLANES = {}

# ── Reel con voz en off: producto presentado, usos, precio, tienda
PLANES["reel1"] = {
    "hook": {"kicker": "Primavera · Verano", "lines": ["El calzado tendencia", "que no te puede", "faltar"], "hi": 2, "to": "presento-0.1", "y": 0.56},
    "shots": [
        (0, "9693", 0.0, L),                                       # zuecos a cámara: gancho abajo
        ("presento-0.1", "9675", 0.2, z("low", entra="whip")),
        ("tipo-0.15", "9666", 0.4, M),
        ("encanta-0.1", "9652", 0.3, z("top", rate=0.6, zoom=[1.02, 1.1])),
        ("jean-0.1", "9686", 3.0, T),
        ("48-0.1", "9675", 2.0, z("low", punch=["48"])),
        ("ingresa-0.15", "9685", 0.3, T),                          # detrás del celular
    ],
    "tags": [("presento+0.4", "encanta-0.2", "Zuecos Atenas", "Marrón · Negro", "$48.750")],
    "chips": [("jean-0.05", "tambien-0.15", "jean + remera", {"y": 0.205})],
    "prices": [("48-0.1", "transferencia+0.9", "$48.750", "pagando con transferencia")],
    "web": ("ingresa-0.15", "atenas"),
    "end": {"img": "zuecos_atenas_3.jpg", "name": "Zuecos Atenas", "price": "$48.750", "old": "$65.000", "lines": LINEAS_CIERRE, "cta": "mudracalzados.com"},
    "style": "nudisco",
}

# ── Reel de promos: cada beneficio en un precio grande, montaje de modelos, tienda
PLANES["reel6"] = {
    "hook": {"kicker": "Mudra Calzados", "lines": ["¿Esperabas para", "renovar tus", "zapatos?"], "hi": 2, "to": "este-0.12", "y": 0.15},
    "shots": [
        (0, "9749", 0.3, T),
        ("este-0.1", "9693", 1.2, L),
        ("en-0.12", "9652", 0.2, T),
        ("ademas-0.1", "9736", 0.3, T),
        ("asi-0.1", "9677", 0.5, L),
        ("varios-0.1", "fotos/f7938.jpg", 0, z("top", zoom=[1.0, 1.08])),
        ("este#2-0.1", "fotos/f8043.jpg", 0, z("top", zoom=[1.0, 1.08])),
        ("ingresa-0.15", "9711", 0.4, M),
    ],
    "chips": [("varios-0.05", "este#2-0.15", "mocasines", {"y": 0.235}), ("este#2-0.05", "ingresa-0.2", "botas", {"y": 0.235})],
    "prices": [
        ("25-0.15", "y-0.1", "25% OFF", "pagando con transferencia"),
        ("3-0.12", "interes+0.45", "3 y 6 cuotas", "sin interés"),
    ],
    "checks": [],
    "web": ("ingresa-0.15", "inicio"),
    "end": {"img": "coleccion.jpg", "name": "Mudra Calzados", "price": "25% OFF", "lines": ["3 y 6 cuotas sin interés", "Envío gratis +$200.000"], "cta": "mudracalzados.com"},
    "style": "progressive",
}

# ── Extra sin voz (con crudos): encuesta "¿cuál te llevás?" — música + texto, tiempos en segundos
PLANES["extra1"] = {
    "vo": False, "dur": 19.4, "end_at": 19.4,
    "hook": {"kicker": "Primavera · Verano", "lines": ["¿Cuál", "te llevás?"], "hi": 1, "to": 2.4, "y": 0.58},
    "shots": [
        (0, "reel1/9677", 0.5, L),
        (2.4, "reel1/9693", 0.6, L),
        (4.9, "reel2/9702", 1.0, T),
        (14.9, "fotos/f7901.jpg", 0, z("low", zoom=[1.0, 1.08])),
    ],
    "tags": [(2.6, 4.8, "Zuecos Atenas", "Opción 1", "$48.750", {"y": 0.67})],
    "chips": [(15.0, 17.0, "comentá tu número 👇", {"y": 0.17})],
    "web": (17.0, "inicio"),
    "end": {"img": "coleccion.jpg", "name": "Colección Mudra", "price": "desde $42.000", "lines": LINEAS_CIERRE, "cta": "mudracalzados.com"},
    "style": "electropop",
}

# ── Montaje al ritmo: un corte cada 2 tiempos de la música (techhouse = 124 BPM)
_B = 60 / 124 * 2
_T0 = 4 * 60 / 124
_TOMAS = [("reel1/9675", 0.3, L), ("reel1/9652", 0.5, z("top", rate=0.6)), ("reel2/9713", 3.0, T)]
PLANES["extra3"] = {
    "vo": False, "dur": round(_T0 + len(_TOMAS) * _B + 2.4, 3), "end_at": round(_T0 + len(_TOMAS) * _B + 2.4, 3),
    "hook": {"kicker": "Lo más pedido", "lines": ["5 modelos", "que vuelan"], "hi": 1, "to": round(_T0, 3), "y": 0.6},
    "shots": [(0, "reel5/7982", 4.8, L)] + [(round(_T0 + i * _B, 3), s, f, {**x, "ritmo": True}) for i, (s, f, x) in enumerate(_TOMAS)],
    "web": (round(_T0 + len(_TOMAS) * _B, 3), "inicio"),
    "end": {"img": "coleccion.jpg", "name": "Lo más pedido", "price": "desde $42.000", "lines": LINEAS_CIERRE, "cta": "mudracalzados.com"},
    "style": "techhouse",
}
