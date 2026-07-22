import { X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Badge } from '@/components/ui/Badge.jsx'
import { Card, CardBody } from '@/components/ui/Card.jsx'
import { ProgressBar } from '@/components/ui/ProgressBar.jsx'
import { LINK_TYPES } from '@/config/constants.js'
import { formatBpd, formatNumber } from '@/utils/formatters.js'

function DetailRow({ label, value, mono=false }) {
  if (value==null||value==='') return null
  return (
    <div className="flex items-start justify-between gap-3 py-1.5 border-b border-surface-600 last:border-0">
      <span className="text-xs text-gray-400 flex-shrink-0">{label}</span>
      <span className={`text-xs text-gray-200 text-right ${mono?'font-mono tabular-nums':''}`}>{value}</span>
    </div>
  )
}

export function LinkDetail({ edge, onClose }) {
  if (!edge) return null
  const data=edge.data, typeInfo=LINK_TYPES[data.link_type]||{}
  return (
    <AnimatePresence>
      <motion.div key="link-detail" initial={{opacity:0,y:-10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} transition={{duration:0.2}} className="absolute top-4 left-1/2 -translate-x-1/2 w-72 z-10">
        <Card className="shadow-2xl">
          <div className="flex items-center justify-between p-4 border-b border-surface-500">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-2 rounded-full flex-shrink-0" style={{backgroundColor:typeInfo.color||'#3b82f6'}}/>
              <div><p className="text-sm font-semibold text-white">{data.link_code||edge.id}</p><p className="text-xs text-gray-400">{typeInfo.label||data.link_type}</p></div>
            </div>
            <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:text-white hover:bg-surface-600 transition-colors"><X className="w-3.5 h-3.5"/></button>
          </div>
          <CardBody className="space-y-4">
            <div className="flex gap-2 flex-wrap">
              <Badge variant={data.status==='operational'?'success':data.status==='degraded'?'warning':'danger'}>{data.status||'unknown'}</Badge>
              {data.is_critical_path && <Badge variant="warning">Critical Path</Badge>}
            </div>
            <ProgressBar value={(data.reliability_score||0)*100} max={100} label="Reliability" color={(data.reliability_score||0)<0.6?'danger':(data.reliability_score||0)<0.8?'warning':'success'}/>
            <div>
              <DetailRow label="Max Capacity" value={formatBpd(data.max_capacity_bpd)} mono/>
              <DetailRow label="Distance"     value={data.distance_km?`${formatNumber(data.distance_km)} km`:'—'} mono/>
              <DetailRow label="Cost/barrel"  value={data.transport_cost?`$${data.transport_cost.toFixed(2)}/bbl`:'—'} mono/>
            </div>
          </CardBody>
        </Card>
      </motion.div>
    </AnimatePresence>
  )
}
