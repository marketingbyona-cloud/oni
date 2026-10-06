import React from "react";
import { Composition, registerRoot } from "remotion";
import { ReelMarca } from "./ReelMarca";
import { CFGS } from "./cfg";

/**
 * Entrada PROPIA de la marca: el bundle solo incluye estas composiciones. Si otra sesión deja un
 * archivo roto en el repo compartido, este bundle no se entera.
 *   npx remotion bundle src/templates/<marca>/entry.tsx --public-dir=<pub propio> --out-dir=<bundle>
 * (render_todo.py --bundle lo hace)
 */
const Raiz: React.FC = () => (
  <>
    {Object.entries(CFGS).map(([id, cfg]) => (
      <Composition key={id} id={id} component={ReelMarca} durationInFrames={Math.round(cfg.total * 30)} fps={30} width={1080} height={1920} defaultProps={{ cfg }} />
    ))}
  </>
);

registerRoot(Raiz);
