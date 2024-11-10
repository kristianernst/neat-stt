import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import tailwindcss from "tailwindcss";
import { vitePlugin as remix } from "@remix-run/dev";

declare module "@remix-run/node" {
  interface Future {
    v3_singleFetch: true;
  }
}

export default defineConfig({
  plugins: [
    remix(),
    tsconfigPaths(),
  ],
  css: {
    postcss: {
      plugins: [tailwindcss],
    },
  },
});