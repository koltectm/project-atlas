/**
 * src/pages/ComparePage.jsx
 * ============================
 * Run comparison page. Lets the user pick two completed runs and
 * renders the ScenarioComparison chart + table.
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { GitCompare } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader.jsx'
import { Select } from '@/components/ui/Select.jsx'
import { Card, CardBody } from '@/components/ui/Card.jsx'
import { ScenarioComparison } from '@/components/results/ScenarioComparison.jsx'
import { scenarioService } from '@/services/scenarioService.js'
import { simulationService } from '@/services/simulationService.js'

export function ComparePage() {
  const { runId1: paramRun1, runId2: paramRun2 } = useParams()
  const navigate = useNavigate()

  const [scenarioId, setScenarioId] = useState('')
  const [runId1, setRunId1] = useState(paramRun1 || '')
  const [runId2, setRunId2] = useState(paramRun2 || '')

  const { data: scenariosData } = useQuery({
    queryKey: ['scenarios', 'mine'],
    queryFn:  () => scenarioService.getMine({ limit: 100 }).then((r) => r.data),
  })
  const scenarios = scenariosData?.items || []

  const { data: runs = [] } = useQuery({
    queryKey: ['runs-for-scenario', scenarioId],
    queryFn:  () => simulationService.getRunsForScenario(scenarioId).then((r) => r.data),
    enabled:  !!scenarioId,
  })

  const completedRuns = runs.filter((r) => r.status === 'completed')

  useEffect(() => {
    if (runId1 && runId2) {
      navigate(`/compare/${runId1}/${runId2}`, { replace: true })
    }
  }, [runId1, runId2, navigate])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Compare Simulation Runs"
        description="Side-by-side comparison of aggregate statistics between two completed runs"
      />

      <Card>
        <CardBody className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Select
            label="Scenario"
            placeholder="Select a scenario…"
            options={scenarios.map((s) => ({ label: s.scenario_name, value: s.scenario_id }))}
            value={scenarioId}
            onChange={(e) => { setScenarioId(e.target.value); setRunId1(''); setRunId2('') }}
          />
          <Select
            label="Run A"
            placeholder="Select first run…"
            options={completedRuns.map((r) => ({
              label: `${r.run_id.slice(0, 8)}… (${new Date(r.started_at).toLocaleDateString()})`,
              value: r.run_id,
            }))}
            value={runId1}
            onChange={(e) => setRunId1(e.target.value)}
            disabled={!scenarioId}
          />
          <Select
            label="Run B"
            placeholder="Select second run…"
            options={completedRuns
              .filter((r) => r.run_id !== runId1)
              .map((r) => ({
                label: `${r.run_id.slice(0, 8)}… (${new Date(r.started_at).toLocaleDateString()})`,
                value: r.run_id,
              }))}
            value={runId2}
            onChange={(e) => setRunId2(e.target.value)}
            disabled={!scenarioId}
          />
        </CardBody>
      </Card>

      <ScenarioComparison
        runId1={runId1 || paramRun1}
        runId2={runId2 || paramRun2}
        label1="Run A"
        label2="Run B"
      />
    </div>
  )
}
