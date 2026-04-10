const apiBase = process.env.NUXT_PUBLIC_API_BASE || "";

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

  runtimeConfig: {
    public: {
      apiBase,
    },
  },

  // Local proxy: production uses NUXT_PUBLIC_API_BASE instead.
  nitro: {
    routeRules: apiBase
      ? {}
      : {
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
