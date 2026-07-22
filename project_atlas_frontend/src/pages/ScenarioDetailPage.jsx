/**
 * src/pages/ScenarioDetailPage.jsx
 * ===================================
 * Handles three modes: create (new scenario wizard), view (read-only +
 * run history), edit (re-opens the builder pre-populated).
 */
import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Play } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { Spinner } from '@/components/ui/Spinner.jsx'
import { StatusBadge } from '@/components/ui/Badge.jsx'
import { ScenarioBuilder } from '@/components/scenario/ScenarioBuilder.jsx'
import { SimulationLauncher } from '@/components/simulation/SimulationLauncher.jsx'
import { RunHistory } from '@/components/simulation/RunHistory.jsx'
import { useScenario } from '@/hooks/useScenario.js'
import useScenarioStore from '@/store/scenarioStore.js'

export function ScenarioDetailPage({ mode = 'view' }) {
  const { id }   = useParams()
  const navigate = useNavigate()
  const resetDraft         = useScenarioStore((s) => s.resetDraft)
  const loadScenarioForEdit= useScenarioStore((s) => s.loadScenarioForEdit)

  const { scenario, isLoading } = useScenario(mode !== 'create' ? id : null)

  // Reset draft for create mode; load existing scenario for edit mode
  useEffect(() => {
    if (mode === 'create') {
      resetDraft()
    } else if (mode === 'edit' && scenario) {
      loadScenarioForEdit(scenario)
    }
  }, [mode, scenario, resetDraft, loadScenarioForEdit])

  if (mode === 'create' || mode === 'edit') {
    if (mode === 'edit' && isLoading) {
      return <div className="flex justify-center py-24"><Spinner size="lg" /></div>
    }
    return (
      <div className="space-y-6">
        <PageHeader
          title={mode === 'create' ? 'New Scenario' : 'Edit Scenario'}
          description="Configure disruption parameters for Monte Carlo stress-testing"
          actions={
            <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate('/scenarios')}>
              Back to Scenarios
            </Button>
          }
        />
        <ScenarioBuilder initialScenarioId={mode === 'edit' ? id : undefined} />
      </div>
    )
  }

  // View mode
  if (isLoading) {
    return <div className="flex justify-center py-24"><Spinner size="lg" /></div>
  }

  if (!scenario) {
    return (
      <div className="text-center py-24">
        <p className="text-gray-400">Scenario not found.</p>
        <Button variant="primary" className="mt-4" onClick={() => navigate('/scenarios')}>
          Back to Scenarios
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={scenario.scenario_name}
        description={scenario.description}
        actions={
          <div className="flex items-center gap-3">
            <StatusBadge status={scenario.status} />
            <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate('/scenarios')}>
              Back
            </Button>
            <Button
              variant="secondary"
              onClick={() => navigate(`/scenarios/${id}/edit`)}
            >
              Edit
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: launcher */}
        <div className="lg:col-span-1">
          <h3 className="text-sm font-semibold text-white mb-3">Run Simulation</h3>
          <SimulationLauncher scenario={scenario} />
        </div>

        {/* Right: disruptions + history */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-white mb-3">
              Configured Disruptions ({scenario.disruptions?.length || 0})
            </h3>
            <div className="space-y-2">
              {scenario.disruptions?.length === 0 && (
                <p className="text-sm text-gray-500">No disruptions configured.</p>
              )}
              {scenario.disruptions?.map((d) => (
                <div
                  key={d.scenario_disruption_id}
                  className="rounded-lg border border-surface-500 bg-surface-700 px-4 py-3 flex items-center justify-between"
                >
                  <span className="text-sm text-gray-200">
                    Disruption: {d.disruption_type_id?.slice(0, 8)}…
                  </span>
                  <span className="text-xs text-gray-500">
                    {d.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Run History</h3>
            <RunHistory scenarioId={id} />
          </div>
        </div>
      </div>
    </div>
  )
}
