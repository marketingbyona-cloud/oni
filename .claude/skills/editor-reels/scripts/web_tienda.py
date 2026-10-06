"""Capturas de la tienda online (como se ve en un celular) para mostrarlas en el reel.

    python web_tienda.py                      # todas las páginas de proyecto.json -> "web.paginas"
    python web_tienda.py atenas inicio        # solo esas
    python web_tienda.py --buscar "zuecos atenas"   # encuentra la URL de un producto (Tiendanube: /search/?q=)

Celular de 390 px a 2.5x (975 px de ancho). Cierra carteles (cookies, newsletter), baja hasta el
final para que carguen las imágenes, saca botones flotantes (WhatsApp) y guarda la página entera
en pub/<marca>/web/<clave>.png + <clave>.json con las cajas (px de la captura) de:
nombre (h1), precio, transferencia (texto "transferencia"), comprar ("Agregar al carrito"/"Comprar").
armar.py usa esas cajas para el scroll, la marca del precio y el toque en el botón.

Usa el Chrome que trae Remotion (chrome-headless-shell); si no está, el Chromium de Playwright.
Mirá cada .png antes de usarlo: si salió un cartel tapando, agregá su selector en web.cerrar.
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from proyecto import C, ASSETS, REMOTION  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

W = C.get("web", {})
BASE = W.get("base", "").rstrip("/")
PAGINAS = W.get("paginas", {})
CERRAR = W.get("cerrar", []) + ["text=ENTENDIDO", "text=Aceptar", "text=Entendido", ".js-modal-close", "[data-dismiss=modal]", ".modal-close", "button[aria-label=Cerrar]", "button[aria-label=Close]"]
OUT = ASSETS / "web"
OUT.mkdir(parents=True, exist_ok=True)
DPR = 2.5
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

CAJAS = """
() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 4 && r.height > 4; };
  const pick = (sel) => [...document.querySelectorAll(sel)].filter(vis);
  const box = (e) => { const r = e.getBoundingClientRect(); return {x: r.left, y: r.top + scrollY, w: r.width, h: r.height, t: (e.innerText || e.value || '').trim().slice(0, 60)}; };
  const hoja = (re) => [...document.querySelectorAll('body *')].filter(e => e.children.length === 0 && vis(e) && re.test((e.innerText || '').trim()));
  const out = {};
  const h1 = pick('h1')[0]; if (h1) out.nombre = box(h1);
  const precio = pick('.js-price-display, #price_display, [data-product-price], .product-price, .price')[0]; if (precio) out.precio = box(precio);
  const tr = hoja(/transferencia/i)[0]; if (tr) out.transferencia = box(tr);
  const btn = pick('input.js-addtocart, .js-addtocart, button[type=submit], input[type=submit], button').filter(e => /agregar|comprar/i.test((e.value || e.innerText || '')))[0]; if (btn) out.comprar = box(btn);
  return out;
}
"""


def chrome():
    for p in (REMOTION / "node_modules" / ".remotion").rglob("chrome-headless-shell.exe"):
        return str(p)
    return None


def capturar(b, clave, ruta):
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=DPR, is_mobile=True, has_touch=True, user_agent=UA)
    pg = ctx.new_page()
    pg.goto(ruta if ruta.startswith("http") else BASE + ruta, wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_timeout(3500)
    for sel in CERRAR:
        try:
            pg.click(sel, timeout=1000)
        except Exception:
            pass
    pg.keyboard.press("Escape")
    alto = pg.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < min(alto, 5200):  # baja de a poco: las imágenes cargan perezosas
        y += 400
        pg.evaluate(f"window.scrollTo(0, {y})")
        pg.wait_for_timeout(200)
    pg.evaluate("window.scrollTo(0, 0)")
    pg.wait_for_timeout(1500)
    pg.evaluate("""() => {
      for (const el of document.querySelectorAll('body *')) {
        const cs = getComputedStyle(el);
        if ((cs.position === 'fixed' || cs.position === 'sticky') && !el.closest('header') && !/head|nav/i.test(el.className)) el.remove();
      }
      for (const el of document.querySelectorAll('.modal, .js-modal, [class*=modal], [class*=popup], [id*=popup], [class*=newsletter], [class*=overlay]')) {
        if (!el.closest('header') && !el.querySelector('.js-product-form, form[action*=cart]')) { const cs = getComputedStyle(el); if (cs.position === 'fixed' || cs.position === 'absolute') el.remove(); }
      }
      document.body.classList.remove('modal-open', 'overflow-none');
      document.body.style.overflow = 'auto';
    }""")
    pg.add_style_tag(content="[class*=whatsapp], [id*=whatsapp] { display: none !important; }")
    hh = min(pg.evaluate("document.documentElement.scrollHeight"), 5200)
    pg.screenshot(path=str(OUT / f"{clave}.png"), clip={"x": 0, "y": 0, "width": 390, "height": hh}, full_page=True)
    cajas = pg.evaluate(CAJAS)
    for v in cajas.values():
        for k in ("x", "y", "w", "h"):
            v[k] = round(v[k] * DPR)
    cajas["_url"] = pg.url
    cajas["_size"] = [round(390 * DPR), round(hh * DPR)]
    json.dump(cajas, open(OUT / f"{clave}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(clave, pg.url, {k: (v["y"], v["t"]) if isinstance(v, dict) else v for k, v in cajas.items()})
    ctx.close()


def buscar(b, q):
    ctx = b.new_context(viewport={"width": 390, "height": 844}, user_agent=UA)
    pg = ctx.new_page()
    pg.goto(f"{BASE}/search/?q={q.replace(' ', '+')}", wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_timeout(2500)
    hrefs = sorted({h for h in pg.eval_on_selector_all("a[href]", "els => els.map(e => e.href)") if "/productos/" in h or "/products/" in h})
    print("\n".join(hrefs) or "nada: probá otra palabra o buscá a mano en la web")
    ctx.close()


if __name__ == "__main__":
    with sync_playwright() as p:
        exe = chrome()
        b = p.chromium.launch(executable_path=exe, args=["--disable-gpu", "--no-sandbox"]) if exe else p.chromium.launch()
        if sys.argv[1:2] == ["--buscar"]:
            buscar(b, " ".join(sys.argv[2:]))
        else:
            for clave in sys.argv[1:] or list(PAGINAS):
                capturar(b, clave, PAGINAS[clave])
        b.close()
