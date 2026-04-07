import type { Config } from "tailwindcss";

export default {
  content: [
    "./components/**/*.{vue,js,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./app.vue",
  ],
  theme: {
    extend: {
      colors: {
        star: {
          blue: "#1a4e8f",
          gold: "#f5a623",
          red: "#c0392b",
          green: "#27ae60",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
