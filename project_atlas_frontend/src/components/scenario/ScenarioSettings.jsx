import { useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Globe, Lock } from 'lucide-react'
import { Input } from '@/components/ui/Input.jsx'
import { Select } from '@/components/ui/Select.jsx'
import { scenarioSchema } from '@/utils/validators.js'
import { ITERATION_PRESETS } from '@/config/constants.js'
import useScenarioStore from '@/store/scenarioStore.js'
import { clsx } from 'clsx'

export function ScenarioSettings({ onValid }) {
  const draft    = useScenarioStore((s) => s.draft)
  const setDraft = useScenarioStore((s) => s.setDraft)

  const { register, control, watch, formState:{ errors, isValid } } = useForm({
    resolver: zodResolver(scenarioSchema),
    defaultValues: { scenario_name:draft.scenario_name, description:draft.description, time_horizon_days:draft.time_horizon_days, simulation_iterations:draft.simulation_iterations, is_public:draft.is_public },
    mode: 'onChange',
  })

  const values = watch()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setDraft(values) }, [JSON.stringify(values)])
  useEffect(() => { onValid?.(isValid) }, [isValid, onValid])

  const timeHorizon = watch('time_horizon_days')

  return (
    <div className="space-y-6 max-w-2xl">
      <Input label="Scenario Name" placeholder="e.g. Niger Delta Pipeline Disruption 2024" error={errors.scenario_name?.message} required {...register('scenario_name')}/>
      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-gray-300">Description <span className="text-gray-500">(optional)</span></label>
        <textarea rows={3} placeholder="Describe the scenario context…" className="w-full rounded-lg border border-surface-500 bg-surface-700 text-gray-100 text-sm px-3 py-2.5 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 transition-all duration-200" {...register('description')}/>
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between"><label className="text-sm font-medium text-gray-300">Time Horizon <span className="text-red-400">*</span></label><span className="text-sm font-mono font-bold text-primary-300 tabular-nums">{timeHorizon} days</span></div>
        <Controller name="time_horizon_days" control={control} render={({field})=>(
          <input type="range" min={30} max={365} step={30} value={field.value} onChange={(e)=>field.onChange(parseInt(e.target.value,10))} className="w-full h-2 rounded-full appearance-none cursor-pointer bg-surface-600 accent-primary-500"/>
        )}/>
        <div className="flex justify-between text-xs text-gray-500"><span>30 days</span><span>6 months</span><span>1 year</span></div>
      </div>
      <Controller name="simulation_iterations" control={control} render={({field})=>(
        <Select label="Simulation Iterations" options={ITERATION_PRESETS.map((p)=>({label:p.label,value:String(p.value)}))} value={String(field.value)} onChange={(e)=>field.onChange(parseInt(e.target.value,10))} error={errors.simulation_iterations?.message} required/>
      )}/>
      <div className="space-y-1.5">
        <label className="block text-sm font-medium text-gray-300">Visibility</label>
        <Controller name="is_public" control={control} render={({field})=>(
          <div className="flex rounded-lg border border-surface-500 overflow-hidden">
            {[{value:false,label:'Private',Icon:Lock,desc:'Only you can see this'},{value:true,label:'Public',Icon:Globe,desc:'Visible to all users'}].map(({value,label,Icon,desc})=>(
              <button key={String(value)} type="button" onClick={()=>field.onChange(value)}
                className={clsx('flex-1 flex items-center gap-2 px-4 py-3 text-sm transition-all duration-150',field.value===value?'bg-primary-600/20 text-primary-300':'bg-surface-700 text-gray-400 hover:text-gray-200 hover:bg-surface-600 border-r border-surface-500')}>
                <Icon className="w-4 h-4 flex-shrink-0"/>
                <div className="text-left"><div className="font-medium">{label}</div><div className="text-2xs opacity-70">{desc}</div></div>
              </button>
            ))}
          </div>
        )}/>
      </div>
    </div>
  )
}
