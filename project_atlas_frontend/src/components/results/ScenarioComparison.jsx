/**
 * src/components/results/ScenarioComparison.jsx
 * ================================================
 * Side-by-side bar comparison of two simulation runs' aggregate metrics.
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Label,
} from 'recharts'
import { GitCompare } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardBody } from '@/components/ui/Card.jsx'
import { Spinner } from '@/components/ui/Spinner.jsx'
import { EmptyState } from '@/components/ui/EmptyState.jsx'
import { useRunComparison } from '@/hooks/useResults.js'
import { buildComparisonData } from '@/utils/chartHelpers.js'
import { formatUSD, formatUSDAxis } from '@/utils/formatters.js'

const METRIC_LABELS = {
  total_cost_usd:          'Total Cost',
  total_delay_days:        'Delay (days)',
  production_loss_barrels: 'Production Loss',
  supply_chain_flow_pct:   'Flow %',
  recovery_time_days:      'Recovery (days)',
}

export function ScenarioComparison({ runId1, runId2, label1 = 'Run A', label2 = 'Run B' }) {
  const { comparison, isLoading, error } = useRunComparison(runId1, runId2)

  if (!runId1 || !runId2) {
    return (
      <Card>
        <EmptyState
          icon={GitCompare}
          title="Select two runs to compare"
          description="Choose two completed simulation runs from the Compare page."
        />
      </Card>
    )
  }

  if (isLoading) {
    return (
      <Card className="h-80 flex items-center justify-center">
        <Spinner />
      </Card>
    )
  }

  if (error || !comparison) {
    return (
      <Card>
        <EmptyState
          icon={GitCompare}
          title="Comparison unavailable"
          description={error?.message || 'Could not load comparison data.'}
        />
      </Card>
    )
  }

  const chartData = buildComparisonData(comparison, label1, label2)
    .map((d) => ({ ...d, metric: METRIC_LABELS[d.metric] || d.metric }))
    .filter((d) => d.metric === 'Total Cost' || d.metric === 'Recovery (days)' || d.metric === 'Delay (days)')

  return (
    <Card id="chart-comparison">
      <CardHeader>
        <CardTitle>Scenario Comparison</CardTitle>
        <CardDescription>
          {label1} vs {label2} — mean values across key metrics
        </CardDescription>
      </CardHeader>
      <CardBody>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 8, right: 24, left: 16, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2d45" />
            <XAxis dataKey="metric" tick={{ fill: '#9ca3af', fontSize: 11 }} stroke="#263650" />
            <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} stroke="#263650" />
            <Tooltip
              contentStyle={{ background: '#162035', border: '1px solid #263650', borderRadius: 8 }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
            <Bar dataKey={label1} fill="#3b82f6" radius={[3, 3, 0, 0]} />
            <Bar dataKey={label2} fill="#16a34a" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>

        {/* Delta table */}
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-500 text-left text-xs text-gray-400">
                <th className="pb-2">Metric</th>
                <th className="pb-2 text-right">{label1}</th>
                <th className="pb-2 text-right">{label2}</th>
                <th className="pb-2 text-right">Δ%</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(comparison.metrics).map(([metric, vals]) => (
                <tr key={metric} className="border-b border-surface-600">
                  <td className="py-2 text-gray-300">{METRIC_LABELS[metric] || metric}</td>
                  <td className="py-2 text-right font-mono text-gray-200">
                    {metric.includes('cost') ? formatUSD(vals.run_1_mean) : vals.run_1_mean?.toFixed(2)}
                  </td>
                  <td className="py-2 text-right font-mono text-gray-200">
                    {metric.includes('cost') ? formatUSD(vals.run_2_mean) : vals.run_2_mean?.toFixed(2)}
                  </td>
                  <td className={`py-2 text-right font-mono font-semibold ${
                    vals.delta_pct > 0 ? 'text-red-400' : vals.delta_pct < 0 ? 'text-green-400' : 'text-gray-400'
                  }`}>
                    {vals.delta_pct > 0 ? '+' : ''}{vals.delta_pct?.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardBody>
    </Card>
  )
}
