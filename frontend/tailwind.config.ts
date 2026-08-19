import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f2f6ff",
          100: "#e6edff",
          200: "#c2d3ff",
          300: "#9db8ff",
          400: "#5f87ff",
          500: "#3a63f5",
          600: "#2a4bd6",
          700: "#213cae",
          800: "#1c3189",
          900: "#1a2c6e",
        },
        recall: {
          again: "#ef4444",
          hard: "#f59e0b",
          good: "#10b981",
          easy: "#3b82f6",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(0 0 0 / 0.04), 0 1px 3px 0 rgb(0 0 0 / 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
