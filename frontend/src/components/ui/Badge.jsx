import clsx from 'clsx'

const VARIANT_CLASSES = {
  profit:  'bg-profit/10 text-profit border border-profit/20',
  loss:    'bg-loss/10 text-loss border border-loss/20',
  neutral: 'bg-border text-text-secondary',
  accent:  'bg-accent/10 text-accent border border-accent/20',
  amber:   'bg-amber/10 text-amber border border-amber/20',
}

export default function Badge({ label, variant = 'neutral' }) {
  return (
    <span
      className={clsx(
        'px-2 py-0.5 rounded text-[11px] font-medium inline-flex',
        VARIANT_CLASSES[variant] ?? VARIANT_CLASSES.neutral
      )}
    >
      {label}
    </span>
  )
}
