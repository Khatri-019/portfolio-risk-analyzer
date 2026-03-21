// Width cycles: 100% → 75% → 50% → repeat, giving a tapered skeleton feel
const WIDTH_CYCLE = ['w-full', 'w-3/4', 'w-1/2']

export default function Loader({ rows = 3, height = 'h-8' }) {
  return (
    <div>
      {Array.from({ length: rows }, (_, i) => (
        <div
          key={i}
          className={`animate-pulse bg-surface border border-border rounded-card mb-3 ${height} ${WIDTH_CYCLE[i % WIDTH_CYCLE.length]}`}
        />
      ))}
    </div>
  )
}
