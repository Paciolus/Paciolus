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
    },
  },
  plugins: [],
}
export default config
