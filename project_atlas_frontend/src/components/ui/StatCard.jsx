import { clsx } from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export function StatCard({ label, value, secondary, icon:Icon, iconColor='text-primary-400', trend, trendLabel, riskLevel, loading=false, className='' }) {
  const riskColor = { critical:'text-red-400', high:'text-orange-400', medium:'text-yellow-400', low:'text-green-400' }
  const trendConfig = { up:{Icon:TrendingUp,color:'text-green-400'}, down:{Icon:TrendingDown,color:'text-red-400'}, neutral:{Icon:Minus,color:'text-gray-500'} }
  const trendInfo = trendConfig[trend]
  return (
    <div className={clsx('rounded-xl border border-surface-500 bg-surface-800 p-5 transition-all duration-200 hover:border-surface-400', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">{label}</p>
          {loading ? <div className="h-8 w-32 bg-surface-600 rounded animate-pulse" /> : (
            <p className={clsx('text-2xl font-mono font-bold tabular-nums truncate', riskLevel?riskColor[riskLevel]:'text-white')}>{value??'—'}</p>
          )}
          {secondary && !loading && <p className="text-xs text-gray-500 mt-1.5 font-mono tabular-nums">{secondary}</p>}
          {trendInfo && trendLabel && !loading && (
            <div className={clsx('flex items-center gap-1 mt-2 text-xs', trendInfo.color)}>
              <trendInfo.Icon className="w-3 h-3" /><span>{trendLabel}</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ml-3 bg-surface-700 border border-surface-500">
            <Icon className={clsx('w-5 h-5', iconColor)} />
          </div>
        )}
      </div>
    </div>
  )
}
