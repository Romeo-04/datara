export default defineNuxtConfig({
  devtools: { enabled: false },
  modules: ["@nuxtjs/tailwindcss"],

  app: {
    head: {
      title: "STARSight",
      link: [{ rel: "icon", type: "image/png", href: "/square_logo.png" }],
    },
  },

  // Fix for Nuxt 3.11 "#app-manifest" vite resolution error in dev mode
  experimental: {
    appManifest: false,
  },

  // Nitro proxy: all /api/** requests are forwarded to FastAPI on :8000
  // This works for both SSR (server-side) and client-side fetches transparently
  nitro: {
    routeRules: {
      "/api/**": { proxy: "http://localhost:8000/api/**" },
    },
  },

  tailwindcss: {
    cssPath: "~/assets/css/main.css",
  },

  typescript: {
    strict: false,
  },
});
