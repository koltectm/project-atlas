import { X, Zap } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { StatusBadge, Badge } from '@/components/ui/Badge.jsx'
import { Card, CardBody } from '@/components/ui/Card.jsx'
import { ProgressBar } from '@/components/ui/ProgressBar.jsx'
import { NODE_TYPES, GEO_ZONES, getRiskLevel } from '@/config/constants.js'
import { formatBpd } from '@/utils/formatters.js'

function DetailRow({ label, value, mono=false }) {
  if (value==null||value==='') return null
  return (
    <div className="flex items-start justify-between gap-3 py-1.5 border-b border-surface-600 last:border-0">
      <span className="text-xs text-gray-400 flex-shrink-0">{label}</span>
      <span className={`text-xs text-gray-200 text-right ${mono?'font-mono tabular-nums':''}`}>{value}</span>
    </div>
  )
}

export function NodeCard({ node, onClose }) {
  if (!node) return null
  const data=node.data, typeInfo=NODE_TYPES[data.node_type]||{}, zone=GEO_ZONES[data.geopolitical_zone], risk=getRiskLevel(1-(data.redundancy||0))
  return (
    <AnimatePresence>
      <motion.div key="node-card" initial={{opacity:0,x:20}} animate={{opacity:1,x:0}} exit={{opacity:0,x:20}} transition={{duration:0.2}} className="absolute top-4 right-4 w-72 z-10">
        <Card className="shadow-2xl">
          <div className="flex items-start justify-between p-4 border-b border-surface-500">
            <div className="flex items-center gap-2.5 flex-1 min-w-0">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{backgroundColor:`${typeInfo.color||'#6b7280'}22`,border:'1px solid',borderColor:`${typeInfo.color||'#6b7280'}44`}}>
                <Zap className="w-4 h-4" style={{color:typeInfo.color||'#6b7280'}}/>
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-white truncate">{data.label||data.node_code}</p>
                <p className="text-xs text-gray-400">{typeInfo.label||data.node_type}</p>
              </div>
            </div>
            <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:text-white hover:bg-surface-600 transition-colors flex-shrink-0 ml-2"><X className="w-3.5 h-3.5"/></button>
          </div>
          <CardBody className="space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge status={data.status}/>
              <Badge variant="default">{data.stage}</Badge>
              {zone && <Badge variant="default" style={{borderColor:zone.color+'66',color:zone.color}}>{data.geopolitical_zone}</Badge>}
            </div>
            {data.capacity_bpd>0 && <ProgressBar value={data.utilization*100} max={100} label="Utilisation" color={data.utilization>0.9?'danger':data.utilization>0.7?'warning':'success'}/>}
            <div>
              <DetailRow label="Capacity"    value={data.capacity_bpd>0?formatBpd(data.capacity_bpd):'—'} mono/>
              <DetailRow label="Operator"    value={data.operator}/>
              <DetailRow label="Criticality" value={data.criticality?`${(data.criticality*100).toFixed(0)}%`:'—'} mono/>
              <DetailRow label="Redundancy"  value={data.redundancy?`${(data.redundancy*100).toFixed(0)}%`:'—'} mono/>
              <DetailRow label="Zone"        value={zone?.label}/>
            </div>
            <div className={`rounded-lg px-3 py-2 border ${risk.bg} ${risk.border}`}>
              <p className="text-xs" style={{color:risk.color}}><span className="font-semibold">{risk.label} redundancy risk</span></p>
            </div>
          </CardBody>
        </Card>
      </motion.div>
    </AnimatePresence>
  )
}
