# Copy Frameworks — PAS + AIDA

This file is the source of truth for Phase 3 (copy script generation). For each carousel in the tanda, fill the bracketed placeholders in the matching framework section using:

1. The brand voice from `brand-dna.json` (tone register, vocabulary cues, value props, compliance flags)
2. The product details from `product-images/` source pages or filename-implied context
3. The user-provided `tone` for this specific tanda

**Output target**: a single `copy-script.json` file at `brands/{brand}/carousels/{campaign}/copy-script.json`. The shape is documented in SKILL.md § Phase 3.

---

## Framework 1 — PAS (Problem, Agitate, Solution)

**Use when**: there's a clear pain point in the audience that the product solves directly. Best for utility / functional / commerce products. Stronger emotional pull than AIDA.

**Slide count**: 3 (default, no overrides in v1).

### Slide 1 — Problem

| Element | Guideline |
|---|---|
| `role` | `"Problem"` |
| `label` | Short Spanish label for the curation gallery (e.g. `"El problema"`) |
| `headline` | 4–8 words. State the pain in the audience's voice. Specific > general. **Do**: "Tu cuchillo se traba con el primer corte." **Don't**: "¿Tenés problemas con tus cuchillos?" |
| `body` | 1 sentence (≤18 words). Ground the pain in a concrete situation. Use sensory detail. |
| `visual_direction` | What the slide should *show*: a scene that visualises the problem WITHOUT showing the product yet. e.g. "Asado scene at dusk, hands attempting to cut meat with a worn-out generic knife, the asador frowning, warm fire glow, shallow DOF on the knife edge struggling." |

### Slide 2 — Agitate

| Element | Guideline |
|---|---|
| `role` | `"Agitate"` |
| `label` | e.g. `"Por qué importa"` |
| `headline` | 5–10 words. Twist the knife — make the consequence vivid. **Do**: "Y no es solo el corte: arruinás la carne." **Don't**: "Esto puede tener consecuencias negativas." |
| `body` | 1–2 sentences (≤30 words). Show the cost of NOT solving it: time wasted, prestige lost, ritual broken, family/guest experience diminished. |
| `visual_direction` | Show the consequence: a cut that went wrong, a juice puddle, a frustrated face. Same lighting as slide 1 (chain-of-reference will reinforce continuity). NEVER show the product yet. |

### Slide 3 — Solution

| Element | Guideline |
|---|---|
| `role` | `"Solution"` |
| `label` | e.g. `"La solución"` |
| `headline` | 4–7 words. Reveal the product as the answer. **Do**: "Por eso forjamos el [Product]." **Don't**: "Te presentamos [Product]." |
| `body` | 1 sentence with 1 concrete proof point (material, origin, dimension, finish). NO prices. NO % off. |
| `visual_direction` | Hero shot of the product (use the product image as primary ref). Same lighting + palette as slides 1–2 so chain-of-reference holds. Optionally include a hand or context cue (e.g., on a wooden cutting board) but the product must be the unambiguous focus. |

### PAS — do / don't

- **Do** keep the slides emotionally connected — slide 2 should answer "and so what?" from slide 1, slide 3 should answer "so what now?"
- **Do** match the brand's voice register exactly (vos for AR, tu/usted per market)
- **Do** reference product specifics from brand-dna.json verbatim — do NOT invent materials, finishes, or origin claims
- **Don't** show the product before slide 3 — chain-of-reference visual continuity depends on slide 1 establishing scene/mood, NOT product identity
- **Don't** write a slide that could stand alone — each must depend on the previous one
- **Don't** use medical/curative claims (compliance: `no_medical_claims: true`)
- **Don't** mention competitors (compliance: `no_competitor_mentions: true`) — use generic "cuchillos genéricos", "veladores plásticos", etc.

---

## Framework 2 — AIDA (Attention, Interest, Desire, Action)

**Use when**: the product needs context-setting (it's a category the audience doesn't fully understand), or when the brand voice is more aspirational/educational than problem-driven. Best for craft / premium / lifestyle products.

**Slide count**: 4 (default, no overrides in v1).

### Slide 1 — Attention

| Element | Guideline |
|---|---|
| `role` | `"Attention"` |
| `label` | e.g. `"Mirá esto"` |
| `headline` | 3–6 words. Disrupt the scroll. Use a counterintuitive claim, a surprising number, or a sensory image. **Do**: "120 horas de trabajo manual." **Don't**: "Conocé nuestro producto." |
| `body` | Optional 1-line subhead. Keep it under 12 words. |
| `visual_direction` | A bold, attention-grabbing scene. Could be macro detail, dramatic lighting, an unusual angle, or a process moment. Don't show the full product — show enough to intrigue. |

### Slide 2 — Interest

| Element | Guideline |
|---|---|
| `role` | `"Interest"` |
| `label` | e.g. `"Cómo se hace"` |
| `headline` | 5–9 words. Pivot to the *why*. **Do**: "Cada hoja se forja a fuego abierto." **Don't**: "Nuestro proceso de fabricación." |
| `body` | 1–2 sentences (≤30 words). One concrete process detail or origin fact. Educational tone. |
| `visual_direction` | Show the process or the maker: hands at work, materials, raw inputs, workshop. Same warmth + palette as slide 1. Product can appear partially. |

### Slide 3 — Desire

| Element | Guideline |
|---|---|
| `role` | `"Desire"` |
| `label` | e.g. `"En tu cocina"` |
| `headline` | 4–8 words. Show the audience the future they want. **Do**: "Tu próximo asado, otro nivel." **Don't**: "Vas a amar este producto." |
| `body` | 1 sentence painting the lifestyle outcome. Use sensory verbs (cortar, deslizar, sentir, durar). |
| `visual_direction` | Aspirational lifestyle scene with the product clearly featured: in use, in context (asado, cocina, mesa). Hero positioning. |

### Slide 4 — Action

| Element | Guideline |
|---|---|
| `role` | `"Action"` |
| `label` | e.g. `"Llevátelo"` |
| `headline` | 3–5 words. Clear, direct CTA. **Do**: "Pedilo al herrero." **Don't**: "Comprá ahora con descuento." |
| `body` | 1 line with non-monetary differentiator: "Hecho a pedido", "Numerado", "Cada pieza única", "Envío en 7 días", "Garantía de por vida" (only if brand publishes that — never invent) |
| `visual_direction` | Clean product hero against the brand's signature backdrop (palette + texture pulled from `brand-dna.json` + asset pack vocabulary). Slide-number indicator at bottom-right reads `4/4`. |

### AIDA — do / don't

- **Do** ramp emotional intensity slide-by-slide — Attention is loud, Interest is informative, Desire is sensory, Action is calm and clear
- **Do** keep one through-line: the same value prop should be the spine of all 4 slides (don't introduce 4 different selling points)
- **Don't** put the CTA before slide 4
- **Don't** use generic CTAs ("Click", "Comprá ya") — match the brand's voice exactly
- **Don't** introduce price or discount messaging anywhere (compliance: `no_pricing_on_ads`, `no_discount_messaging`)

---

---

## Framework 3 — Listicle (cover + N items + close)

**Use when**: there's a clear count of distinct points to make ("3 razones", "5 errores comunes", "4 maneras de…"). Best for educational, save-worthy content. High organic save rate.

**Slide count**: 5 (default = cover + 3 items + close).

### Slide 1 — Cover

| Element | Guideline |
|---|---|
| `role` | `"Cover"` |
| `label` | e.g. `"El listado"` |
| `headline` | 5-9 words. Number + value prop. **Do**: "3 razones por las que tu cuchillo se traba." **Don't**: "Algunas razones para…" |
| `body` | Optional 1-line teaser. Keep under 12 words. |
| `visual_direction` | Bold typographic slide. The number is the visual hook — render it large. Product can be partial or out-of-focus. |

### Slides 2-4 — Item #1, #2, #3

| Element | Guideline |
|---|---|
| `role` | `"Item N"` (e.g. `"Item 1"`) |
| `label` | e.g. `"#1"` or `"Razón uno"` |
| `headline` | 4-7 words. The point itself. Concrete, not abstract. |
| `body` | 1 sentence (≤25 words). One specific reason / example / consequence. |
| `visual_direction` | Scene that illustrates THIS specific item. Product can appear if relevant. Number indicator (1/N, 2/N) is part of the slide-indicator at bottom-right. |

### Slide 5 — Close

| Element | Guideline |
|---|---|
| `role` | `"Close"` |
| `label` | e.g. `"Por eso"` or `"Conclusión"` |
| `headline` | 4-6 words. Synthesis or CTA. |
| `body` | Non-monetary differentiator or invitation. |
| `visual_direction` | Clean brand product hero. The "I get it now" closing shot. |

### Listicle — do / don't

- **Do** match the number in the cover to the items shown ("3 razones" → exactly 3 items, not 2 or 4)
- **Do** make each item independently understandable — viewers may skip directly to slide 3
- **Don't** repeat the cover headline on every item slide — the slide indicator does the structural work

---

## Framework 4 — Before/After (3 slides)

**Use when**: the product visibly transforms a state. Best for products with a clear "before → after" — wear and tear, lighting, performance, ritual.

**Slide count**: 3.

### Slide 1 — Before

| Element | Guideline |
|---|---|
| `role` | `"Before"` |
| `label` | e.g. `"El antes"` |
| `headline` | 4-8 words. Name the broken / dim / frustrating state. **Do**: "Tu velador se quema cada año." **Don't**: "Tenés problemas con la luz?" |
| `body` | 1 sentence on the cost of the "before" state. |
| `visual_direction` | Scene of the BEFORE — broken / generic / dim / cluttered. NEVER show the brand product here. Use generic stand-ins. |

### Slide 2 — After

| Element | Guideline |
|---|---|
| `role` | `"After"` |
| `label` | e.g. `"El después"` |
| `headline` | 4-7 words. Name the fixed state. **Do**: "Esto dura 20 años." |
| `body` | 1 sentence on what changed. Concrete, sensory. |
| `visual_direction` | Hero shot of the brand product, clearly the AFTER. Same lighting/palette as slide 1 (chain of reference) so the contrast lands as a transformation, not a context switch. |

### Slide 3 — Why

| Element | Guideline |
|---|---|
| `role` | `"Why"` |
| `label` | e.g. `"Por qué"` |
| `headline` | 4-7 words. The mechanism. **Do**: "Hecho a mano. 12 horas de forja." |
| `body` | 1 specific proof point (material, origin, dimension, finish — verbatim from brand-dna). |
| `visual_direction` | Detail / process shot. Macro of the texture, hands at work, raw material. |

### Before/After — do / don't

- **Do** keep the "before" generic — never use a competitor's product
- **Do** maintain visual continuity (lighting, palette, framing) so the after feels like the SAME scene fixed, not a different scene
- **Don't** invent the "before" pain — base it on what brand-dna's voice/positioning implies the audience cares about

---

## Framework 5 — Us vs Them (4 slides)

**Use when**: the brand is positioned premium / artisanal / specialized vs a generic alternative. Differentiation is the central message.

**Slide count**: 4.

### Slide 1 — Setup

| Element | Guideline |
|---|---|
| `role` | `"Setup"` |
| `label` | e.g. `"El dilema"` |
| `headline` | 5-8 words. Pose the choice without taking sides yet. **Do**: "No todos los cuchillos son iguales." |
| `body` | 1 line framing the comparison. |
| `visual_direction` | Ambient scene. No product yet. Could be a context cue (asado, cocina) without subjects. |

### Slide 2 — Them

| Element | Guideline |
|---|---|
| `role` | `"Them"` |
| `label` | e.g. `"Los genéricos"` |
| `headline` | 4-7 words. Name the bad option WITHOUT naming a competitor brand. **Do**: "Cuchillos de fábrica" / "Veladores plásticos comunes" |
| `body` | 2-3 weak points (vague materials, mass production, short life). |
| `visual_direction` | Generic-looking product silhouette. Lower contrast, blurred, neutral. Make it visually un-special. |

### Slide 3 — Us

| Element | Guideline |
|---|---|
| `role` | `"Us"` |
| `label` | e.g. `"Nosotros"` |
| `headline` | 4-7 words. Name the brand promise. |
| `body` | 2-3 strong points (proof-based — verbatim from brand-dna). |
| `visual_direction` | Hero shot of brand product. High contrast vs slide 2. Same composition rhythm so the difference reads as quality, not random. |

### Slide 4 — Verdict

| Element | Guideline |
|---|---|
| `role` | `"Verdict"` |
| `label` | e.g. `"La elección"` |
| `headline` | 3-5 words. Tight CTA. |
| `body` | Non-monetary differentiator. |
| `visual_direction` | Clean product shot with brand mark prominent. The "decided" closing image. |

### Us vs Them — do / don't

- **Don't** name competitors (compliance: `no_competitor_mentions: true`). Use generics.
- **Do** make the visual contrast as strong as the verbal one — slide 2 should LOOK lower-quality than slide 3
- **Don't** be sneering or dismissive — the audience may have bought "them" before. Frame it as upgrade, not insult.

---

## Framework 6 — HSO (Hook + Story + Offer, 3 slides)

**Use when**: classic direct-response copy. Works for almost any product. Best when the brand has a strong origin story or a counterintuitive angle.

**Slide count**: 3.

### Slide 1 — Hook

| Element | Guideline |
|---|---|
| `role` | `"Hook"` |
| `label` | e.g. `"El gancho"` |
| `headline` | 3-7 words. Surprising statement, fact, or question. Disrupts scroll. **Do**: "120 horas de fuego por cada hoja." |
| `body` | Optional 1-line teaser (≤12 words). |
| `visual_direction` | Bold attention-grab. Macro detail, dramatic lighting, unusual angle. Don't reveal the full product. |

### Slide 2 — Story

| Element | Guideline |
|---|---|
| `role` | `"Story"` |
| `label` | e.g. `"La historia"` |
| `headline` | 5-9 words. The pivot — context for the hook. |
| `body` | 2-3 short sentences anchoring the hook in origin / process / craft. Concrete details, no abstractions. |
| `visual_direction` | Maker / process / origin shot. Hands, materials, workshop. Brand product can appear partial. |

### Slide 3 — Offer

| Element | Guideline |
|---|---|
| `role` | `"Offer"` |
| `label` | e.g. `"La oferta"` |
| `headline` | 3-5 words. Clean CTA. |
| `body` | Non-monetary differentiator (handcrafted, made-to-order, numbered, lifetime warranty — only verbatim from brand-dna). |
| `visual_direction` | Clean product hero. The "decision" frame. |

### HSO — do / don't

- **Do** make the hook surprising — if it could appear in any generic ad, it's not a hook
- **Do** let slide 2 do the heavy lifting on credibility. The hook earns attention; the story earns trust.
- **Don't** put the offer before slide 3

---

## Framework 7 — Myth / Truth (4 slides)

**Use when**: the brand needs to correct a category misconception. Educational tone. Works well for premium brands fighting "all X are the same" perception.

**Slide count**: 4.

### Slide 1 — Cover

| Element | Guideline |
|---|---|
| `role` | `"Cover"` |
| `label` | e.g. `"Mito vs realidad"` |
| `headline` | 4-7 words. Pose the category. **Do**: "Lo que pensás de los cuchillos." |
| `body` | Optional teaser. |
| `visual_direction` | Bold cover, neutral / question-marked mood. |

### Slide 2 — Myth

| Element | Guideline |
|---|---|
| `role` | `"Myth"` |
| `label` | e.g. `"El mito"` |
| `headline` | 4-7 words. A common belief, stated as if it were true. **Do**: "Más caro = mejor." |
| `body` | 1 line on why people think this. |
| `visual_direction` | Visual cue of "common wisdom" — could be a generic product shot, neutral. |

### Slide 3 — Truth

| Element | Guideline |
|---|---|
| `role` | `"Truth"` |
| `label` | e.g. `"La realidad"` |
| `headline` | 5-9 words. The correction. Concrete and brand-grounded. **Do**: "Lo que importa es cómo se forja." |
| `body` | Brand evidence — process, material, origin. |
| `visual_direction` | Brand product or process shot. Same scene language as slide 2 but reframed. |

### Slide 4 — Close

| Element | Guideline |
|---|---|
| `role` | `"Close"` |
| `label` | e.g. `"Conclusión"` |
| `headline` | 4-6 words. The takeaway / CTA. |
| `body` | Non-monetary invitation. |
| `visual_direction` | Clean brand hero. |

### Myth/Truth — do / don't

- **Do** make the myth something a friendly customer would actually say (not a strawman)
- **Don't** mock the audience for believing the myth — frame it as common-sense-but-incomplete, not stupid
- **Don't** cite stats or sources you don't have — keep it grounded in brand process / material / craft

---

## Framework 8 — Step-by-Step / How-to (5 slides)

**Use when**: the product is part of a process the audience wants to learn (afilar un cuchillo, cuidar un velador artesanal, preparar un asado). Educational + utility content.

**Slide count**: 5 (cover + 3 steps + close).

### Slide 1 — Cover

| Element | Guideline |
|---|---|
| `role` | `"Cover"` |
| `label` | e.g. `"Cómo se hace"` |
| `headline` | 5-9 words. Name the outcome and the step count. **Do**: "Cómo afilar tu cuchillo en 3 pasos." |
| `body` | Optional 1-line teaser. |
| `visual_direction` | Outcome shot — the finished thing. Inspirational. |

### Slides 2-4 — Step 1, 2, 3

| Element | Guideline |
|---|---|
| `role` | `"Step N"` |
| `label` | e.g. `"Paso 1"` |
| `headline` | 3-6 words. Imperative verb + object. **Do**: "Mojá la piedra." / "Pasá la hoja." |
| `body` | 1-2 sentences with the specific detail (angle, time, motion). |
| `visual_direction` | Scene of THAT step in progress. Hands, action, mid-motion. Same lighting / palette across all steps so the sequence reads as one tutorial. |

### Slide 5 — Result / CTA

| Element | Guideline |
|---|---|
| `role` | `"Close"` |
| `label` | e.g. `"Listo"` |
| `headline` | 3-5 words. Result confirmation + CTA. |
| `body` | Optional non-monetary next-step. |
| `visual_direction` | Clean shot of the finished result. |

### Step-by-Step — do / don't

- **Do** make each step ACTIONABLE — viewer should feel they could do it after watching
- **Do** keep step count low (3 in defaults). Long tutorials lose engagement on Instagram
- **Don't** use steps as a thinly-veiled product demo — the user should learn something they could do anyway

---

## Framework 9 — Quote / Insight (3 slides)

**Use when**: there's ONE big idea worth dwelling on. Brand thought-leadership, founder voice, philosophical positioning. Highest engagement-per-effort when done well.

**Slide count**: 3.

### Slide 1 — Setup

| Element | Guideline |
|---|---|
| `role` | `"Setup"` |
| `label` | e.g. `"Mirá esto"` |
| `headline` | 4-7 words. Ambient prelude — sets the scene without giving away the insight. |
| `body` | 1 line of context. |
| `visual_direction` | Atmospheric scene. Subject can be ambiguous. Mood is contemplative. |

### Slide 2 — Insight

| Element | Guideline |
|---|---|
| `role` | `"Insight"` |
| `label` | e.g. `"La idea"` |
| `headline` | 8-15 words. The BIG QUOTE — fills the slide. The whole design is dedicated to this single line. |
| `body` | Optional attribution (e.g. brand voice, founder, "— [Brand]"). |
| `visual_direction` | Type-driven design. The quote IS the slide. Background is minimal — solid brand color, subtle texture, or out-of-focus product. NO competing imagery. |

### Slide 3 — Why It Matters

| Element | Guideline |
|---|---|
| `role` | `"Close"` |
| `label` | e.g. `"Por eso"` |
| `headline` | 4-7 words. Bring the insight back to the brand product. |
| `body` | 1 line non-monetary CTA or invitation. |
| `visual_direction` | Clean brand shot. Quiet, confident. |

### Quote/Insight — do / don't

- **Do** earn the quote — slide 2 should feel like it took the brand a long time to arrive at that line
- **Don't** use generic motivational filler ("dare to dream", "be bold"). The insight must be specific to the brand's worldview.
- **Don't** clutter slide 2 with imagery — the quote is the whole design

---

---

## Framework 10 — Propuesta Comercial (5 slides)

**Use when**: the brand wants to communicate concrete **facilidades de compra** — the operational perks that make buying easy. Cuotas, descuento por transferencia/efectivo, envíos (gratis / tiempos / cobertura / retiro), regalos incluidos, programas de puntos, garantía extendida. This is the carousel that answers *"¿qué me conviene de comprarte?"* with operational specifics, not brand storytelling.

Best for: post-launch announcements, "ya estás por comprar — mirá lo que te incluye", periodic reminders of permanent commercial terms, and onboarding new clients to the agency's offer.

**Slide count**: 5 (cover + 3 facilidades + CTA close).

### Slide 1 — Cover

| Element | Guideline |
|---|---|
| `role` | `"Cover"` |
| `label` | e.g. `"Cómo te lo llevás"` or `"Facilidades para comprarnos"` |
| `headline` | 4-7 words. Frames that this carousel is about HOW you buy, not what you buy. **Do**: "Llevátelo fácil." / "Cómo comprarnos." / "Las 3 formas en que te ayudamos." **Don't**: "Por qué elegirnos" (eso es otro framework — Listicle / HSO). |
| `body` | Optional 1-line teaser ("Cuotas, transferencia, envío gratis y más"). |
| `visual_direction` | Bold cover with brand product as hero. Sets the tone for "vamos a desglosar las facilidades concretas". |

### Slide 2 — Pago

| Element | Guideline |
|---|---|
| `role` | `"Pago"` |
| `label` | e.g. `"Cómo pagás"` or `"Las formas de pago"` |
| `headline` | 4-8 words. The core payment facility. **Examples** (only use what the brand publishes): "Hasta 12 cuotas sin interés." / "15% off por transferencia." / "Pagás como te queda mejor." |
| `body` | 1-2 sentences with the operational detail: cuotas exactas si las publican, % de descuento por transferencia/efectivo si lo publican, métodos aceptados (tarjetas, Mercado Pago, transferencia). **Compliance**: si `compliance.no_pricing_on_ads: true` y `no_discount_messaging: true` están en TRUE → omitir números específicos y reframe direccional ("Aceptamos cuotas con todos los bancos. Descuento por transferencia."). Si el operador lifteó esos flags para esta tanda → mostrar montos/porcentajes verbatim del sitio. |
| `visual_direction` | Clean grid de íconos de medios de pago (en paleta de marca, NUNCA con prices grandes prominentes). O un detalle de manos pagando con teléfono / tarjeta. |

### Slide 3 — Envío

| Element | Guideline |
|---|---|
| `role` | `"Envío"` |
| `label` | e.g. `"Cómo te llega"` or `"El envío"` |
| `headline` | 4-8 words. The shipping facility. **Examples**: "Envío gratis a todo el país." / "En CABA, llega en 24hs." / "Retirá en el taller, sin costo." |
| `body` | 1-2 sentences con el detalle: tiempos por zona, costo / threshold de envío gratis (si publican monto, mismo criterio compliance que slide 2), opción de retiro en local, áreas cubiertas. NUNCA inventar tiempos o áreas. |
| `visual_direction` | Escena de envío: caja con el packaging de la marca, mapa de cobertura estilizado en paleta de marca, o producto en su packaging final listo para despachar. Cuidado con cliché stock-photo. |

### Slide 4 — Plus (regalo / bonus / extra)

| Element | Guideline |
|---|---|
| `role` | `"Plus"` |
| `label` | e.g. `"Te llevás más"` or `"De regalo"` or `"Tu bonus"` |
| `headline` | 4-8 words. The "extra" the brand throws in. **Examples** (use lo que la marca publique): "Te llega con [accesorio] de regalo." / "Garantía de por vida." / "Sumás puntos en cada compra." / "Sesión de asesoramiento incluida." |
| `body` | 1-2 sentences con detalle del bonus / regalo / programa. Verbatim del sitio. Si la marca no publica un "plus" claro, este slide se reframe como una facilidad secundaria (ej: devoluciones flexibles, soporte post-venta). |
| `visual_direction` | Si es regalo material → unboxing scene mostrando producto + el regalo. Si es servicio (asesoramiento, garantía) → mano + producto en contexto del servicio. Si es programa de puntos → composición tipográfica limpia con el dato en grande. |

### Slide 5 — CTA / Cierre

| Element | Guideline |
|---|---|
| `role` | `"Action"` |
| `label` | e.g. `"Llevátelo"` or `"Empezá ahora"` |
| `headline` | 3-6 words. CTA directo y calmo. **Do**: "Comprá ahora." / "Pedilo por WhatsApp." / "Vení al taller." |
| `body` | 1 line con el resumen del paquete ("Cuotas + envío + regalo, todo junto") O CTA secundario no monetario. |
| `visual_direction` | Producto hero limpio con brand mark prominente. La toma "decisión tomada" — el cierre de las 3 facilidades anteriores. |

### Propuesta Comercial — Phase 0 (compliance scoped override)

**Antes de escribir el copy del carrusel #10, hacer este check específico:**

1. Leer `brand-dna.json` flags `compliance.no_pricing_on_ads` y `no_discount_messaging`.
2. Leer `brand-dna.json` `_compliance_notes` (si existe) — frecuentemente dice algo como *"el sitio usa heavy promo (30% OFF, 25% transferencia, cuotas)"*. Eso es **señal verde** de que la marca SÍ publica esos términos.
3. Si los flags están en `true` PERO `_compliance_notes` indica que el sitio publica condiciones, o si el operador dio override explícito en el trigger prompt:
    - **Fetcheá el sitio del producto/marca** (URL provista en el trigger prompt o `brand-dna.json` `brand_info.website_url`) y **extrae los wordings verbatim**. Buscá: `"30% OFF"`, `"25% por transferencia"`, `"X cuotas sin interés"`, `"envío gratis"`, `"alta demanda"`, garantías publicadas, regalos incluidos.
    - Agregá al objeto del carrusel #10 en `copy-script.json` un campo `_compliance_override` con la fuente:
      ```json
      "_compliance_override": {
        "scoped_to": "carousel-10-propuesta-comercial",
        "source_url": "https://cuchillosdecampo.com.ar/criollo-roseta-ciervo",
        "fetched_at": "2026-04-27T14:30:00Z",
        "verbatim_excerpts": [
          "30% OFF — Promoción especial",
          "25% off por transferencia bancaria",
          "Hasta 12 cuotas sin interés con todos los bancos",
          "Envío gratis a todo el país en compras +$50.000"
        ],
        "rationale": "_compliance_notes en brand-dna indica que el sitio publica heavy promo. Override scoped solo al carrusel #10."
      }
      ```
4. Si los flags están en `true` y NO hay `_compliance_notes` que indique override, NI el operador dio override explícito → **mantenete non-monetario**: enuncia direccionalmente ("Aceptamos cuotas. Tenemos descuento por transferencia. Hacemos envíos.") sin números, y al final del copy-script.json para este carrusel agregá `"_needs_user_confirmation": "Compliance flags estrictos. ¿Querés override scoped para este carrusel? Si sí, dame URL del sitio para fetchear wordings."`.

**El override es SOLO para el carrusel #10**. Los otros 9 carruseles del set mantienen los flags brand-wide intactos (PAS, AIDA, Listicle, etc. siguen sin precios/descuentos como dictan los flags de la marca).

### Propuesta Comercial — do / don't

- **Do** sourceá CADA detalle (cuotas, %, montos de envío, regalos, programas) **verbatim del sitio de la marca** o del campo correspondiente en `brand-dna.json`. NUNCA inventar términos comerciales — incluso uno solo destruye la credibilidad de toda la tanda (per `feedback_no_fabricated_claims`).
- **Do** dejá el `_compliance_override` registrado en el copy-script.json para auditoría. Cuando el operador (o el cliente) pregunte "¿de dónde sacaste el 25%?", la respuesta está ahí.
- **Do** mantené el "what's in it for me" del cliente como el norte. Cada slide responde a una pregunta práctica: ¿cómo pago? ¿cuándo me llega? ¿qué me sumás? ¿cómo cierro la compra?
- **Don't** uses este framework para storytelling de marca — eso va en HSO. Acá hay que ser **concreto, operacional, verificable**.
- **Don't** inventes "regalo incluido", "garantía de por vida", "envío gratis", o cuotas que la marca no publique. Si tres de las cuatro facilidades faltan, el framework no aplica esta tanda — sugerí al operador usar otro framework.
- **Don't** apiles más de 1 facilidad por slide (excepto cuando son intrínsecamente combinadas, e.g. "cuotas + transferencia" en slide 2 son ambas formas de pago). Cada facilidad merece su propio momento visual.
- **Don't** hagas el slide 5 una repetición de lo que vino antes — es CTA, no recap. Una llamada a la acción concreta y propia.
- **Don't** apliques el `_compliance_override` a OTROS carruseles del set. La regla es scoped solo al #10 — los demás respetan los flags globales.

---

## Universal rules (apply to all frameworks)

### Voice + tone

- Read `brand-dna.json` `tone_of_voice` block. Use the listed adjectives + sample phrases as a reference register.
- Argentine brands: rioplatense vos (`tenés`, `comprás`, `mirá`). NOT `tienes`, `mira`.
- Match the user-provided `tone` parameter (e.g. `"warm-rioplatense"`, `"informative-premium"`) — it's an override on the brand's default voice for this specific tanda.

### Compliance (block-list before writing each slide)

- `no_pricing_on_ads: true` → never write currency amounts, "$", "AS LOW AS"
- `no_discount_messaging: true` → never write "% OFF", "SALE", "PROMO"
- `no_competitor_mentions: true` → use generics ("cuchillos comunes", "veladores plásticos")
- `no_medical_claims: true` → no "cura", "previene", "trata"
- `no_assumed_construction: true` (if set) → never claim materials/finishes the brand doesn't publish

### Voice consistency across slides

The 7 slides of a tanda (3 PAS + 4 AIDA) should sound like they were written by the same person. Same:
- Pronoun register
- Sentence rhythm
- Vocabulary palette (words drawn from the same semantic field)
- Punctuation style (trailing periods or not, em-dashes or not)

### Visual direction — what counts as good

`visual_direction` is read by the kie.ai prompt builder verbatim and prepended with:
1. Brand modifier (palette + typography + photography + don'ts)
2. Asset pack vocabulary (textures + grains + overlays available)
3. Layout pin block (from `visual-templates.md`)
4. Safe zones rule
5. Chain-of-reference instruction (slides 2..N reference slide 1)

So `visual_direction` per slide should describe ONLY what's unique about *that* slide's scene — composition, subject, mood, lighting *change* if any. Do NOT repeat brand colors, typography, or layout there. Those come from the modifier.

**Good visual_direction**: "Macro shot of the antler handle at 45° angle, fingers grazing the texture, cinematic shallow DOF, warm fire glow from the right, smoke wisps in the background out of focus."

**Bad visual_direction**: "Use the brand's color palette of brown and orange. Use Montserrat font for the headline. Make sure there's space at the top for the Instagram UI." (← all of this is in the modifier already)

### Chain-of-reference visual continuity

Slides 2..N will receive slide 1 as a 3rd visual reference to kie.ai. So:
- Slide 1's `visual_direction` should establish a scene mood that subsequent slides can build on
- Slides 2..N should describe scenes *consistent* with slide 1's lighting, palette, and texture
- Don't switch from "warm dusk asado" in slide 1 to "clinical white studio" in slide 2 — kie.ai will fight itself

---

## Adding new frameworks later (post-v1.2)

v1.2 ships with 10 frameworks (PAS, AIDA, Listicle, Before/After, Us vs Them, HSO, Myth/Truth, How-to, Quote/Insight, Propuesta Comercial). To add more in the future (e.g. Recipe, Comparison Matrix, Customer Journey, Day-in-the-Life):

1. Append a new `## Framework N — {NAME}` section here, modelled on the existing 10
2. Update the SKILL.md scope table (bumps `Carousels per tanda`)
3. No code changes needed in `generate_carousels.py` — it reads the framework name + slide list from `copy-script.json`. Multi-word framework names (with spaces or slashes) are handled by `slug_framework()` which converts them to hyphenated filename-safe form.

The skill auto-scales — N frameworks → N carousels per tanda by default.

## Subset override (per-tanda)

The default is "1 carousel per available framework" → 10 carousels for v1.2. If for a specific tanda you want fewer, the user can say in the trigger prompt:

> "Generemos carruseles para [brand], producto [X], tono [Y]. **Solo Propuesta Comercial y Listicle** para esta tanda."

Claude reads `copy-frameworks.md`, sees 10 frameworks, but only generates the 2 the user named in `copy-script.json`. The pipelines (`generate_carousels.py`, etc) iterate on whatever's in the JSON — no code path knows or cares about the framework count.
