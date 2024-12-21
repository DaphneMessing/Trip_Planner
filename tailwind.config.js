/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx}', // All files in 'src/app' for App Router
    './src/components/**/*.{js,ts,jsx,tsx}', // Include if you have a components folder
    './public/**/*.html', // Include static HTML files in 'public'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

