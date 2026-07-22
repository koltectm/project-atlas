import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Clock, Layers, Zap } from 'lucide-react'
import toast from 'react-hot-toast'
import { Button } from '@/components/ui/Button.jsx'
import { Card, CardBody } from '@/components/ui/Card.jsx'
import { AlertBanner } from '@/components/ui/AlertBanner.jsx'
import { simulationService } from '@/services/simulationService.js'
import useSimulationStore from '@/store/simulationStore.js'
import useAuthStore from '@/store/authStore.js'
import { formatIterations } from '@/utils/formatters.js'

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-surface-600 last:border-0">
      <div className="flex items-center gap-2 text-sm text-gray-400"><Icon className="w-4 h-4"/>{label}</div>
      <span className="text-sm font-medium text-gray-200 font-mono tabular-nums">{value}</span>
    </div>
  )
}

export function SimulationLauncher({ scenario }) {
  const navigate     = useNavigate()
  const setActiveRun = useSimulationStore((s) => s.setActiveRun)
  const activeStatus = useSimulationStore((s) => s.activeRunStatus)
  const canRun       = useAuthStore((s) => s.canRunSimulations)()
  const [launching, setLaunching] = useState(false)

  const isAlreadyRunning = ['queued','running'].includes(activeStatus)
  const iters            = scenario?.simulation_iterations ?? 10_000
  const estimatedTime    = iters<=1_000?'< 1 second':iters<=10_000?'~0.1–2 seconds':iters<=50_000?'~2–15 seconds':'~15–60 seconds'

  const handleRun = async () => {
    if (!scenario?.scenario_id) return
    setLaunching(true)
    try {
      const { data: run } = await simulationService.run(scenario.scenario_id)
      setActiveRun(run)
      toast.success('Simulation queued successfully')
      navigate(`/simulation/${run.run_id}`)
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to start simulation')
    } finally {
      setLaunching(false)
    }
  }

  if (!scenario) return null

  return (
    <div className="space-y-4">
      <Card>
        <CardBody className="space-y-0 divide-y divide-surface-600">
          <InfoRow icon={Layers} label="Disruptions configured"    value={scenario.disruptions?.length ?? 0}/>
          <InfoRow icon={Zap}    label="Monte Carlo iterations"    value={formatIterations(iters)}/>
          <InfoRow icon={Clock}  label="Time horizon"              value={`${scenario.time_horizon_days} days`}/>
          <InfoRow icon={Clock}  label="Estimated run time"        value={estimatedTime}/>
        </CardBody>
      </Card>
      {!canRun            && <AlertBanner variant="warning">Analyst or Admin role required to run simulations.</AlertBanner>}
      {isAlreadyRunning   && <AlertBanner variant="info">A simulation is already in progress.</AlertBanner>}
      {(scenario.disruptions?.length??0)===0 && <AlertBanner variant="warning">Add at least one disruption before running.</AlertBanner>}
      <Button variant="primary" size="lg" icon={Play} onClick={handleRun} loading={launching}
        disabled={!canRun||isAlreadyRunning||(scenario.disruptions?.length??0)===0||launching} className="w-full">
        {launching?'Queuing…':'Run Simulation'}
      </Button>
    </div>
  )
}
