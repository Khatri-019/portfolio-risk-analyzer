import { getProfitClass, formatPct } from '../../utils/formatters'
import Card from './Card'

export default function MetricCard({ label, value, change, changeLabel, description, icon: Icon }) {
  return (
    <Card className="hover:border-l-2 hover:border-l-accent transition-all p-5">
      <div className="flex items-start justify-between mb-1">
        <span className="uppercase text-[10px] tracking-widest text-text-secondary font-medium">
          {label}
        </span>
        {Icon && <Icon size={16} className="text-text-secondary shrink-0" />}
      </div>

      <div className="text-[22px] font-bold text-text-primary leading-tight mt-2">
        {value ?? 'N/A'}
      </div>

      {change !== undefined && change !== null && (
        <div className="flex items-center gap-2 mt-2">
          <span className={`text-[12px] font-medium ${getProfitClass(change)}`}>
            {formatPct(change)}
          </span>
          {changeLabel && (
            <span className="text-[12px] text-text-secondary">{changeLabel}</span>
          )}
        </div>
      )}

      {description && (
        <p className="text-[11px] text-text-secondary italic mt-1">{description}</p>
      )}
    </Card>
  )
}
