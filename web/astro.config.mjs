import { defineConfig } from "astro/config";

// GitHub Pages serves the site of this repository under /sidestore-source/.
export default defineConfig({
  site: "https://stiven-gjekaj.github.io",
  base: "/sidestore-source",
  trailingSlash: "ignore",
});
