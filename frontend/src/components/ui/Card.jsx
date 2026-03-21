import clsx from 'clsx'

export default function Card({ children, className }) {
  return (
    <div
      className={clsx(
        'bg-surface border border-border rounded-card shadow-card hover:shadow-card-hover transition-shadow p-4',
        className
      )}
    >
      {children}
    </div>
  )
}
