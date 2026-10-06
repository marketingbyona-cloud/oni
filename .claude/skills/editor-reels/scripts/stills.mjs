// Cuadros sueltos desde un bundle de Remotion ya armado (sin re-empaquetar), con un solo navegador.
//   node stills.mjs <repoRemotion> <bundleDir> <outDir> <compId> <cuadro> [<cuadro> ...]
// Saltea los cuadros que ya existen en outDir: los scripts qa.py/chk.py borran la carpeta antes,
// porque si no quedan cuadros de un bundle viejo y "revisás" algo que ya cambió.
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const [repo, serveUrl, outDir, id, ...frames] = process.argv.slice(2);
const require = createRequire(path.join(repo, "package.json"));
const { renderStill, selectComposition, openBrowser } = require("@remotion/renderer");
fs.mkdirSync(outDir, { recursive: true });
const browser = await openBrowser("chrome");
// timeouts largos: con videos 60 fps y la PC compartida, 30 s no alcanzan
const composition = await selectComposition({ serveUrl, id, puppeteerInstance: browser, timeoutInMilliseconds: 180000 });
for (const fr of frames.map(Number)) {
  const output = path.join(outDir, `f${String(fr).padStart(4, "0")}.jpg`);
  if (fs.existsSync(output)) continue;
  await renderStill({ serveUrl, composition, frame: fr, output, imageFormat: "jpeg", jpegQuality: 85, timeoutInMilliseconds: 180000, puppeteerInstance: browser });
  console.log("ok", output);
}
await browser.close({ silent: true });
