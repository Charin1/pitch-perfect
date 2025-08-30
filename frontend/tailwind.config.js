// From: frontend/tailwind.config.js
// ----------------------------------------
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        orange: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
        },
      }
    },
  },
  // The 'daisyui' plugin is great for pre-styled components like buttons and inputs
  plugins: [
    require('@tailwindcss/typography'),
    require("daisyui")
  ],
  daisyui: {
    // We can keep the default light theme for a clean look
    themes: ["light"],
  },
}