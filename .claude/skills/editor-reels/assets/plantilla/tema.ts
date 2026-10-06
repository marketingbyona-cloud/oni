/**
 * Estilo de la marca (sacalo de la WEB de la marca: colores de botones/barras, tipografías, logo).
 * Es lo único que cambia de una marca a otra en la plantilla.
 *
 * Fuentes: @remotion/google-fonts/<Nombre>. Si la fuente de la marca no está en Google Fonts
 * (pasó con Onest), cargala como TTF con FontFace desde public/<marca>/fonts.
 */
import { loadFont as loadTexto } from "@remotion/google-fonts/Poppins";
import { loadFont as loadTitulo } from "@remotion/google-fonts/Italiana";

loadTexto("normal", { weights: ["400", "500", "600", "700", "800"], subsets: ["latin", "latin-ext"] });
loadTitulo("normal", { weights: ["400"], subsets: ["latin"] });

export const TEMA = {
  /** subtítulos, precios, botones */
  texto: '"Poppins", Helvetica, Arial, sans-serif',
  /** nombre del producto en placas y cierre (la del logo o la de los títulos de la web) */
  titulo: '"Italiana", Georgia, serif',
  /** palabra que suena en los subtítulos, caja del gancho, pastillas */
  acento: "#EFE9D6",
  /** texto encima del acento (oscuro si el acento es claro, blanco si es oscuro) */
  sobreAcento: "#111111",
  /** texto oscuro general */
  tinta: "#111111",
  /** subtítulo chico de las placas (color, línea) */
  sec: "#7E7F6C",
  /** precio con transferencia y la marca del precio en la web (en Tiendanube suele ser verde) */
  precio: "#2F8A2A",
  /** fondo de la placa final */
  fondoCierre: "#FFFFFF",
  /** logo (relativo a public/<marca>/); PNG transparente */
  logo: "img/logo.png",
  /** al lado del precio en la placa de producto */
  textoPrecioPlaca: "con transferencia",
  /** debajo del precio en el cierre (se puede pisar por reel con end.nota) */
  notaPrecio: "pagando con transferencia",
  /** sombra de los textos blancos sobre video (si la ropa es blanca, usá una sombra de color "dura") */
  sombra: "0 3px 16px rgba(0,0,0,.6), 0 1px 3px rgba(0,0,0,.65)",
};
