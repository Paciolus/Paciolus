export const MOVEMENT_TYPE_LABELS: Record<string, string> = {
  new_account: 'New',
  closed_account: 'Closed',
  sign_change: 'Sign Change',
  increase: 'Increase',
  decrease: 'Decrease',
  unchanged: 'Unchanged',
}

export const MOVEMENT_TYPE_COLORS: Record<string, string> = {
  new_account: 'bg-sage-50 text-sage-700 border-sage-500/30',
  closed_account: 'bg-clay-50 text-clay-700 border-clay-500/30',
  sign_change: 'bg-clay-50 text-clay-700 border-clay-500/30',
  increase: 'bg-sage-50 text-sage-600 border-sage-500/20',
  decrease: 'bg-clay-50 text-clay-600 border-clay-500/20',
  unchanged: 'bg-surface-card-secondary text-content-tertiary border-theme',
}

export const SIGNIFICANCE_COLORS: Record<string, string> = {
  material: 'text-clay-600 font-bold',
  significant: 'text-content-primary font-medium',
  minor: 'text-content-tertiary',
}

export const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } },
}

export const stagger = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
}

export const formatCurrency = (val: number) => {
  const abs = Math.abs(val)
  const formatted = abs >= 1000 ? `$${(abs / 1000).toFixed(1)}K` : `$${abs.toFixed(0)}`
  return val < 0 ? `-${formatted}` : formatted
}
