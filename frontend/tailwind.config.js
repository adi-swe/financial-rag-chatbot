/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        serif: ["Spectral", "serif"],
      },
      colors: {
        ink: "#101223",
        glow: "#9bd4ff",
        paper: "#f8f5ef",
        ocean: "#074764",
        coral: "#f3a264",
      },
    },
  },
  plugins: [],
};
