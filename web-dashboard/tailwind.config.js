/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        critical:  "#DC2626",
        high:      "#EA580C",
        warning:   "#D97706",
        safe:      "#16A34A",
        info:      "#2563EB",
        bg:        "#0F172A",
        surface:   "#1E293B",
        border:    "#334155",
        "text-primary":   "#F8FAFC",
        "text-secondary": "#94A3B8",
      },
    },
  },
  plugins: [],
};
