import { useNavigate } from 'react-router-dom'
import { Play, Edit2, Trash2, Copy, FlaskConical, Lock, Globe } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card, CardBody } from '@/components/ui/Card.jsx'
import { StatusBadge, Badge } from '@/components/ui/Badge.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { Tooltip } from '@/components/ui/Tooltip.jsx'
import { formatRelative, formatIterations } from '@/utils/formatters.js'
import { DISRUPTION_CATEGORIES } from '@/config/constants.js'
import useAuthStore from '@/store/authStore.js'

export function ScenarioCard({ scenario, onDelete, onRun, onClone }) {
  const navigate  = useNavigate()
  const canRun    = useAuthStore((s) => s.canRunSimulations)()
  const userId    = useAuthStore((s) => s.profile?.profile_id)
  const isOwner   = scenario.created_by === userId
  const isAnalyst = useAuthStore((s) => s.isAnalyst)()

  const categories = [...new Set((scenario.disruptions||[]).map((d)=>d._category).filter(Boolean))].slice(0,3)

  return (
    <motion.div initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:0.2}}>
      <Card hover className="h-full flex flex-col">
        <CardBody className="flex flex-col gap-3 h-full">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-primary-900/50 border border-primary-700/50 flex items-center justify-center flex-shrink-0"><FlaskConical className="w-4 h-4 text-primary-400"/></div>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-white truncate">{scenario.scenario_name}</h3>
                <div className="flex items-center gap-1.5 mt-0.5"><StatusBadge status={scenario.status}/>{scenario.is_public?<Globe className="w-3 h-3 text-gray-500"/>:<Lock className="w-3 h-3 text-gray-500"/>}</div>
              </div>
            </div>
          </div>
          {scenario.description && <p className="text-xs text-gray-400 line-clamp-2">{scenario.description}</p>}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-surface-700 rounded-lg px-2.5 py-1.5"><p className="text-gray-500">Disruptions</p><p className="font-mono font-semibold text-white">{scenario.disruptions?.length||0}</p></div>
            <div className="bg-surface-700 rounded-lg px-2.5 py-1.5"><p className="text-gray-500">Iterations</p><p className="font-mono font-semibold text-white">{formatIterations(scenario.simulation_iterations)}</p></div>
          </div>
          {categories.length>0 && (
            <div className="flex flex-wrap gap-1">
              {categories.map((cat)=>{ const ci=DISRUPTION_CATEGORIES[cat]; return <span key={cat} className="px-1.5 py-0.5 text-2xs rounded-md border" style={{backgroundColor:(ci?.color||'#6b7280')+'18',borderColor:(ci?.color||'#6b7280')+'44',color:ci?.color||'#9ca3af'}}>{ci?.label||cat}</span> })}
            </div>
          )}
          <div className="flex-1"/>
          <div className="flex items-center justify-between pt-2 border-t border-surface-600">
            <span className="text-2xs text-gray-500">{formatRelative(scenario.updated_at)}</span>
            <div className="flex items-center gap-1">
              {canRun && <Tooltip content="Run"><Button size="xs" variant="primary" onClick={()=>onRun?.(scenario)}><Play className="w-3 h-3"/></Button></Tooltip>}
              <Tooltip content="View"><Button size="xs" variant="secondary" onClick={()=>navigate(`/scenarios/${scenario.scenario_id}`)}><Edit2 className="w-3 h-3"/></Button></Tooltip>
              {isAnalyst && <Tooltip content="Clone"><Button size="xs" variant="ghost" onClick={()=>onClone?.(scenario)}><Copy className="w-3 h-3"/></Button></Tooltip>}
              {isOwner && <Tooltip content="Delete"><Button size="xs" variant="danger" onClick={()=>onDelete?.(scenario.scenario_id)}><Trash2 className="w-3 h-3"/></Button></Tooltip>}
            </div>
          </div>
        </CardBody>
      </Card>
    </motion.div>
  )
}
