/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Dark HUD / terminal palette
        bg: "#0A0C0E",
        surface: "#12161A",
        "surface-2": "#1A2129",
        border: "#1E262D",
        accent: "#00FFCC",
        "accent-2": "#E3A857",
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
