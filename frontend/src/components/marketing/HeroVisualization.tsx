'use client'

import { motion } from 'framer-motion'

/**
 * HeroVisualization — Sprint 319
 *
 * Animated floating financial data elements that drift, pulse, and connect.
 * Visual metaphor: raw financial data being organized into insights.
 *
 * Pure CSS + framer-motion — no images, no external dependencies.
 * Respects prefers-reduced-motion via framer-motion MotionConfig.
 */

type ElementSize = 'sm' | 'md' | 'lg'
type ElementType = 'ratio' | 'amount' | 'label' | 'category'

// Floating data elements — financial terms and numbers that drift
const FLOATING_ELEMENTS: Array<{
  label: string; x: string; y: string; delay: number; size: ElementSize; type: ElementType
}> = [
  // Row 1 — top scattered
  { label: '1.82', x: '8%', y: '6%', delay: 0.3, size: 'lg', type: 'ratio' },
  { label: 'DR', x: '72%', y: '2%', delay: 0.5, size: 'sm', type: 'label' },
  { label: '$4.2M', x: '85%', y: '12%', delay: 0.7, size: 'md', type: 'amount' },
  // Row 2
  { label: 'CR', x: '18%', y: '22%', delay: 0.4, size: 'sm', type: 'label' },
  { label: '94.7%', x: '55%', y: '18%', delay: 0.6, size: 'md', type: 'ratio' },
  // Row 3 — mid emphasis
  { label: 'Assets', x: '5%', y: '42%', delay: 0.2, size: 'md', type: 'category' },
  { label: '$12.4M', x: '70%', y: '38%', delay: 0.8, size: 'lg', type: 'amount' },
  // Row 4
  { label: '0.67', x: '25%', y: '58%', delay: 0.5, size: 'sm', type: 'ratio' },
  { label: 'Equity', x: '82%', y: '55%', delay: 0.3, size: 'md', type: 'category' },
  // Row 5 — bottom
  { label: 'Revenue', x: '12%', y: '75%', delay: 0.6, size: 'md', type: 'category' },
  { label: '$892K', x: '58%', y: '72%', delay: 0.4, size: 'sm', type: 'amount' },
  { label: '3.14', x: '40%', y: '88%', delay: 0.7, size: 'md', type: 'ratio' },
  { label: 'ISA 520', x: '78%', y: '82%', delay: 0.9, size: 'sm', type: 'label' },
]

const TYPE_STYLES: Record<ElementType, string> = {
  ratio: 'text-sage-400 bg-sage-500/10 border-sage-500/20',
  amount: 'text-oatmeal-300 bg-oatmeal-500/10 border-oatmeal-500/20',
  label: 'text-oatmeal-500 bg-obsidian-700/50 border-obsidian-500/30',
  category: 'text-sage-300 bg-sage-500/8 border-sage-500/15',
}

const SIZE_CLASSES: Record<ElementSize, string> = {
  sm: 'text-xs px-2 py-1',
  md: 'text-sm px-3 py-1.5',
  lg: 'text-base px-4 py-2 font-semibold',
}

// Connection lines between elements (SVG paths)
const CONNECTIONS = [
  { x1: '15%', y1: '25%', x2: '55%', y2: '20%', delay: 1.2 },
  { x1: '70%', y1: '40%', x2: '82%', y2: '57%', delay: 1.4 },
  { x1: '12%', y1: '44%', x2: '25%', y2: '60%', delay: 1.6 },
  { x1: '58%', y1: '74%', x2: '40%', y2: '90%', delay: 1.8 },
]

// Mini bar chart data for the chart fragment
const CHART_BARS = [
  { height: 40, delay: 1.0 },
  { height: 65, delay: 1.1 },
  { height: 52, delay: 1.2 },
  { height: 78, delay: 1.3 },
  { height: 45, delay: 1.4 },
  { height: 88, delay: 1.5 },
  { height: 60, delay: 1.6 },
]

export function HeroVisualization() {
  return (
    <div className="relative w-full h-full min-h-[400px] md:min-h-[480px]" aria-hidden="true">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-sage-500/[0.04] blur-[100px]" />
      </div>

      {/* Grid overlay — subtle ledger lines */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.06]" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="hero-grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-oatmeal-400" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#hero-grid)" />
      </svg>

      {/* Connection lines */}
      <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
        {CONNECTIONS.map((conn, i) => (
          <motion.line
            key={i}
            x1={conn.x1}
            y1={conn.y1}
            x2={conn.x2}
            y2={conn.y2}
            stroke="currentColor"
            strokeWidth="1"
            className="text-obsidian-500/40"
            strokeDasharray="4 4"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.4 }}
            transition={{ duration: 1.2, delay: conn.delay, ease: 'easeOut' as const }}
          />
        ))}
      </svg>

      {/* Floating data elements */}
      {FLOATING_ELEMENTS.map((el, i) => (
        <motion.div
          key={i}
          className={`absolute font-mono rounded-lg border backdrop-blur-sm ${TYPE_STYLES[el.type]} ${SIZE_CLASSES[el.size]}`}
          style={{ left: el.x, top: el.y }}
          initial={{ opacity: 0, scale: 0.8, y: 10 }}
          animate={{
            opacity: [0, 1, 1, 0.7, 1],
            scale: 1,
            y: [10, 0, -3, 0],
          }}
          transition={{
            duration: 3,
            delay: el.delay,
            y: {
              duration: 6,
              repeat: Infinity,
              repeatType: 'reverse' as const,
              ease: 'easeInOut' as const,
              delay: el.delay,
            },
            opacity: {
              duration: 4,
              times: [0, 0.2, 0.5, 0.8, 1],
              delay: el.delay,
            },
          }}
        >
          {el.label}
        </motion.div>
      ))}

      {/* Mini chart fragment — bottom-left area */}
      <motion.div
        className="absolute bottom-[12%] left-[35%] flex items-end gap-1.5 p-3 rounded-xl bg-obsidian-800/60 border border-obsidian-500/30 backdrop-blur-sm"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.8 }}
      >
        {CHART_BARS.map((bar, i) => (
          <motion.div
            key={i}
            className="w-2.5 rounded-t bg-gradient-to-t from-sage-600 to-sage-400"
            initial={{ height: 0 }}
            animate={{ height: `${bar.height}px` }}
            transition={{
              duration: 0.8,
              delay: bar.delay,
              ease: 'easeOut' as const,
            }}
          />
        ))}
      </motion.div>

      {/* Score circle — top-right area */}
      <motion.div
        className="absolute top-[15%] right-[8%] w-20 h-20 md:w-24 md:h-24"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 1.0 }}
      >
        <svg viewBox="0 0 100 100" className="w-full h-full">
          <circle
            cx="50" cy="50" r="40"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-obsidian-600"
          />
          <motion.circle
            cx="50" cy="50" r="40"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-sage-500"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 40}`}
            strokeDashoffset={2 * Math.PI * 40 * 0.28}
            transform="rotate(-90 50 50)"
            initial={{ strokeDashoffset: 2 * Math.PI * 40 }}
            animate={{ strokeDashoffset: 2 * Math.PI * 40 * 0.28 }}
            transition={{ duration: 1.5, delay: 1.2, ease: 'easeOut' as const }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className="font-mono text-lg md:text-xl font-bold text-sage-400"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.8 }}
          >
            72
          </motion.span>
          <span className="text-[9px] text-oatmeal-600 font-sans">/100</span>
        </div>
      </motion.div>

      {/* Pulse dot indicators — scattered */}
      {[
        { x: '48%', y: '30%', delay: 2.0 },
        { x: '30%', y: '50%', delay: 2.3 },
        { x: '65%', y: '60%', delay: 2.6 },
      ].map((dot, i) => (
        <motion.div
          key={`dot-${i}`}
          className="absolute w-2 h-2 rounded-full bg-sage-400"
          style={{ left: dot.x, top: dot.y }}
          initial={{ opacity: 0, scale: 0 }}
          animate={{
            opacity: [0, 0.6, 0.3, 0.6],
            scale: [0, 1, 1.5, 1],
          }}
          transition={{
            duration: 3,
            delay: dot.delay,
            repeat: Infinity,
            repeatType: 'reverse' as const,
          }}
        />
      ))}
    </div>
  )
}
