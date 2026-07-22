import { clsx } from 'clsx'
import { LayoutGrid, Globe, RotateCcw, Route, Download } from 'lucide-react'
import { Button } from '@/components/ui/Button.jsx'
import { Badge } from '@/components/ui/Badge.jsx'
import useUiStore from '@/store/uiStore.js'
import { NODE_TYPES, GEO_ZONES } from '@/config/constants.js'
import { exportElementAsPng } from '@/utils/exportHelpers.js'
import toast from 'react-hot-toast'

const STAGES=['upstream','midstream','downstream'], STATUSES=['operational','degraded','offline']

function FilterChip({ label, active, onClick }) {
  return <button onClick={onClick} className={clsx('px-2 py-1 text-xs rounded-md border transition-all duration-150 font-medium', active?'bg-primary-600/30 border-primary-500 text-primary-300':'bg-surface-700 border-surface-500 text-gray-400 hover:text-gray-200 hover:border-surface-400')}>{label}</button>
}

function toggle(arr, item) { return arr.includes(item)?arr.filter((x)=>x!==item):[...arr,item] }

export function NetworkControls({ className='' }) {
  const layout           = useUiStore((s) => s.networkLayout)
  const showCriticalPath = useUiStore((s) => s.showCriticalPath)
  const nodeFilters      = useUiStore((s) => s.nodeFilters)
  const setNetworkLayout = useUiStore((s) => s.setNetworkLayout)
  const toggleCritPath   = useUiStore((s) => s.toggleCriticalPath)
  const setNodeFilters   = useUiStore((s) => s.setNodeFilters)
  const resetNodeFilters = useUiStore((s) => s.resetNodeFilters)

  const activeCount = nodeFilters.stages.length+nodeFilters.types.length+nodeFilters.statuses.length+nodeFilters.zones.length

  const handleExport = async () => { try { await exportElementAsPng('supply-chain-map','atlas-network-map.png'); toast.success('Exported') } catch { toast.error('Export failed') } }

  return (
    <div className={clsx('bg-surface-800/95 backdrop-blur-sm border border-surface-500 rounded-xl p-4 space-y-4', className)}>
      <div>
        <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">Layout</p>
        <div className="flex gap-2">
          <Button size="xs" variant={layout==='hierarchical'?'primary':'secondary'} onClick={()=>setNetworkLayout('hierarchical')} icon={LayoutGrid}>Hierarchical</Button>
          <Button size="xs" variant={layout==='geographic'?'primary':'secondary'} onClick={()=>setNetworkLayout('geographic')} icon={Globe}>Geographic</Button>
        </div>
      </div>
      <Button size="xs" variant={showCriticalPath?'warning':'secondary'} onClick={toggleCritPath} icon={Route}>{showCriticalPath?'Hide Critical Path':'Show Critical Path'}</Button>
      <div>
        <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">Stage</p>
        <div className="flex flex-wrap gap-1.5">{STAGES.map((s)=><FilterChip key={s} label={s} active={nodeFilters.stages.includes(s)} onClick={()=>setNodeFilters({stages:toggle(nodeFilters.stages,s)})}/>)}</div>
      </div>
      <div>
        <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">Status</p>
        <div className="flex flex-wrap gap-1.5">{STATUSES.map((s)=><FilterChip key={s} label={s} active={nodeFilters.statuses.includes(s)} onClick={()=>setNodeFilters({statuses:toggle(nodeFilters.statuses,s)})}/>)}</div>
      </div>
      <div>
        <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">Zone</p>
        <div className="flex flex-wrap gap-1.5">{Object.keys(GEO_ZONES).map((z)=><FilterChip key={z} label={z} active={nodeFilters.zones.includes(z)} onClick={()=>setNodeFilters({zones:toggle(nodeFilters.zones,z)})}/>)}</div>
      </div>
      <div className="flex items-center gap-2 pt-1 border-t border-surface-500">
        <Button size="xs" variant="ghost" onClick={resetNodeFilters} icon={RotateCcw} disabled={activeCount===0}>Reset{activeCount>0&&<Badge variant="primary" className="ml-1">{activeCount}</Badge>}</Button>
        <Button size="xs" variant="ghost" onClick={handleExport} icon={Download}>Export PNG</Button>
      </div>
    </div>
  )
}
