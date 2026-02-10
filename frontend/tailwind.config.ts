import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Oat & Obsidian Theme
        // See: skills/theme-factory/themes/oat-and-obsidian.md

        obsidian: {
          50: '#f5f5f5',
          100: '#e0e0e0',
          200: '#bdbdbd',
          300: '#9e9e9e',
          400: '#757575',
          500: '#616161',
          600: '#424242',
          700: '#303030',
          800: '#212121',  // Base
          900: '#121212',
          DEFAULT: '#212121',
        },

        oatmeal: {
          50: '#FAFAF9',
          100: '#F5F4F2',
          200: '#EBE9E4',  // Base
          300: '#DDD9D1',
          400: '#C9C3B8',
          500: '#B5AD9F',
          600: '#9A9486',
          700: '#7F7A6E',
          800: '#656157',
          900: '#4B4840',
          DEFAULT: '#EBE9E4',
        },

        clay: {
          50: '#FDF2F2',
          100: '#FBE5E5',
          200: '#F5CCCC',
          300: '#E99A9B',
          400: '#D16C6E',
          500: '#BC4749',  // Base
          600: '#A33D3F',
          700: '#882F31',
          800: '#6E2224',
          900: '#541718',
          DEFAULT: '#BC4749',
        },

        sage: {
          50: '#F2F7F4',
          100: '#E5EFE9',
          200: '#C8DED1',
          300: '#9BC5AB',
          400: '#6FA882',
          500: '#4A7C59',  // Base
          600: '#3D6649',
          700: '#30503A',
          800: '#243D2C',
          900: '#192B1F',
          DEFAULT: '#4A7C59',
        },

        // Legacy alias (for gradual migration)
        primary: {
          50: '#F2F7F4',
          100: '#E5EFE9',
          200: '#C8DED1',
          300: '#9BC5AB',
          400: '#6FA882',
          500: '#4A7C59',
          600: '#3D6649',
          700: '#30503A',
          800: '#253D2B',
          900: '#1A2B1E',
          950: '#0F1A12',
        },
      },
      fontFamily: {
        // Oat & Obsidian Typography
        serif: ['Merriweather', 'Georgia', 'serif'],
        sans: ['Lato', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'monospace'],
      },
      boxShadow: {
        // Oat & Obsidian Shadow System
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.03)',
        'card-hover': '0 8px 25px -5px rgba(0, 0, 0, 0.4), 0 4px 10px -2px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        'glow-sage': '0 0 10px rgba(74, 124, 89, 0.5)',
        'glow-sage-soft': '0 0 8px rgba(74, 124, 89, 0.3)',
        'inner-sage': 'inset 0 0 30px rgba(74, 124, 89, 0.1)',
        'inner-sage-hover': 'inset 0 0 40px rgba(74, 124, 89, 0.15)',
      },
      transitionDuration: {
        // Standardized transition durations
        'fast': '150ms',
        'base': '200ms',
        'slow': '300ms',
      },
    },
  },
  plugins: [],
}
export default config
