import { ComposedChart, Bar, ReferenceLine, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Label } from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardDescription, CardBody } from '@/components/ui/Card.jsx'
import { Spinner } from '@/components/ui/Spinner.jsx'
import { EmptyState } from '@/components/ui/EmptyState.jsx'
import { resultsService } from '@/services/resultsService.js'
import { buildHistogram } from '@/utils/chartHelpers.js'
import { formatUSD, formatUSDAxis } from '@/utils/formatters.js'
import { BarChart2 } from 'lucide-react'

function CostTooltip({ active, payload }) {
  if (!active||!payload?.length) return null
  const d=payload[0]?.payload; if(!d) return null
  return (
    <div className="bg-surface-700 border border-surface-500 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="font-semibold text-white mb-1">{formatUSD(d.bin_start)} – {formatUSD(d.bin_end)}</p>
      <p className="text-primary-300">{d.count} iterations ({d._total>0?((d.count/d._total)*100).toFixed(1):0}%)</p>
    </div>
  )
}

export function CostDistribution({ runId, keyed={} }) {
  const cost = keyed['total_cost_usd'] || {}

  const { data: iterData, isLoading } = useQuery({
    queryKey: ['results-iterations-all', runId],
    queryFn:  () => resultsService.getIterations(runId, { limit:10_000, offset:0 }).then((r)=>r.data),
    enabled:  !!runId, staleTime: Infinity,
  })

  const items  = iterData?.items || []
  const values = items.map((r)=>r.total_cost_usd).filter((v)=>v!=null&&isFinite(v))
  const total  = values.length
  const histData = buildHistogram(values,50).map((bin)=>({...bin,_total:total}))

  if (isLoading) return <Card className="h-80 flex items-center justify-center"><Spinner/></Card>
  if (!values.length) return <Card className="h-80"><EmptyState icon={BarChart2} title="No iteration data" description="Run a simulation to see the cost distribution."/></Card>

  return (
    <Card id="chart-cost-distribution">
      <CardHeader><CardTitle>Total Cost Distribution</CardTitle><CardDescription>Empirical distribution across {total.toLocaleString()} Monte Carlo iterations</CardDescription></CardHeader>
      <CardBody>
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={histData} margin={{top:8,right:24,left:16,bottom:32}}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45"/>
            <XAxis dataKey="bin_mid" tickFormatter={formatUSDAxis} tick={{fill:'#6b7280',fontSize:11}} stroke="#263650"><Label value="Total Cost (USD)" offset={-10} position="insideBottom" fill="#6b7280" fontSize={11}/></XAxis>
            <YAxis tick={{fill:'#6b7280',fontSize:11}} stroke="#263650"><Label value="Frequency" angle={-90} position="insideLeft" fill="#6b7280" fontSize={11} offset={8}/></YAxis>
            <Tooltip content={<CostTooltip/>}/>
            <Bar dataKey="count" name="Iterations" fill="#2563eb" fillOpacity={0.75} radius={[2,2,0,0]}/>
            {cost.mean_value!=null && <ReferenceLine x={cost.mean_value} stroke="#3b82f6" strokeDasharray="6 3" strokeWidth={2} label={{value:`Mean: ${formatUSD(cost.mean_value)}`,fill:'#3b82f6',fontSize:10,position:'top'}}/>}
            {cost.var_95!=null    && <ReferenceLine x={cost.var_95}    stroke="#f59e0b" strokeWidth={2}        label={{value:`VaR-95: ${formatUSD(cost.var_95)}`,fill:'#f59e0b',fontSize:10,position:'top'}}/>}
            {cost.cvar_95!=null   && <ReferenceLine x={cost.cvar_95}   stroke="#ef4444" strokeWidth={2}        label={{value:`CVaR-95: ${formatUSD(cost.cvar_95)}`,fill:'#ef4444',fontSize:10,position:'insideTopRight'}}/>}
          </ComposedChart>
        </ResponsiveContainer>
      </CardBody>
    </Card>
  )
}
