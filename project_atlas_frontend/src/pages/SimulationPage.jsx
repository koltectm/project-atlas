/**
 * src/pages/SimulationPage.jsx
 */
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { EmptyState } from '@/components/ui/EmptyState.jsx'
import { ProgressTracker } from '@/components/simulation/ProgressTracker.jsx'
import { Play } from 'lucide-react'
import useSimulationStore from '@/store/simulationStore.js'

export function SimulationPage() {
  const { runId: paramRunId } = useParams()
  const navigate = useNavigate()
  const activeRunId = useSimulationStore((s) => s.activeRunId)

  const runId = paramRunId || activeRunId

  if (!runId) {
    return (
      <div className="space-y-6">
        <PageHeader title="Simulation Runner" />
        <EmptyState
          icon={Play}
          title="No active simulation"
          description="Start a simulation from a scenario to track its progress here."
          action={
            <Button variant="primary" onClick={() => navigate('/scenarios')}>
              Go to Scenarios
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Simulation Progress"
        breadcrumb={`Run ${runId.slice(0, 8)}…`}
        actions={
          <Button variant="ghost" icon={ArrowLeft} onClick={() => navigate('/scenarios')}>
            Back to Scenarios
          </Button>
        }
      />
      <ProgressTracker runId={runId} />
    </div>
  )
}
