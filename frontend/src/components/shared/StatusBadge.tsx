interface StatusBadgeColors {
  bg: string
  text: string
  border: string
}

interface StatusBadgeProps {
  label: string
  colors: StatusBadgeColors
}

export function StatusBadge({ label, colors }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-sans ${colors.bg} ${colors.text} border ${colors.border}`}>
      {label}
    </span>
  )
}
