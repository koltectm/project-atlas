/**
 * src/pages/ResultsPage.jsx
 */
import { useParams } from 'react-router-dom'
import { ResultsDashboard } from '@/components/results/ResultsDashboard.jsx'
import { EmptyState } from '@/components/ui/EmptyState.jsx'
import { BarChart3 } from 'lucide-react'

export function ResultsPage() {
  const { runId } = useParams()

  if (!runId) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No run selected"
        description="Select a completed simulation run to view its results."
      />
    )
  }

  return <ResultsDashboard runId={runId} />
}
