export default defineNuxtConfig({
  devtools: { enabled: false },
  modules: ["@nuxtjs/tailwindcss"],

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
