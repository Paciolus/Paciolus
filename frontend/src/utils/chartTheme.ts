/** Oat & Obsidian chart colors — single source of truth for Recharts/framer-motion */
export const CHART_THEME = {
  sage: '#4A7C59',         // sage-500
  clay: '#BC4749',         // clay-500
  oatmeal: '#B5AD9F',     // oatmeal-500
  oatmealLight: '#DDD9D1', // oatmeal-300
  oatmealMuted: '#9A9486', // oatmeal-600
  obsidianLight: '#616161', // obsidian-500
  obsidianGrid: '#424242',  // obsidian-600
  obsidianBg: '#212121',    // obsidian-800
  textLight: '#EBE9E4',    // oatmeal-200
  textMuted: '#9e9e9e',    // obsidian-300
  white: '#FFFFFF',
} as const

/** Pre-built rgba helpers for animation shadows */
export const CHART_SHADOWS = {
  clayPulse: (opacity: number): string => `rgba(188, 71, 73, ${opacity})`,
  sagePulse: (opacity: number): string => `rgba(74, 124, 89, ${opacity})`,
  darkShadow: (opacity: number): string => `rgba(0, 0, 0, ${opacity})`,
} as const
