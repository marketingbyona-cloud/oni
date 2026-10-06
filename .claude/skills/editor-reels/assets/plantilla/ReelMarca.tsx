import React from "react";
import { AbsoluteFill, Audio, Easing, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame } from "remotion";
import { TEMA } from "./tema";

/**
 * Reel de marca 1080x1920 (Instagram/TikTok) armado por armar.py desde planes.py.
 * Capas (de abajo hacia arriba): tomas -> sombra -> gancho -> placas/pastillas/precios/pops/listas
 * -> celular con la tienda -> subtítulos -> cierre. Audio: voz + música + efectos.
 *
 * Reglas que esto respeta (cada una salió de una corrección):
 *  - SAFE ZONE de Instagram: nada importante arriba de 250 px (0.13), abajo de 1500 px (0.78) ni en
 *    la columna de botones (x > 940 en la mitad de abajo). Subtítulos con 140 px de margen lateral.
 *  - NINGÚN gráfico tapa el producto ni una cara: la altura de cada texto sale de la "zona" de la toma
 *    activa (dónde está el producto), o de una altura propia (y) puesta en el plan.
 *  - Subtítulos sin fondo ni contorno: Poppins blanca con sombra suave, la palabra que suena en acento.
 *  - Los subtítulos no se muestran mientras hay un precio grande, palabra grande o lista (sería duplicado),
 *    ni antes de que termine el gancho (no queda "colgado" el final de una frase).
 */

const FPS = 30;
const f = (s: number) => Math.round(s * FPS);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export type Word = { w: string; t: number; e: number };
/** Dónde está el PRODUCTO en la toma: "top" = abajo (textos arriba), "mid" = plano entero (textos sobre
 * el torso), "low" = en la mano a la altura del pecho (textos abajo). */
export type Zone = "top" | "mid" | "low";
type Kind = "cap" | "tag" | "stamp" | "chip";
export type Shot = {
  src: string; from: number; t0: number; t1: number; rate?: number; zoom?: [number, number]; origin?: string;
  zone?: Zone; y?: Partial<Record<Kind, number>>;
  /** entrada con energía (va con whoosh/pop en sfx.wav) */
  entra?: "zoom" | "whip" | "flash";
  /** tiempos (s absolutos) de golpes de zoom: palabras clave */
  punch?: number[];
};
export type Tag = { name: string; sub?: string; price?: string; t0: number; t1: number; y?: number };
export type Chip = { text: string; t0: number; t1: number; y?: number; side?: "left" | "center" };
export type PriceCard = { big: string; small?: string; t0: number; t1: number; y?: number };
export type PopWord = { text: string; t0: number; t1: number; y?: number };
export type Checks = { title?: string | null; t0: number; t1: number; items: { text: string; at: number }[]; y?: number };
export type WebPhone = {
  t0: number; t1: number; img: string; sw: number; sh: number; url: string;
  /** [s desde t0, y de la captura arriba de la pantalla] */
  scroll: [number, number][];
  marks?: { t: number; x: number; y: number; w: number; h: number; label?: string }[];
  taps?: { t: number; x: number; y: number }[];
};
export type EndCard = { t0: number; img: string; name: string; price: string; old?: string; nota?: string; lines: string[]; cta: string };
export type ReelCfg = {
  dir: string;
  total: number;
  vo?: string;
  music: string;
  sfx?: string;
  words: Word[];
  shots: Shot[];
  hook: { lines: string[]; hi?: number; to: number; kicker?: string; y?: number; size?: number };
  tags: Tag[];
  chips: Chip[];
  prices: PriceCard[];
  pops?: PopWord[];
  checks?: Checks[];
  end: EndCard;
  captionsOff?: [number, number][];
  web?: WebPhone;
};

/** Alturas (fracción de 1920) por tipo de gráfico y zona de la toma. Probadas en calzado e indumentaria:
 *  en un plano entero caminando los pies quedan a 0.60-0.75 -> en "mid" nada baja de 0.59. */
const YZ: Record<Kind, Record<Zone, number>> = {
  cap: { top: 0.14, mid: 0.5, low: 0.7 },
  tag: { top: 0.225, mid: 0.585, low: 0.555 },
  stamp: { top: 0.225, mid: 0.55, low: 0.655 },
  chip: { top: 0.345, mid: 0.4, low: 0.6 },
};
type YAt = (kind: Kind, t: number) => number;

const Seg: React.FC<{ from: number; to: number; pre?: number; children: React.ReactNode }> = ({ from, to, pre = 0, children }) => (
  <Sequence from={f(from)} durationInFrames={Math.max(1, f(to) - f(from))} premountFor={pre}>
    {children}
  </Sequence>
);
const useIn = (at = 0, cfg = { damping: 14, stiffness: 190, mass: 0.6 }) => {
  const frame = useCurrentFrame();
  return Math.min(1.15, spring({ frame: frame - at, fps: FPS, config: cfg }));
};

/** Una toma: empuje suave + golpe de zoom al entrar (corte con ritmo), entradas y golpes en palabras clave. */
const Take: React.FC<{ s: Shot; dur: number; dir: string }> = ({ s, dur, dir }) => {
  const frame = useCurrentFrame();
  const [z0, z1] = s.zoom ?? [1.0, 1.06];
  let z = interpolate(frame, [0, dur], [z0, z1], { ...clamp, easing: Easing.inOut(Easing.quad) }) * interpolate(frame, [0, 6], [1.05, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  let tx = 0;
  let blur = 0;
  if (s.entra === "zoom") {
    z *= interpolate(frame, [0, 8], [1.28, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
    blur = interpolate(frame, [0, 6], [10, 0], clamp);
  } else if (s.entra === "whip") {
    z *= interpolate(frame, [0, 7], [1.2, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
    tx = interpolate(frame, [0, 7], [110, 0], { ...clamp, easing: Easing.out(Easing.cubic) });
    blur = interpolate(frame, [0, 6], [18, 0], clamp);
  }
  // golpes de zoom en palabras clave: alternan acercar / volver (como un jump cut), resorte rápido
  let zp = 1;
  (s.punch ?? []).forEach((p, i) => {
    const at = f(p - s.t0);
    if (frame < at) return;
    const k = spring({ frame: frame - at, fps: FPS, config: { damping: 20, stiffness: 420, mass: 0.4 } });
    const [a, b] = i % 2 === 0 ? [1, 1.14] : [1.14, 1];
    zp = a + (b - a) * k;
  });
  z *= zp;
  const flash = s.entra === "flash" ? interpolate(frame, [0, 6], [0.85, 0], clamp) : 0;
  const style: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover", filter: `contrast(1.04) saturate(1.05) brightness(1.02)${blur ? ` blur(${blur}px)` : ""}` };
  return (
    <AbsoluteFill style={{ background: "black", overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `translateX(${tx}px) scale(${z})`, transformOrigin: s.origin ?? "50% 50%" }}>
        {/\.(jpe?g|png|webp)$/i.test(s.src) ? (
          <Img src={staticFile(`${dir}${s.src}`)} style={style} />
        ) : (
          // trimBefore (Remotion >= 4.0.319; en versiones viejas se llama startFrom). Siempre muted: la voz va aparte
          <OffthreadVideo src={staticFile(`${dir}${s.src}`)} trimBefore={f(s.from)} playbackRate={s.rate ?? 1} muted style={style} />
        )}
      </AbsoluteFill>
      {flash > 0 ? <AbsoluteFill style={{ background: "white", opacity: flash }} /> : null}
    </AbsoluteFill>
  );
};

/** Sombras suaves arriba y abajo para leer texto blanco sobre cualquier toma. */
const Shade: React.FC = () => (
  <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,.38) 0%, rgba(0,0,0,0) 26%, rgba(0,0,0,0) 56%, rgba(0,0,0,.42) 100%)" }} />
);

/** Gancho (primeros 2-4 s): kicker en pastilla + título blanco grande, la línea clave en caja de acento. */
const Hook: React.FC<{ lines: string[]; hi?: number; kicker?: string; out: number; y?: number; size?: number }> = ({ lines, hi, kicker, out, y = 0.15, size = 84 }) => {
  const frame = useCurrentFrame();
  const leave = interpolate(frame, [out - 7, out], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const k = useIn(0);
  return (
    <div style={{ position: "absolute", left: 80, right: 80, top: y * 1920, textAlign: "center", opacity: 1 - leave, transform: `translateY(${-leave * 20}px)` }}>
      {kicker ? (
        <div style={{ display: "inline-block", marginBottom: 22, padding: "10px 26px", borderRadius: 999, background: TEMA.acento, color: TEMA.sobreAcento, fontFamily: TEMA.texto, fontWeight: 600, fontSize: 30, letterSpacing: 2, textTransform: "uppercase", opacity: Math.min(1, k), transform: `scale(${0.8 + 0.2 * Math.min(1, k)})` }}>
          {kicker}
        </div>
      ) : null}
      {lines.map((ln, i) => {
        const a = interpolate(frame, [3 + i * 4, 12 + i * 4], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.6)) });
        const isHi = hi === i;
        return (
          <div key={i}>
            <span style={{ display: "inline-block", margin: "4px 0", padding: isHi ? "2px 22px 8px" : 0, borderRadius: 14, background: isHi ? TEMA.acento : "transparent", color: isHi ? TEMA.sobreAcento : "white", fontFamily: TEMA.texto, fontWeight: 800, fontSize: size, lineHeight: 1.08, letterSpacing: -2, textShadow: isHi ? undefined : "0 4px 24px rgba(0,0,0,.55), 0 2px 4px rgba(0,0,0,.5)", opacity: a, transform: `translateY(${(1 - a) * 30}px) scale(${0.85 + 0.15 * a})` }}>
              {ln}
            </span>
          </div>
        );
      })}
    </div>
  );
};

/** Subtítulos palabra por palabra: grupos de hasta 4 palabras (cortan en puntuación y pausas > 0.45 s),
 * cada palabra entra con un pop y la que suena va en el color de acento. */
const Captions: React.FC<{ words: Word[]; until: number; skip: Array<[number, number]>; yAt: YAt }> = ({ words, until, skip, yAt }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  if (t >= until || skip.some(([a, b]) => t >= a && t < b)) return null;
  const chunks: Word[][] = [];
  let cur: Word[] = [];
  for (const w of words) {
    if (cur.length && w.t - cur[cur.length - 1].e > 0.45) {
      chunks.push(cur);
      cur = [];
    }
    cur.push(w);
    if (cur.length >= 4 || /[,.:!?]$/.test(w.w)) {
      chunks.push(cur);
      cur = [];
    }
  }
  if (cur.length) chunks.push(cur);
  const ci = chunks.findIndex((c, i) => {
    const nx = chunks[i + 1];
    const end = Math.min(c[c.length - 1].e + 0.35, nx ? nx[0].t - 0.02 : Infinity);
    return t >= c[0].t - 0.04 && t < end;
  });
  if (ci < 0) return null;
  return (
    <div style={{ position: "absolute", left: 140, right: 140, top: yAt("cap", t) * 1920, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 15px" }}>
      {chunks[ci].map((w, i) => {
        const fr = (w.t - 0.04) * FPS;
        if (frame < fr) return null;
        const a = interpolate(frame, [fr, fr + 5], [0, 1], { ...clamp, easing: Easing.out(Easing.back(2.2)) });
        const now = t >= w.t - 0.03 && t < w.e + 0.05;
        return (
          <span key={i} style={{ display: "inline-block", fontFamily: TEMA.texto, fontWeight: 700, fontSize: 64, lineHeight: 1.12, letterSpacing: -1, color: now ? TEMA.acento : "white", textShadow: TEMA.sombra, opacity: Math.min(1, a * 1.5), transform: `translateY(${(1 - a) * 22}px) scale(${0.7 + 0.3 * a})` }}>
            {w.w}
          </span>
        );
      })}
    </div>
  );
};

/** Placa de producto como la tienda: tarjeta blanca, nombre en la tipografía de títulos, precio por transferencia. */
const ProductTag: React.FC<{ tag: Tag; dur: number; yAt: YAt }> = ({ tag, dur, yAt }) => {
  const frame = useCurrentFrame();
  const y = tag.y ?? yAt("tag", tag.t0 + frame / FPS);
  const inn = useIn(0);
  const leave = interpolate(frame, [dur - 7, dur], [0, 1], clamp);
  return (
    <div style={{ position: "absolute", left: 60, top: y * 1920, padding: "22px 30px 24px", borderRadius: 24, background: "rgba(255,255,255,.96)", boxShadow: "0 18px 50px rgba(0,0,0,.28)", minWidth: 470, opacity: Math.min(1, inn) * (1 - leave), transform: `translateX(${(1 - Math.min(1, inn)) * -90 - leave * 40}px)` }}>
      {tag.sub ? <div style={{ fontFamily: TEMA.texto, fontWeight: 600, fontSize: 22, letterSpacing: 3, textTransform: "uppercase", color: TEMA.sec }}>{tag.sub}</div> : null}
      <div style={{ fontFamily: TEMA.titulo, fontSize: 66, lineHeight: 1.05, color: TEMA.tinta, marginTop: 2 }}>{tag.name}</div>
      {tag.price ? (
        <div style={{ marginTop: 8, display: "flex", alignItems: "baseline", gap: 12 }}>
          <span style={{ fontFamily: TEMA.texto, fontWeight: 800, fontSize: 44, color: TEMA.tinta, letterSpacing: -1 }}>{tag.price}</span>
          <span style={{ fontFamily: TEMA.texto, fontWeight: 600, fontSize: 24, color: TEMA.precio }}>{TEMA.textoPrecioPlaca}</span>
        </div>
      ) : null}
    </div>
  );
};

/** Pastilla con un dato corto (color, taco, uso, nombre del modelo). */
const InfoChip: React.FC<{ c: Chip; dur: number; yAt: YAt }> = ({ c, dur, yAt }) => {
  const frame = useCurrentFrame();
  const y = c.y ?? yAt("chip", c.t0 + frame / FPS);
  const inn = useIn(0, { damping: 11, stiffness: 240, mass: 0.5 });
  const leave = interpolate(frame, [dur - 6, dur], [0, 1], clamp);
  const center = c.side !== "left";
  return (
    <div style={{ position: "absolute", top: y * 1920, ...(center ? { left: 0, right: 0, display: "flex", justifyContent: "center" } : { left: 60 }), opacity: Math.min(1, inn) * (1 - leave), transform: `translateY(${(1 - Math.min(1, inn)) * 24}px) scale(${0.8 + 0.2 * inn})` }}>
      <div style={{ padding: "14px 30px", borderRadius: 999, background: TEMA.acento, color: TEMA.sobreAcento, fontFamily: TEMA.texto, fontWeight: 600, fontSize: 38, boxShadow: "0 12px 30px rgba(0,0,0,.3)", whiteSpace: "nowrap" }}>{c.text}</div>
    </div>
  );
};

/** Precio / beneficio grande: entra con un golpe (1.6 -> 0.96 -> 1) y una leve inclinación. */
const PriceStamp: React.FC<{ p: PriceCard; dur: number; yAt: YAt }> = ({ p, dur, yAt }) => {
  const frame = useCurrentFrame();
  const y = p.y ?? yAt("stamp", p.t0 + frame / FPS);
  const s = interpolate(frame, [0, 5, 9], [1.6, 0.96, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const o = interpolate(frame, [0, 3], [0, 1], clamp) * (1 - interpolate(frame, [dur - 6, dur], [0, 1], clamp));
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: y * 1920, display: "flex", justifyContent: "center", opacity: o }}>
      <div style={{ padding: "26px 48px 30px", borderRadius: 30, background: "rgba(255,255,255,.97)", textAlign: "center", boxShadow: "0 24px 60px rgba(0,0,0,.35)", transform: `scale(${s}) rotate(-2deg)` }}>
        <div style={{ fontFamily: TEMA.texto, fontWeight: 800, fontSize: 110, lineHeight: 1, color: TEMA.tinta, letterSpacing: -3 }}>{p.big}</div>
        {p.small ? <div style={{ marginTop: 10, fontFamily: TEMA.texto, fontWeight: 600, fontSize: 32, color: TEMA.precio }}>{p.small}</div> : null}
      </div>
    </div>
  );
};

/** Palabra grande que "salta" cuando se dice (dinamismo pegado al texto: "OFERTA", "10 cm", "2x1"). */
const Pop: React.FC<{ p: PopWord; dur: number; yAt: YAt }> = ({ p, dur, yAt }) => {
  const frame = useCurrentFrame();
  const y = p.y ?? yAt("stamp", p.t0 + frame / FPS);
  const s = interpolate(frame, [0, 4, 8], [0.4, 1.12, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const o = interpolate(frame, [0, 2], [0, 1], clamp) * (1 - interpolate(frame, [dur - 5, dur], [0, 1], clamp));
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: y * 1920, textAlign: "center", opacity: o }}>
      <span style={{ display: "inline-block", padding: "6px 30px 14px", borderRadius: 18, background: TEMA.acento, color: TEMA.sobreAcento, fontFamily: TEMA.texto, fontWeight: 900, fontSize: 132, lineHeight: 1, letterSpacing: -4, boxShadow: "0 20px 50px rgba(0,0,0,.35)", transform: `scale(${s}) rotate(${interpolate(frame, [0, 8], [-6, -2], clamp)}deg)` }}>
        {p.text}
      </span>
    </div>
  );
};

/** Lista que se tilda a medida que se enumera (cada ítem entra a su tiempo con un tic). */
const CheckList: React.FC<{ c: Checks; dur: number; yAt: YAt }> = ({ c, dur, yAt }) => {
  const frame = useCurrentFrame();
  const y = c.y ?? yAt("tag", c.t0 + frame / FPS);
  const inn = useIn(0);
  const leave = interpolate(frame, [dur - 7, dur], [0, 1], clamp);
  return (
    <div style={{ position: "absolute", left: 60, right: 160, top: y * 1920, padding: "24px 30px", borderRadius: 26, background: "rgba(255,255,255,.96)", boxShadow: "0 18px 50px rgba(0,0,0,.28)", opacity: Math.min(1, inn) * (1 - leave), transform: `translateY(${(1 - Math.min(1, inn)) * 40}px)` }}>
      {c.title ? <div style={{ fontFamily: TEMA.titulo, fontSize: 52, color: TEMA.tinta, marginBottom: 10 }}>{c.title}</div> : null}
      {c.items.map((it, i) => {
        const k = frame - f(it.at - c.t0);
        if (k < 0) return null;
        const a = interpolate(k, [0, 6], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.8)) });
        const tick = interpolate(k, [3, 10], [24, 0], clamp);
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, margin: "8px 0", opacity: a, transform: `translateX(${(1 - a) * -30}px)` }}>
            <svg width={50} height={50} viewBox="0 0 50 50">
              <circle cx={25} cy={25} r={23} fill={TEMA.precio} />
              <path d="M14 26 L22 34 L37 17" fill="none" stroke="white" strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={24} strokeDashoffset={tick} />
            </svg>
            <span style={{ fontFamily: TEMA.texto, fontWeight: 700, fontSize: 48, color: TEMA.tinta }}>{it.text}</span>
          </div>
        );
      })}
    </div>
  );
};

/**
 * La tienda en un celular: marco con isla, barra de estado y barra con la URL; la captura real baja con
 * scroll suave, se marca el precio con transferencia y se toca "Agregar al carrito". Detrás, la toma
 * difuminada (nunca color plano). La captura entra ENTERA de ancho, sin recortes. Va entre 0.14 y 0.69.
 */
const Phone: React.FC<{ o: WebPhone; end: number; dir: string }> = ({ o, end, dir }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const inn = spring({ frame, fps: FPS, config: { damping: 16, stiffness: 140, mass: 0.7 } });
  const out = interpolate(frame, [end - 6, end], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  // 520x1060: termina en 0.692 del alto y los subtítulos (0.70, hasta 2 líneas) quedan arriba de 1500 px
  const PW = 520;
  const PH = 1060;
  const B = 14;
  const SW = PW - 2 * B;
  const SH = PH - 2 * B;
  const TOP = 0.14 * 1920;
  const HEAD = 112;
  const sc = SW / o.sw;
  let y = o.scroll[0][1];
  for (let i = 0; i < o.scroll.length - 1; i++) {
    const [ta, ya] = o.scroll[i];
    const [tb, yb] = o.scroll[i + 1];
    if (t >= ta && t <= tb) y = ya + (yb - ya) * Easing.inOut(Easing.cubic)((t - ta) / Math.max(0.01, tb - ta));
    if (t > tb) y = yb;
  }
  y = Math.min(Math.max(0, y), Math.max(0, o.sh - (SH - HEAD) / sc));
  const toScreen = (px: number, py: number) => ({ x: px * sc, y: HEAD + (py - y) * sc });
  return (
    <AbsoluteFill style={{ opacity: 1 - out }}>
      <AbsoluteFill style={{ backdropFilter: `blur(${18 * inn}px)`, background: `rgba(20,20,18,${0.36 * inn})` }} />
      <div style={{ position: "absolute", left: (1080 - PW) / 2, top: TOP, width: PW, height: PH, borderRadius: 74, background: "#111", boxShadow: "0 40px 90px rgba(0,0,0,.55), inset 0 0 0 3px #2a2a2a", transform: `translateY(${(1 - inn) * 260}px) scale(${0.9 + 0.1 * inn})` }}>
        <div style={{ position: "absolute", left: B, top: B, width: SW, height: SH, borderRadius: 60, overflow: "hidden", background: "white" }}>
          <Img src={staticFile(`${dir}${o.img}`)} style={{ position: "absolute", left: 0, top: HEAD - y * sc, width: SW }} />
          {(o.marks ?? []).map((m, i) => {
            const k = interpolate(t, [m.t, m.t + 0.25], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.6)) });
            if (k <= 0) return null;
            const p0 = toScreen(m.x, m.y);
            return (
              <div key={i} style={{ position: "absolute", left: p0.x - 8, top: p0.y - 8, width: m.w * sc + 16, height: m.h * sc + 16, borderRadius: 14, border: `4px solid ${TEMA.precio}`, opacity: k, transform: `scale(${1.15 - 0.15 * k})` }}>
                {m.label ? <div style={{ position: "absolute", right: 0, top: -46, padding: "6px 14px", borderRadius: 999, background: TEMA.precio, color: "white", fontFamily: TEMA.texto, fontWeight: 700, fontSize: 22, whiteSpace: "nowrap" }}>{m.label}</div> : null}
              </div>
            );
          })}
          {(o.taps ?? []).map((tp, i) => {
            const k = interpolate(t, [tp.t, tp.t + 0.45], [0, 1], clamp);
            if (t < tp.t - 0.3 || k >= 1) return null;
            const p0 = toScreen(tp.x, tp.y);
            const near = interpolate(t, [tp.t - 0.3, tp.t], [0, 1], clamp);
            return (
              <div key={i}>
                <div style={{ position: "absolute", left: p0.x - 30, top: p0.y - 30, width: 60, height: 60, borderRadius: 30, background: "rgba(40,40,40,.28)", border: "3px solid rgba(255,255,255,.9)", opacity: near * (1 - k), transform: `scale(${1 - 0.25 * Math.sin(Math.min(1, k * 2) * Math.PI)})` }} />
                <div style={{ position: "absolute", left: p0.x - 30, top: p0.y - 30, width: 60, height: 60, borderRadius: 30, border: `4px solid ${TEMA.acento}`, opacity: 1 - k, transform: `scale(${1 + 1.6 * k})` }} />
              </div>
            );
          })}
          <div style={{ position: "absolute", left: 0, top: 0, width: SW, height: HEAD, background: "rgba(248,247,246,.97)", borderBottom: "1px solid #e4e1de" }}>
            <div style={{ position: "absolute", left: 44, top: 20, fontFamily: TEMA.texto, fontWeight: 600, fontSize: 22, color: "#111" }}>9:41</div>
            <div style={{ position: "absolute", left: SW / 2 - 62, top: 14, width: 124, height: 34, borderRadius: 17, background: "#111" }} />
            <div style={{ position: "absolute", right: 40, top: 22, display: "flex", gap: 8, alignItems: "center" }}>
              <div style={{ width: 22, height: 13, borderRadius: 3, background: "#111" }} />
              <div style={{ width: 34, height: 16, borderRadius: 5, border: "2px solid #111", position: "relative" }}>
                <div style={{ position: "absolute", left: 2, top: 2, width: 24, height: 8, borderRadius: 2, background: "#111" }} />
              </div>
            </div>
            <div style={{ position: "absolute", left: 24, right: 24, top: 58, height: 42, borderRadius: 14, background: "#ebe8e5", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, fontFamily: TEMA.texto, fontWeight: 500, fontSize: 21, color: "#333" }}>
              <span style={{ fontSize: 16 }}>🔒</span> {o.url}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Cierre: fondo de la marca que se abre del centro, logo, foto del producto de la web, precio y cómo comprar. */
const End: React.FC<{ e: EndCard; dir: string }> = ({ e, dir }) => {
  const frame = useCurrentFrame();
  const bg = interpolate(frame, [0, 9], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const logo = useIn(3);
  const img = useIn(7, { damping: 15, stiffness: 150, mass: 0.7 });
  const txt = (d: number) => interpolate(frame, [d, d + 8], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: TEMA.fondoCierre, clipPath: `inset(${(1 - bg) * 50}% 0 ${(1 - bg) * 50}% 0)` }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 262, display: "flex", justifyContent: "center", opacity: Math.min(1, logo), transform: `scale(${0.85 + 0.15 * Math.min(1, logo)})` }}>
        <Img src={staticFile(`${dir}${TEMA.logo}`)} style={{ width: 330, maxHeight: 140, objectFit: "contain" }} />
      </div>
      <div style={{ position: "absolute", left: 210, right: 210, top: 425, height: 590, borderRadius: 28, overflow: "hidden", background: "#f3f1ec", opacity: Math.min(1, img), transform: `translateY(${(1 - Math.min(1, img)) * 60}px)` }}>
        <Img src={staticFile(`${dir}img/${e.img}`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1040, textAlign: "center", opacity: txt(12) }}>
        <div style={{ fontFamily: TEMA.titulo, fontSize: 82, color: TEMA.tinta, lineHeight: 1 }}>{e.name}</div>
        <div style={{ marginTop: 14, display: "flex", justifyContent: "center", alignItems: "baseline", gap: 16 }}>
          {e.old ? <span style={{ fontFamily: TEMA.texto, fontWeight: 500, fontSize: 34, color: "#999", textDecoration: "line-through" }}>{e.old}</span> : null}
          <span style={{ fontFamily: TEMA.texto, fontWeight: 800, fontSize: 60, color: TEMA.tinta, letterSpacing: -1.5 }}>{e.price}</span>
        </div>
        <div style={{ marginTop: 2, fontFamily: TEMA.texto, fontWeight: 600, fontSize: 28, color: TEMA.precio }}>{e.nota ?? TEMA.notaPrecio}</div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1308, display: "flex", justifyContent: "center", gap: 14, opacity: txt(18) }}>
        {e.lines.map((l) => (
          <div key={l} style={{ padding: "10px 22px", borderRadius: 999, background: TEMA.acento, color: TEMA.sobreAcento, fontFamily: TEMA.texto, fontWeight: 600, fontSize: 26 }}>{l}</div>
        ))}
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1388, display: "flex", justifyContent: "center", opacity: txt(24) }}>
        <div style={{ padding: "16px 40px", borderRadius: 999, background: TEMA.tinta, color: "white", fontFamily: TEMA.texto, fontWeight: 700, fontSize: 34 }}>{e.cta}</div>
      </div>
    </AbsoluteFill>
  );
};

export const ReelMarca: React.FC<{ cfg: ReelCfg }> = ({ cfg }) => {
  const endT = cfg.end.t0;
  const dir = cfg.dir;
  const pops = cfg.pops ?? [];
  const checks = cfg.checks ?? [];
  const yAt: YAt = (kind, t) => {
    if (cfg.web && t >= cfg.web.t0 - 0.05 && t < cfg.web.t1) return kind === "cap" ? 0.7 : 0.5;
    const s = cfg.shots.find((x) => t >= x.t0 - 0.001 && t < x.t1) ?? cfg.shots[cfg.shots.length - 1];
    return s?.y?.[kind] ?? YZ[kind][s?.zone ?? "top"];
  };
  // sin subtítulos mientras el mismo texto ya está en pantalla (precio, palabra grande, lista)
  const skip: [number, number][] = [[0, cfg.hook.to], ...[...cfg.prices, ...pops, ...checks].map((p) => [p.t0, p.t1] as [number, number]), ...(cfg.captionsOff ?? [])];
  return (
    <AbsoluteFill style={{ background: "black" }}>
      {cfg.shots.map((s, i) => (
        // la última toma sigue 0.5 s debajo del cierre: sin cuadros negros mientras se abre la placa
        <Seg key={i} from={s.t0} to={s.t1 + (i < cfg.shots.length - 1 ? 0.04 : 0.5)} pre={24}>
          <Take s={s} dur={f(s.t1 - s.t0)} dir={dir} />
        </Seg>
      ))}
      <Seg from={0} to={endT}>
        <Shade />
      </Seg>
      <Seg from={0} to={cfg.hook.to}>
        <Hook lines={cfg.hook.lines} hi={cfg.hook.hi} kicker={cfg.hook.kicker} out={f(cfg.hook.to)} y={cfg.hook.y} size={cfg.hook.size} />
      </Seg>
      {cfg.tags.map((t, i) => (
        <Seg key={`t${i}`} from={t.t0} to={t.t1}>
          <ProductTag tag={t} dur={f(t.t1) - f(t.t0)} yAt={yAt} />
        </Seg>
      ))}
      {cfg.chips.map((c, i) => (
        <Seg key={`c${i}`} from={c.t0} to={c.t1}>
          <InfoChip c={c} dur={f(c.t1) - f(c.t0)} yAt={yAt} />
        </Seg>
      ))}
      {cfg.prices.map((p, i) => (
        <Seg key={`p${i}`} from={p.t0} to={p.t1}>
          <PriceStamp p={p} dur={f(p.t1) - f(p.t0)} yAt={yAt} />
        </Seg>
      ))}
      {pops.map((p, i) => (
        <Seg key={`w${i}`} from={p.t0} to={p.t1}>
          <Pop p={p} dur={f(p.t1) - f(p.t0)} yAt={yAt} />
        </Seg>
      ))}
      {checks.map((c, i) => (
        <Seg key={`k${i}`} from={c.t0} to={c.t1}>
          <CheckList c={c} dur={f(c.t1) - f(c.t0)} yAt={yAt} />
        </Seg>
      ))}
      {cfg.web ? (
        // sigue 0.3 s debajo del cierre (que se abre encima): sin un instante de toma "pelada" en el medio
        <Seg from={cfg.web.t0} to={cfg.web.t1 + 0.3}>
          <Phone o={cfg.web} end={f(cfg.web.t1 + 0.3) - f(cfg.web.t0)} dir={dir} />
        </Seg>
      ) : null}
      <Captions words={cfg.words.filter((w) => w.t >= cfg.hook.to - 0.02)} until={endT} skip={skip} yAt={yAt} />
      <Seg from={endT} to={cfg.total} pre={20}>
        <End e={cfg.end} dir={dir} />
      </Seg>
      {cfg.vo ? <Audio src={staticFile(`${dir}${cfg.vo}`)} /> : null}
      <Audio src={staticFile(`${dir}${cfg.music}`)} />
      {cfg.sfx ? <Audio src={staticFile(`${dir}${cfg.sfx}`)} /> : null}
    </AbsoluteFill>
  );
};
