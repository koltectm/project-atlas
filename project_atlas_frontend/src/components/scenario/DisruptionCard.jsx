import { X } from 'lucide-react'
import { Card, CardBody } from '@/components/ui/Card.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { DISRUPTION_CATEGORIES } from '@/config/constants.js'
import { formatProbability } from '@/utils/formatters.js'

function Slider({ label, value, onChange, min=0, max=1, step=0.01 }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs"><span className="text-gray-400">{label}</span><span className="font-mono text-gray-200">{Math.round((value??0)*100)}%</span></div>
      <input type="range" min={min} max={max} step={step} value={value??0} onChange={(e)=>onChange(parseFloat(e.target.value))} className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-surface-600 accent-primary-500"/>
    </div>
  )
}

export function DisruptionCard({ disruption, index, onUpdate, onRemove }) {
  const catInfo = DISRUPTION_CATEGORIES[disruption._category] || {}
  return (
    <Card className="border-l-2" style={{borderLeftColor:catInfo.color||'#6b7280'}}>
      <CardBody className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-sm font-medium text-white">{disruption._name}</p>
            <p className="text-2xs text-gray-500 mt-0.5">base p={formatProbability(disruption._default_probability)}</p>
          </div>
          <Button size="xs" variant="ghost" onClick={()=>onRemove(index)} className="text-gray-500 hover:text-red-400"><X className="w-3.5 h-3.5"/></Button>
        </div>
        <Slider label="Probability override" value={disruption.probability_override??disruption._default_probability??0} onChange={(v)=>onUpdate(index,{probability_override:v})}/>
        <Slider label="Severity override" value={disruption.severity_override??0.5} onChange={(v)=>onUpdate(index,{severity_override:v})}/>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">Active in simulation</span>
          <button onClick={()=>onUpdate(index,{is_active:!disruption.is_active})} className={`relative w-9 h-5 rounded-full transition-colors duration-200 ${disruption.is_active?'bg-primary-600':'bg-surface-600'}`}>
            <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${disruption.is_active?'translate-x-4':'translate-x-0.5'}`}/>
          </button>
        </div>
      </CardBody>
    </Card>
  )
}
