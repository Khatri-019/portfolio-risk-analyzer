/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0F0F0F",
        surface: "#1A1A1A",
        border: "#2A2A2A",
        accent: "#387ED1",
        profit: "#21B556",
        loss: "#E74C3C",
        amber: "#F59E0B",
        "text-primary": "#FFFFFF",
        "text-secondary": "#808080",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      borderRadius: {
        card: "8px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.4)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.6)",
      },
    },
  },
  plugins: [],
}
