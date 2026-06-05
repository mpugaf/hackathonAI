export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'IBM Plex Sans'", 'sans-serif'],
        mono: ["'IBM Plex Mono'", 'monospace']
      },
      colors: {
        navy: '#0a1628',
        blue: '#1a3a6b',
        teal: '#00c9b1',
        'teal-lt': '#e0faf7',
        slate: '#4a5568',
        silver: '#e8edf4',
        danger: '#ef4444',
        warn: '#f59e0b',
        ok: '#10b981'
      }
    }
  },
  plugins: []
};
