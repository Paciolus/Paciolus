import { motion } from 'framer-motion'
import { fadeIn, stagger } from './constants'
import type { MovementSummaryResponse } from '@/hooks'

export function MovementSummaryCards({ comparison }: { comparison: MovementSummaryResponse }) {
  const cards = [
    { key: 'new_account', label: 'New Accounts', icon: '+', color: 'sage' },
    { key: 'closed_account', label: 'Closed Accounts', icon: '-', color: 'clay' },
    { key: 'sign_change', label: 'Sign Changes', icon: '~', color: 'clay' },
    { key: 'increase', label: 'Increases', icon: '\u2191', color: 'sage' },
    { key: 'decrease', label: 'Decreases', icon: '\u2193', color: 'clay' },
    { key: 'unchanged', label: 'Unchanged', icon: '=', color: 'oatmeal' },
  ]

  const borderAccentMap: Record<string, string> = {
    sage: 'border-l-4 border-l-sage-500',
    clay: 'border-l-4 border-l-clay-500',
    oatmeal: 'border-l-4 border-l-oatmeal-400',
  }

  return (
    <motion.div className="grid grid-cols-3 md:grid-cols-6 gap-3" variants={stagger} initial="hidden" animate="visible">
      {cards.map(({ key, label, icon, color }) => (
        <motion.div
          key={key}
          className={`theme-card p-3 text-center ${borderAccentMap[color]}`}
          variants={fadeIn}
        >
          <div className="text-content-tertiary text-xs font-mono mb-1">{icon}</div>
          <div className={`text-2xl font-mono font-bold ${color === 'sage' ? 'text-sage-600' : color === 'clay' ? 'text-clay-600' : 'text-content-secondary'}`}>
            {comparison.movements_by_type[key] || 0}
          </div>
          <div className="text-xs font-sans text-content-tertiary mt-1">{label}</div>
        </motion.div>
      ))}
    </motion.div>
  )
}
