module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#F9FAFB',
        primaryText: '#1A1A1A',
        dividers: '#E5E7EB',
        primaryAccent: '#6366F1',
        secondaryAccent: '#3B82F6',
        pastelPeach: '#FFD1DC',
        pastelMint: '#D1FFD6',
        pastelLavender: '#E6E6FA',
      },
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        alternative: ['Plus Jakarta Sans', 'Work Sans', 'Satoshi', 'sans-serif'],
      },
    },
  },
  plugins: [],
}; 