/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        aws: {
          orange: '#ff9900',
          'orange-dark': '#e88a00',
          squid: '#0d1117',
          ink: '#1b2230',
          card: '#1f2937',
          border: '#374151',
          text: '#d4dae3',
          muted: '#9ca3af',
        },
      },
    },
  },
  plugins: [],
};
