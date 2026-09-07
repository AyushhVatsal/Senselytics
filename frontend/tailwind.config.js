/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14181F",
        paper: "#FAFAF8",
        signal: {
          DEFAULT: "#E29A3E",
          dark: "#C77F26",
          light: "#F6E3C4",
        },
        slate: {
          50: "#F5F6F7",
          100: "#E9EBEE",
          200: "#DADDE2",
          300: "#C0C5CC",
          400: "#9AA1AB",
          500: "#727A87",
          600: "#565D68",
          700: "#3F444D",
          800: "#282B31",
          900: "#181A1E",
        },
        line: "#E4E1D9",
        teal: {
          DEFAULT: "#2F8F7A",
          light: "#E1F1EC",
        },
        danger: {
          DEFAULT: "#C24A3F",
          light: "#F7E6E3",
        },
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(20, 24, 31, 0.06)",
      },
    },
  },
  plugins: [],
};
