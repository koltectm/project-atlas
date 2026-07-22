/**
 * src/components/results/IterationTable.jsx
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Table2 } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardBody } from '@/components/ui/Card.jsx'
import { DataTable } from '@/components/ui/DataTable.jsx'
import { resultsService } from '@/services/resultsService.js'
import { formatUSD, formatDays, formatPct, formatBarrels } from '@/utils/formatters.js'

const PAGE_SIZE = 50

export function IterationTable({ runId }) {
  const [page, setPage] = useState(0)

  const { data, isLoading } = useQuery({
    queryKey: ['results-iterations-page', runId, page],
    queryFn:  () => resultsService.getIterations(runId, {
      limit: PAGE_SIZE, offset: page * PAGE_SIZE,
    }).then((r) => r.data),
    enabled:  !!runId,
    staleTime: Infinity,
  })

  const columns = [
    { key: 'iteration_number', label: '#', sortable: true, align: 'right', width: 'w-16' },
    {
      key: 'total_cost_usd', label: 'Total Cost', sortable: true, align: 'right',
      render: (v) => formatUSD(v),
    },
    {
      key: 'total_delay_days', label: 'Delay', sortable: true, align: 'right',
      render: (v) => formatDays(v),
    },
    {
      key: 'production_loss_barrels', label: 'Prod. Loss', sortable: true, align: 'right',
      render: (v) => formatBarrels(v),
    },
    {
      key: 'supply_chain_flow_pct', label: 'Flow %', sortable: true, align: 'right',
      render: (v) => formatPct(v),
    },
    {
      key: 'nodes_affected', label: 'Nodes', sortable: true, align: 'right',
    },
    {
      key: 'links_disrupted', label: 'Links', sortable: true, align: 'right',
    },
    {
      key: 'recovery_time_days', label: 'Recovery', sortable: true, align: 'right',
      render: (v) => formatDays(v),
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Raw Iteration Data</CardTitle>
        <CardDescription>
          Page {page + 1} of {Math.ceil((data?.total || 0) / PAGE_SIZE)} —
          {' '}{data?.total?.toLocaleString() || 0} total iterations
        </CardDescription>
      </CardHeader>
      <CardBody>
        <DataTable
          columns={columns}
          data={data?.items || []}
          loading={isLoading}
          rowKey="result_id"
          pageSize={PAGE_SIZE}
          emptyTitle="No iteration data"
        />
      </CardBody>
    </Card>
  )
}
