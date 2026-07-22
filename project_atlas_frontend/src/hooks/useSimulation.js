import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { simulationService } from '@/services/simulationService.js'
import useSimulationStore from '@/store/simulationStore.js'
import { SIMULATION_POLL_INTERVAL_MS, RESULTS_REDIRECT_DELAY_MS } from '@/config/constants.js'

export function useSimulation(runId, { autoNavigate=true }={}) {
  const navigate     = useNavigate()
  const setActiveRun = useSimulationStore((s) => s.setActiveRun)
  const activeStatus = useSimulationStore((s) => s.activeRunStatus)
  const progressPct  = useSimulationStore((s) => s.progressPct)
  const isPolling    = useSimulationStore((s) => s.isPolling)

  const isActive = !!runId && ['queued','running'].includes(activeStatus)

  const { data: run, error } = useQuery({
    queryKey: ['simulation-run', runId],
    queryFn:  () => simulationService.getStatus(runId).then((r) => r.data),
    enabled:  !!runId,
    refetchInterval: isActive ? SIMULATION_POLL_INTERVAL_MS : false,
    refetchIntervalInBackground: false,
  })

  useEffect(() => {
    if (!run) return
    setActiveRun(run)
    if (run.status==='completed' && autoNavigate) {
      setTimeout(() => navigate(`/results/${runId}`, { replace:false }), RESULTS_REDIRECT_DELAY_MS)
    }
  }, [run, runId, autoNavigate, navigate, setActiveRun])

  const triggerRun = useCallback(async (scenarioId) => {
    const { data } = await simulationService.run(scenarioId)
    setActiveRun(data)
    return data
  }, [setActiveRun])

  return {
    run, error, progressPct, isPolling,
    status:      run?.status || null,
    isCompleted: run?.status === 'completed',
    isFailed:    run?.status === 'failed',
    triggerRun,
  }
}
