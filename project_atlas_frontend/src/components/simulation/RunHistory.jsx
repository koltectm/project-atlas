import { useNavigate } from 'react-router-dom'
import { BarChart3, Eye, Play } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { DataTable } from '@/components/ui/DataTable.jsx'
import { StatusBadge } from '@/components/ui/Badge.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { EmptyState } from '@/components/ui/EmptyState.jsx'
import { Tooltip } from '@/components/ui/Tooltip.jsx'
import { simulationService } from '@/services/simulationService.js'
import { formatDateTime, formatSeconds, formatIterations } from '@/utils/formatters.js'

export function RunHistory({ scenarioId }) {
  const navigate = useNavigate()
  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['runs-for-scenario', scenarioId],
    queryFn:  () => simulationService.getRunsForScenario(scenarioId).then((r) => r.data),
    enabled:  !!scenarioId,
    refetchInterval: 5_000,
  })

  const columns = [
    { key:'status',           label:'Status',     render:(v)=><StatusBadge status={v}/> },
    { key:'total_iterations', label:'Iterations',  sortable:true, align:'right', render:(v)=><span className="font-mono tabular-nums text-gray-200">{formatIterations(v)}</span> },
    { key:'duration_seconds', label:'Duration',    sortable:true, align:'right', render:(v)=><span className="font-mono tabular-nums text-gray-400">{v!=null?formatSeconds(v):'—'}</span> },
    { key:'started_at',       label:'Started',     sortable:true, render:(v)=><span className="text-xs text-gray-400">{formatDateTime(v)}</span> },
    { key:'run_id',           label:'Actions',     width:'w-24',
      render:(runId,row)=>(
        <div className="flex items-center gap-1.5">
          {row.status==='completed' && <Tooltip content="View Results"><Button size="xs" variant="secondary" icon={Eye} onClick={(e)=>{ e.stopPropagation(); navigate(`/results/${runId}`) }}/></Tooltip>}
          {['running','queued'].includes(row.status) && <Tooltip content="View Progress"><Button size="xs" variant="primary" icon={BarChart3} onClick={(e)=>{ e.stopPropagation(); navigate(`/simulation/${runId}`) }}/></Tooltip>}
        </div>
      )},
  ]

  if (!isLoading && runs.length===0) return <EmptyState icon={Play} title="No runs yet" description="Run the simulation to see results here."/>

  return (
    <DataTable columns={columns} data={runs} rowKey="run_id" loading={isLoading} pageSize={10}
      emptyTitle="No simulation runs"
      onRowClick={(row)=>{ if(row.status==='completed') navigate(`/results/${row.run_id}`); else if(['queued','running'].includes(row.status)) navigate(`/simulation/${row.run_id}`) }}/>
  )
}
