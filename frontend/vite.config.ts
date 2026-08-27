// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - TanStack devtools (dev-only, first), tanstackStart, viteReact, tailwindcss, tsConfigPaths,
//     nitro (build-only using cloudflare as a default target), VITE_* env injection, @ path alias,
//     React/TanStack dedupe, error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";
// mcpPlugin() removido temporariamente para dev local no Windows — quebra em
// assertContains() por misturar separadores "/" e "\\" ao resolver routesDir.
// import { mcpPlugin } from "@lovable.dev/mcp-js/stacks/tanstack/vite";

export default defineConfig({
  vite: {
    plugins: [],
    server: {
      allowedHosts: true,
      proxy: {
        // Assets (/__l5e/...) só resolvem no storage gerenciado pela Lovable
        // em produção. Localmente, proxy para o domínio publicado.
        "/__l5e": {
          target: "https://crassusastrologo.com.br",
          changeOrigin: true,
        },
      },
    },
    preview: {
      allowedHosts: true,
    },
  },
  nitro: {
    preset: "node-server",
    compressPublicAssets: true,
    routeRules: {
      "/__l5e/**": { headers: { "cache-control": "public, max-age=31536000, immutable" } },
      "/assets/**": { headers: { "cache-control": "public, max-age=31536000, immutable" } },
      "/**/*.webp": { headers: { "cache-control": "public, max-age=31536000, immutable" } },
      "/**/*.png": { headers: { "cache-control": "public, max-age=31536000, immutable" } },
      "/**/*.css": { headers: { "cache-control": "public, max-age=31536000, immutable" } },
      "/**/*.js": { headers: { "cache-control": "public, max-age=31536000, immutable" } },
      "/**/*.svg": { headers: { "cache-control": "public, max-age=31536000, immutable" } },
      "/**/*.woff2": { headers: { "cache-control": "public, max-age=31536000, immutable" } },
    },
  },
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },
});
