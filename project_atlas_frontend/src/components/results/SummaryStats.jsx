import { DollarSign, Shield, TrendingDown, AlertTriangle, Clock, Gauge } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard.jsx'
import { formatUSD, formatPct, formatDays, formatProbability } from '@/utils/formatters.js'

export function SummaryStats({ keyed={}, loading=false }) {
  const cost  = keyed['total_cost_usd']        || {}
  const flow  = keyed['supply_chain_flow_pct'] || {}
  const recov = keyed['recovery_time_days']    || {}

  const pFailure = flow.percentile_5!=null ? Math.max(0,1-(flow.percentile_5/0.5)) : null
  const meanFlow  = flow.mean_value!=null ? flow.mean_value : null

  const varRisk = !cost.var_95?'low':cost.var_95>5e9?'critical':cost.var_95>1e9?'high':cost.var_95>1e8?'medium':'low'
  const failRisk = pFailure==null?'low':pFailure>0.4?'critical':pFailure>0.2?'high':pFailure>0.05?'medium':'low'

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
      <StatCard label="Expected Cost (Mean)" value={cost.mean_value!=null?formatUSD(cost.mean_value):'—'} secondary={cost.std_deviation!=null?`±${formatUSD(cost.std_deviation)} std dev`:undefined} icon={DollarSign} iconColor="text-primary-400" loading={loading}/>
      <StatCard label="VaR-95" value={cost.var_95!=null?formatUSD(cost.var_95):'—'} secondary="5% chance cost exceeds this" icon={Shield} iconColor="text-amber-400" riskLevel={varRisk} loading={loading}/>
      <StatCard label="CVaR-95" value={cost.cvar_95!=null?formatUSD(cost.cvar_95):'—'} secondary="Average of worst 5% outcomes" icon={TrendingDown} iconColor="text-red-400" riskLevel={varRisk} loading={loading}/>
      <StatCard label="P(Supply Failure)" value={pFailure!=null?formatProbability(pFailure):'—'} secondary="Flow drops below 50% of normal" icon={AlertTriangle} iconColor={failRisk==='critical'?'text-red-400':'text-orange-400'} riskLevel={failRisk} loading={loading}/>
      <StatCard label="Mean Recovery Time" value={recov.mean_value!=null?formatDays(recov.mean_value):'—'} secondary={recov.percentile_95!=null?`P95: ${formatDays(recov.percentile_95)}`:undefined} icon={Clock} iconColor="text-blue-400" loading={loading}/>
      <StatCard label="Mean Flow Achievement" value={meanFlow!=null?formatPct(meanFlow):'—'} secondary={flow.percentile_5!=null?`P5: ${formatPct(flow.percentile_5)}`:undefined} icon={Gauge} iconColor={meanFlow==null?'text-gray-400':meanFlow>0.85?'text-green-400':meanFlow>0.60?'text-yellow-400':'text-red-400'} riskLevel={meanFlow==null?undefined:meanFlow>0.85?'low':meanFlow>0.60?'medium':'high'} loading={loading}/>
    </div>
  )
}
