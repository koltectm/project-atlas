import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

const useSimulationStore = create(devtools((set) => ({
  activeRunId: null, activeRunStatus: null,
  completedIterations: 0, totalIterations: 0, progressPct: 0,
  liveMetrics: { runningCostEstimate: null, disruptionsTriggered: 0, flowEstimate: null },
  isPolling: false,

  setActiveRun: (run) => set({
    activeRunId: run.run_id, activeRunStatus: run.status,
    completedIterations: run.completed_iterations || 0,
    totalIterations: run.total_iterations || 0,
    progressPct: run.total_iterations > 0 ? Math.round(((run.completed_iterations || 0) / run.total_iterations) * 100) : 0,
    isPolling: ['queued', 'running'].includes(run.status),
  }),

  updateProgress: (completed, total, status) => set({
    completedIterations: completed, totalIterations: total, activeRunStatus: status,
    progressPct: total > 0 ? Math.round((completed / total) * 100) : 0,
    isPolling: ['queued', 'running'].includes(status),
  }),

  clearActiveRun: () => set({
    activeRunId: null, activeRunStatus: null, completedIterations: 0,
    totalIterations: 0, progressPct: 0, isPolling: false,
    liveMetrics: { runningCostEstimate: null, disruptionsTriggered: 0, flowEstimate: null },
  }),
}), { name: 'atlas-simulation' }))

export default useSimulationStore
