/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0fdf4",
          500: "#1db954",
          600: "#169c46",
          700: "#128c3d",
        },
      },
    },
  },
  plugins: [],
};
