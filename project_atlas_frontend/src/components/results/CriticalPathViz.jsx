/**
 * src/components/results/CriticalPathViz.jsx
 * ============================================
 * Displays the critical path analysis results from the OR engine:
 *  - Ordered list of critical path nodes with lead times
 *  - Min-cut bottleneck capacity
 *  - Single points of failure (SPOFs)
 *  - Node importance scores (top 10)
 */
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, Label,
} from 'recharts'
import { Route, AlertTriangle, Zap, ArrowRight } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardBody } from '@/components/ui/Card.jsx'
import { Badge } from '@/components/ui/Badge.jsx'
import { Spinner } from '@/components/ui/Spinner.jsx'
import { AlertBanner } from '@/components/ui/AlertBanner.jsx'
import { analyticsService } from '@/services/analyticsService.js'
import { formatBpd, formatDays, formatScore } from '@/utils/formatters.js'

export function CriticalPathViz() {
  const { data, isLoading, error } = useQuery({
    queryKey:  ['critical-path'],
    queryFn:   () => analyticsService.getCriticalPath().then((r) => r.data),
    staleTime: 5 * 60_000,
  })

  if (isLoading) {
    return (
      <Card className="h-72 flex items-center justify-center">
        <Spinner />
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardBody>
          <AlertBanner variant="error" title="Critical path analysis unavailable">
            {error.message || 'Failed to load OR engine results.'}
          </AlertBanner>
        </CardBody>
      </Card>
    )
  }

  const criticalPath  = data?.critical_path || []
  const spofs         = data?.single_points_of_failure || []
  const minCutBpd     = data?.min_cut_bpd
  const importance    = data?.node_importance || {}

  // Build importance chart data from the top 10 nodes
  const importanceData = Object.entries(importance)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([id, score]) => ({
      id: id.slice(0, 8) + '…',
      score: parseFloat(score.toFixed(4)),
      fullId: id,
    }))

  return (
    <div className="space-y-4">
      {/* Critical path chain */}
      <Card>
        <CardHeader>
          <CardTitle>Critical Path</CardTitle>
          <CardDescription>
            Longest lead-time path from upstream to downstream (CPM analysis)
          </CardDescription>
        </CardHeader>
        <CardBody>
          {criticalPath.length === 0 ? (
            <p className="text-sm text-gray-500">No critical path data available.</p>
          ) : (
            <div className="flex items-center flex-wrap gap-1">
              {criticalPath.map((nodeId, i) => (
                <div key={nodeId} className="flex items-center gap-1">
                  <span className={`px-2 py-1 text-xs rounded-md font-mono border ${
                    spofs.includes(nodeId)
                      ? 'bg-red-900/20 border-red-600/50 text-red-400'
                      : 'bg-amber-900/20 border-amber-600/50 text-amber-300'
                  }`}>
                    {nodeId.slice(0, 8)}
                    {spofs.includes(nodeId) && ' ⚠'}
                  </span>
                  {i < criticalPath.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-gray-600 flex-shrink-0" />
                  )}
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardBody className="text-center py-4">
            <Zap className="w-5 h-5 text-amber-400 mx-auto mb-2" />
            <p className="text-xs text-gray-400 mb-1">Min-Cut Capacity</p>
            <p className="text-base font-mono font-bold text-white">
              {minCutBpd != null ? formatBpd(minCutBpd) : '—'}
            </p>
            <p className="text-2xs text-gray-500 mt-1">Network bottleneck</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center py-4">
            <AlertTriangle className="w-5 h-5 text-red-400 mx-auto mb-2" />
            <p className="text-xs text-gray-400 mb-1">Single Points of Failure</p>
            <p className="text-2xl font-mono font-bold text-red-400">
              {spofs.length}
            </p>
            <p className="text-2xs text-gray-500 mt-1">Nodes / links</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="text-center py-4">
            <Route className="w-5 h-5 text-primary-400 mx-auto mb-2" />
            <p className="text-xs text-gray-400 mb-1">Critical Path Nodes</p>
            <p className="text-2xl font-mono font-bold text-white">
              {criticalPath.length}
            </p>
            <p className="text-2xs text-gray-500 mt-1">Sequential hops</p>
          </CardBody>
        </Card>
      </div>

      {/* SPOFs list */}
      {spofs.length > 0 && (
        <AlertBanner variant="warning" title={`${spofs.length} Single Point(s) of Failure Detected`}>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {spofs.map((id) => (
              <span
                key={id}
                className="px-2 py-0.5 text-xs font-mono rounded border
                           bg-yellow-900/20 border-yellow-700/50 text-yellow-300"
              >
                {id.slice(0, 12)}…
              </span>
            ))}
          </div>
        </AlertBanner>
      )}

      {/* Node importance chart */}
      {importanceData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Node Importance Scores</CardTitle>
            <CardDescription>
              Composite structural importance combining betweenness, degree, and closeness centrality
            </CardDescription>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                layout="vertical"
                data={importanceData}
                margin={{ top: 4, right: 32, left: 80, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[0, 1]}
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  stroke="#263650"
                >
                  <Label value="Importance Score" position="insideBottom" offset={-4} fill="#6b7280" fontSize={10} />
                </XAxis>
                <YAxis
                  type="category"
                  dataKey="id"
                  tick={{ fill: '#9ca3af', fontSize: 10 }}
                  stroke="#263650"
                  width={75}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null
                    const d = payload[0]?.payload
                    return (
                      <div className="bg-surface-700 border border-surface-500 rounded-lg px-3 py-2 text-xs">
                        <p className="font-mono text-gray-300">{d?.fullId}</p>
                        <p className="text-primary-300 font-mono">Score: {d?.score?.toFixed(4)}</p>
                      </div>
                    )
                  }}
                  cursor={{ fill: '#1e2d4520' }}
                />
                <Bar dataKey="score" name="Importance" radius={[0, 3, 3, 0]}>
                  {importanceData.map((_, i) => (
                    <Cell
                      key={`cell-${i}`}
                      fill={i === 0 ? '#2563eb' : i <= 2 ? '#3b82f6' : '#1e40af'}
                      fillOpacity={0.9 - i * 0.05}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      )}
    </div>
  )
}
