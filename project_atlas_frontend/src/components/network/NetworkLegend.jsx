import { clsx } from 'clsx'
import { NODE_TYPES, LINK_TYPES } from '@/config/constants.js'

export function NetworkLegend({ className='' }) {
  return (
    <div className={clsx('bg-surface-800/90 backdrop-blur-sm border border-surface-500 rounded-xl p-4 text-xs space-y-4', className)}>
      <div>
        <p className="text-gray-400 font-semibold uppercase tracking-wider mb-2">Node Types</p>
        <div className="space-y-1.5">
          {Object.entries(NODE_TYPES).map(([type,info])=>(
            <div key={type} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full flex-shrink-0" style={{backgroundColor:info.color}}/>
              <span className="text-gray-300">{info.label}</span>
            </div>
          ))}
        </div>
      </div>
      <div>
        <p className="text-gray-400 font-semibold uppercase tracking-wider mb-2">Status</p>
        <div className="space-y-1.5">
          {[{label:'Operational',color:'#16a34a'},{label:'Degraded',color:'#ca8a04',pulse:true},{label:'Offline',color:'#dc2626'}].map(({label,color,pulse})=>(
            <div key={label} className="flex items-center gap-2">
              <div className={clsx('w-3 h-3 rounded-full flex-shrink-0',pulse&&'animate-pulse')} style={{backgroundColor:color}}/>
              <span className="text-gray-300">{label}</span>
            </div>
          ))}
        </div>
      </div>
      <div>
        <p className="text-gray-400 font-semibold uppercase tracking-wider mb-2">Link Types</p>
        <div className="space-y-1.5">
          {Object.entries(LINK_TYPES).map(([type,info])=>(
            <div key={type} className="flex items-center gap-2">
              <svg width="24" height="8" className="flex-shrink-0">
                <line x1="0" y1="4" x2="24" y2="4" stroke={info.color} strokeWidth="2" strokeDasharray={info.strokeDasharray==='none'?undefined:info.strokeDasharray}/>
              </svg>
              <span className="text-gray-300">{info.label}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="border-t border-surface-500 pt-3">
        <div className="flex items-center gap-2">
          <svg width="24" height="8" className="flex-shrink-0"><line x1="0" y1="4" x2="24" y2="4" stroke="#f59e0b" strokeWidth="3"/></svg>
          <span className="text-amber-400">Critical Path</span>
        </div>
      </div>
    </div>
  )
}
