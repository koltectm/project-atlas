import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight, ChevronLeft, Save, Play, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button.jsx'
import { AlertBanner } from '@/components/ui/AlertBanner.jsx'
import { ScenarioSettings } from './ScenarioSettings.jsx'
import { DisruptionPicker } from './DisruptionPicker.jsx'
import { DisruptionCard } from './DisruptionCard.jsx'
import useScenarioStore from '@/store/scenarioStore.js'
import useSimulationStore from '@/store/simulationStore.js'
import { useScenarioMutations } from '@/hooks/useScenario.js'
import { simulationService } from '@/services/simulationService.js'
import { formatIterations } from '@/utils/formatters.js'

const STEPS = [{label:'Configure',desc:'Name, horizon, iterations'},{label:'Disruptions',desc:'Select what can go wrong'},{label:'Review',desc:'Confirm and launch'}]

function StepIndicator({ currentStep }) {
  return (
    <div className="flex items-center gap-0">
      {STEPS.map((step,i)=>(
        <div key={i} className="flex items-center">
          <div className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${i<currentStep?'bg-accent-500 text-white':i===currentStep?'bg-primary-600 text-white ring-2 ring-primary-500/40':'bg-surface-600 text-gray-400'}`}>
              {i<currentStep?<CheckCircle2 className="w-4 h-4"/>:i+1}
            </div>
            <div className="hidden sm:block"><p className={`text-xs font-medium ${i===currentStep?'text-white':'text-gray-500'}`}>{step.label}</p><p className="text-2xs text-gray-600">{step.desc}</p></div>
          </div>
          {i<STEPS.length-1 && <div className={`w-12 h-px mx-3 ${i<currentStep?'bg-accent-500':'bg-surface-500'}`}/>}
        </div>
      ))}
    </div>
  )
}

export function ScenarioBuilder() {
  const navigate     = useNavigate()
  const draft        = useScenarioStore((s) => s.draft)
  const currentStep  = useScenarioStore((s) => s.currentStep)
  const nextStep     = useScenarioStore((s) => s.nextStep)
  const prevStep     = useScenarioStore((s) => s.prevStep)
  const addDisruption    = useScenarioStore((s) => s.addDisruption)
  const updateDisruption = useScenarioStore((s) => s.updateDisruption)
  const removeDisruption = useScenarioStore((s) => s.removeDisruption)
  const resetDraft       = useScenarioStore((s) => s.resetDraft)
  const setActiveRun     = useSimulationStore((s) => s.setActiveRun)
  const { createScenario } = useScenarioMutations()
  const [step0Valid, setStep0Valid] = useState(false)
  const [isSaving,  setIsSaving]   = useState(false)

  const selectedIds = new Set(draft.disruptions.map((d) => d.disruption_type_id))

  const buildPayload = () => ({
    scenario_name:draft.scenario_name, description:draft.description||undefined,
    time_horizon_days:draft.time_horizon_days, simulation_iterations:draft.simulation_iterations,
    is_public:draft.is_public, tags:draft.tags||[],
    disruptions:draft.disruptions.map((d)=>({
      disruption_type_id:d.disruption_type_id,
      probability_override:d.probability_override!=null?d.probability_override:undefined,
      severity_override:d.severity_override!=null?d.severity_override:undefined,
      target_node_id:d.target_node_id||undefined, target_link_id:d.target_link_id||undefined,
      is_active:d.is_active!==false,
    })),
  })

  const handleSave = async () => {
    setIsSaving(true)
    try { const s=await createScenario.mutateAsync(buildPayload()); resetDraft(); navigate(`/scenarios/${s.scenario_id}`) }
    catch {} finally { setIsSaving(false) }
  }

  const handleSaveAndRun = async () => {
    setIsSaving(true)
    try {
      const s=await createScenario.mutateAsync(buildPayload())
      const { data:run }=await simulationService.run(s.scenario_id)
      setActiveRun(run); resetDraft(); toast.success('Simulation queued!'); navigate(`/simulation/${run.run_id}`)
    } catch {} finally { setIsSaving(false) }
  }

  return (
    <div className="flex flex-col gap-6 h-full">
      <StepIndicator currentStep={currentStep}/>
      <AnimatePresence mode="wait">
        <motion.div key={currentStep} initial={{opacity:0,x:12}} animate={{opacity:1,x:0}} exit={{opacity:0,x:-12}} transition={{duration:0.18}} className="flex-1">
          {currentStep===0 && <ScenarioSettings onValid={setStep0Valid}/>}
          {currentStep===1 && (
            <div className="grid grid-cols-2 gap-6 h-full min-h-96">
              <div className="flex flex-col"><h3 className="text-sm font-semibold text-white mb-3">Disruption Library</h3><div className="flex-1 overflow-hidden"><DisruptionPicker selectedIds={selectedIds} onAdd={addDisruption}/></div></div>
              <div className="flex flex-col">
                <div className="flex items-center justify-between mb-3"><h3 className="text-sm font-semibold text-white">Selected Disruptions</h3><span className="text-xs text-gray-400 font-mono">{draft.disruptions.length} added</span></div>
                {draft.disruptions.length===0
                  ? <div className="flex-1 flex items-center justify-center rounded-xl border border-dashed border-surface-500"><p className="text-sm text-gray-500 text-center px-4">Add disruptions from the library on the left</p></div>
                  : <div className="flex-1 overflow-y-auto space-y-2 pr-1">{draft.disruptions.map((d,i)=><DisruptionCard key={`${d.disruption_type_id}-${i}`} disruption={d} index={i} onUpdate={updateDisruption} onRemove={removeDisruption}/>)}</div>}
              </div>
            </div>
          )}
          {currentStep===2 && (
            <div className="max-w-2xl space-y-6">
              <AlertBanner variant="info">Review your scenario before saving.</AlertBanner>
              <div className="rounded-xl border border-surface-500 bg-surface-700 overflow-hidden">
                <div className="px-5 py-4 border-b border-surface-500"><h3 className="text-base font-semibold text-white">{draft.scenario_name}</h3>{draft.description&&<p className="text-sm text-gray-400 mt-1">{draft.description}</p>}</div>
                <div className="px-5 py-4 grid grid-cols-3 gap-4 text-sm">
                  <div><p className="text-gray-400 mb-1">Time Horizon</p><p className="font-mono font-semibold text-white">{draft.time_horizon_days} days</p></div>
                  <div><p className="text-gray-400 mb-1">Iterations</p><p className="font-mono font-semibold text-white">{formatIterations(draft.simulation_iterations)}</p></div>
                  <div><p className="text-gray-400 mb-1">Visibility</p><p className="font-semibold text-white">{draft.is_public?'Public':'Private'}</p></div>
                </div>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white mb-3">Disruptions ({draft.disruptions.length})</h4>
                <div className="space-y-2">{draft.disruptions.map((d,i)=>(
                  <div key={i} className="flex items-center justify-between rounded-lg border border-surface-500 bg-surface-700 px-4 py-2.5">
                    <p className="text-sm font-medium text-white">{d._name}</p>
                    <p className="text-xs text-gray-400">p={((d.probability_override??d._default_probability??0)*100).toFixed(1)}%</p>
                  </div>
                ))}</div>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
      <div className="flex items-center justify-between pt-4 border-t border-surface-500">
        <Button variant="secondary" icon={ChevronLeft} onClick={prevStep} disabled={currentStep===0}>Back</Button>
        <div className="flex items-center gap-3">
          {currentStep<2
            ? <Button variant="primary" iconRight={ChevronRight} onClick={nextStep} disabled={(currentStep===0&&!step0Valid)||(currentStep===1&&draft.disruptions.length===0)}>Continue</Button>
            : <><Button variant="secondary" icon={Save} loading={isSaving} onClick={handleSave}>Save Draft</Button><Button variant="primary" icon={Play} loading={isSaving} onClick={handleSaveAndRun}>Save & Run Now</Button></>}
        </div>
      </div>
    </div>
  )
}
