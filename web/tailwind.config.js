/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Dark HUD / terminal palette
        bg: "#0A0C0E",
        surface: "#12161A",
        border: "#1E262D",
        accent: "#00FFCC",
        muted: "#7B8794",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
