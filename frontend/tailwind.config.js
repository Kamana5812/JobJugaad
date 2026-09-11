/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0F2A4A',
          dark: '#081B30'
        },
        saffron: {
          DEFAULT: '#F2802E',
          deep: '#D9660F'
        },
        green: {
          subtle: '#3F9166'
        },
        paper: '#FBFAF7',
        ink: '#1C2733',
        muted: '#5B6B7D',
        line: '#E2E6EC'
      }
    },
  },
  plugins: [],
}
