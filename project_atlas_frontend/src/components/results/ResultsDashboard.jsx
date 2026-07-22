/**
 * src/components/results/ResultsDashboard.jsx
 * ==============================================
 * Main container assembling all results sub-components per spec layout:
 *   Row 1: SummaryStats (6 cards)
 *   Row 2: CostDistribution (60%) | FlowDistribution (40%)
 *   Row 3: VulnerabilityHeatmap (50%) | CriticalPathViz (50%)
 *   Row 4: MitigationPanel (full width)
 *   Row 5: ScenarioComparison (if comparison active)
 *   Bottom: IterationTable + ExportPanel
 */
import { useQuery } from '@tanstack/react-query'
import { useResults } from '@/hooks/useResults.js'
import { simulationService } from '@/services/simulationService.js'
import { scenarioService } from '@/services/scenarioService.js'
import { SummaryStats }        from './SummaryStats.jsx'
import { CostDistribution }    from './CostDistribution.jsx'
import { FlowDistribution }    from './FlowDistribution.jsx'
import { VulnerabilityHeatmap }from './VulnerabilityHeatmap.jsx'
import { CriticalPathViz }     from './CriticalPathViz.jsx'
import { MitigationPanel }     from './MitigationPanel.jsx'
import { IterationTable }      from './IterationTable.jsx'
import { ExportPanel }         from './ExportPanel.jsx'
import { PageHeader }          from '@/components/layout/PageHeader.jsx'
import { Badge, StatusBadge }  from '@/components/ui/Badge.jsx'
import { Spinner }             from '@/components/ui/Spinner.jsx'
import { AlertBanner }         from '@/components/ui/AlertBanner.jsx'
import { formatDateTime, formatIterations } from '@/utils/formatters.js'

export function ResultsDashboard({ runId }) {
  const { aggregates, keyed, vulnerability, isLoading, error } = useResults(runId)

  const { data: run } = useQuery({
    queryKey: ['simulation-run-meta', runId],
    queryFn:  () => simulationService.getStatus(runId).then((r) => r.data),
    enabled:  !!runId,
  })

  const { data: scenario } = useQuery({
    queryKey: ['scenario-for-run', run?.scenario_id],
    queryFn:  () => scenarioService.getById(run.scenario_id).then((r) => r.data),
    enabled:  !!run?.scenario_id,
  })

  if (error) {
    return (
      <AlertBanner variant="error" title="Failed to load results">
        {error.message || 'The simulation run was not found or has no results.'}
      </AlertBanner>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={scenario?.scenario_name || 'Simulation Results'}
        description={scenario?.description}
        breadcrumb={`Run ${runId?.slice(0, 8)}…`}
        actions={
          <div className="flex items-center gap-2">
            {run && <StatusBadge status={run.status} />}
            {run && (
              <Badge variant="default">
                {formatIterations(run.total_iterations)} iterations
              </Badge>
            )}
          </div>
        }
      />

      {run && (
        <p className="text-xs text-gray-500 -mt-4">
          Completed {formatDateTime(run.completed_at)} ·
          {' '}Started {formatDateTime(run.started_at)}
        </p>
      )}

      {/* Row 1: Summary stats */}
      <SummaryStats keyed={keyed} loading={isLoading} />

      {/* Row 2: Cost + Flow distributions */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3">
          <CostDistribution runId={runId} keyed={keyed} />
        </div>
        <div className="lg:col-span-2">
          <FlowDistribution runId={runId} keyed={keyed} />
        </div>
      </div>

      {/* Row 3: Vulnerability + Critical path */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <VulnerabilityHeatmap vulnerability={vulnerability} isLoading={isLoading} />
        <CriticalPathViz />
      </div>

      {/* Row 4: Mitigation optimiser */}
      <MitigationPanel />

      {/* Bottom: Iteration table + export */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <IterationTable runId={runId} />
        </div>
        <div>
          <ExportPanel
            runId={runId}
            aggregates={aggregates}
            vulnerability={vulnerability}
            scenarioName={scenario?.scenario_name}
          />
        </div>
      </div>
    </div>
  )
}
