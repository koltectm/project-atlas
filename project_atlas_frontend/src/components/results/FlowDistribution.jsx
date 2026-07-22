import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Label } from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { Card, CardHeader, CardTitle, CardDescription, CardBody } from '@/components/ui/Card.jsx'
import { Spinner } from '@/components/ui/Spinner.jsx'
import { EmptyState } from '@/components/ui/EmptyState.jsx'
import { resultsService } from '@/services/resultsService.js'
import { buildHistogram } from '@/utils/chartHelpers.js'
import { formatPct } from '@/utils/formatters.js'
import { Waves } from 'lucide-react'

function FlowTooltip({ active, payload }) {
  if (!active||!payload?.length) return null
  const d=payload[0]?.payload; if(!d) return null
  return <div className="bg-surface-700 border border-surface-500 rounded-lg px-3 py-2 text-xs shadow-xl"><p className="font-semibold text-white mb-1">Flow: {formatPct(d.bin_mid)}</p><p className="text-primary-300">{d.count} iterations</p></div>
}

export function FlowDistribution({ runId, keyed={} }) {
  const flow = keyed['supply_chain_flow_pct'] || {}

  const { data: iterData, isLoading } = useQuery({
    queryKey: ['results-iterations-all', runId],
    queryFn:  () => resultsService.getIterations(runId, { limit:10_000, offset:0 }).then((r)=>r.data),
    enabled:  !!runId, staleTime: Infinity,
  })

  const items  = iterData?.items || []
  const values = items.map((r)=>r.supply_chain_flow_pct).filter((v)=>v!=null&&isFinite(v))
  const histData = buildHistogram(values,40)

  if (isLoading) return <Card className="h-80 flex items-center justify-center"><Spinner/></Card>
  if (!values.length) return <Card className="h-80"><EmptyState icon={Waves} title="No flow data" description="Run a simulation first."/></Card>

  return (
    <Card id="chart-flow-distribution">
      <CardHeader><CardTitle>Supply Chain Flow Distribution</CardTitle><CardDescription>Fraction of baseline throughput achieved across {values.length.toLocaleString()} iterations</CardDescription></CardHeader>
      <CardBody>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={histData} margin={{top:8,right:16,left:16,bottom:32}}>
            <defs><linearGradient id="flowGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#16a34a" stopOpacity={0.4}/><stop offset="95%" stopColor="#16a34a" stopOpacity={0.05}/></linearGradient></defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45"/>
            <XAxis dataKey="bin_mid" tickFormatter={(v)=>formatPct(v)} tick={{fill:'#6b7280',fontSize:11}} stroke="#263650" domain={[0,1]}><Label value="Flow Achievement (%)" offset={-10} position="insideBottom" fill="#6b7280" fontSize={11}/></XAxis>
            <YAxis tick={{fill:'#6b7280',fontSize:11}} stroke="#263650"/>
            <Tooltip content={<FlowTooltip/>}/>
            <Area type="monotone" dataKey="count" stroke="#16a34a" strokeWidth={2} fill="url(#flowGradient)"/>
            {flow.mean_value!=null && <ReferenceLine x={flow.mean_value} stroke="#3b82f6" strokeDasharray="5 3" strokeWidth={2} label={{value:`Mean: ${formatPct(flow.mean_value)}`,fill:'#3b82f6',fontSize:10,position:'top'}}/>}
            <ReferenceLine x={0.5} stroke="#dc2626" strokeDasharray="4 4" strokeWidth={1.5} label={{value:'Failure threshold (50%)',fill:'#dc2626',fontSize:9,position:'insideTopLeft'}}/>
          </AreaChart>
        </ResponsiveContainer>
      </CardBody>
    </Card>
  )
}
