/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50:'#eff6ff',100:'#dbeafe',200:'#bfdbfe',300:'#93c5fd',400:'#60a5fa',
          500:'#3b82f6',600:'#2563eb',700:'#1d4ed8',800:'#1e40af',900:'#1e3a5f',950:'#0f1f3d',
        },
        accent: { 500: '#16a34a', 600: '#15803d' },
        risk: {
          critical: '#dc2626', high: '#ea580c', medium: '#ca8a04', low: '#16a34a', none: '#6b7280',
        },
        surface: {
          900:'#0a0f1e',800:'#0f1629',700:'#162035',600:'#1e2d45',500:'#263650',400:'#2f4060',
        },
        node: {
          wellhead:'#f59e0b', pipeline:'#3b82f6', export_terminal:'#14b8a6',
          refinery:'#a855f7', storage_depot:'#64748b', port:'#06b6d4',
          distribution_hub:'#6366f1', consumer:'#9ca3af',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: { '2xs': ['0.625rem', { lineHeight: '0.875rem' }] },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      backgroundSize: { 'grid-40': '40px 40px' },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flow-right': 'flowRight 2s linear infinite',
        'glow-critical': 'glowCritical 1.5s ease-in-out infinite alternate',
        'glow-degraded': 'glowDegraded 2s ease-in-out infinite alternate',
        'spin-slow': 'spin 3s linear infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
      },
      keyframes: {
        flowRight: { '0%': { strokeDashoffset: '24' }, '100%': { strokeDashoffset: '0' } },
        glowCritical: {
          from: { boxShadow: '0 0 4px #dc2626, 0 0 8px #dc262640' },
          to:   { boxShadow: '0 0 8px #dc2626, 0 0 20px #dc262660' },
        },
        glowDegraded: {
          from: { boxShadow: '0 0 4px #ca8a04, 0 0 8px #ca8a0440' },
          to:   { boxShadow: '0 0 8px #ca8a04, 0 0 16px #ca8a0460' },
        },
        fadeIn: { from: { opacity: '0', transform: 'translateY(4px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        slideInRight: { from: { opacity: '0', transform: 'translateX(20px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
      },
      boxShadow: {
        'glow-primary': '0 0 20px rgba(37, 99, 235, 0.3)',
        'glow-accent': '0 0 20px rgba(22, 163, 74, 0.3)',
        card: '0 4px 24px rgba(0, 0, 0, 0.4)',
        'card-hover': '0 8px 32px rgba(0, 0, 0, 0.6)',
      },
      borderRadius: { xl: '0.75rem', '2xl': '1rem' },
      transitionDuration: { DEFAULT: '200ms' },
    },
  },
  plugins: [],
}
