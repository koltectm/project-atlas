import { memo } from 'react'
import { Handle, Position } from 'reactflow'
import { clsx } from 'clsx'
import { Droplets, Pipette, Anchor, Factory, Database, Ship, Network, Building2 } from 'lucide-react'

const TYPE_ICONS = {
  wellhead:Droplets, pipeline:Pipette, export_terminal:Anchor, refinery:Factory,
  storage_depot:Database, port:Ship, distribution_hub:Network, consumer:Building2,
}
const TYPE_SHAPES = {
  wellhead:'rounded-full', pipeline:'rotate-45', export_terminal:'rounded-2xl',
  refinery:'rounded-lg', storage_depot:'rounded-lg', port:'rounded-2xl',
  distribution_hub:'rounded-xl', consumer:'rounded-full',
}
const STATUS_GLOW = { operational:'node-glow-operational', degraded:'node-glow-degraded', offline:'node-glow-offline opacity-60' }

function AtlasNode({ data, selected }) {
  const Icon  = TYPE_ICONS[data.node_type] || Building2
  const glow  = STATUS_GLOW[data.status]   || ''
  const shape = TYPE_SHAPES[data.node_type]|| 'rounded-lg'
  const size  = data.size || 45
  const isPipeline = data.node_type === 'pipeline'

  return (
    <div className="flex flex-col items-center gap-1 select-none">
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-surface-400 !border-surface-300" />
      <div
        className={clsx('flex items-center justify-center cursor-pointer border-2 transition-all duration-200', isPipeline?'rotate-45':'', shape, glow, selected?'border-white scale-110':'border-transparent hover:scale-105')}
        style={{ width:size, height:size, backgroundColor:`${data.typeColor}22`, borderColor:selected?'#fff':`${data.typeColor}88` }}
      >
        <div className={isPipeline?'-rotate-45':''}>
          <Icon style={{ color:data.typeColor, width:size*0.38, height:size*0.38 }} />
        </div>
      </div>
      <div className="text-center max-w-24 px-1" style={{ fontSize:Math.max(9,size*0.18) }}>
        <p className="font-medium text-gray-200 leading-tight line-clamp-2 text-center">{data.node_code||data.label}</p>
      </div>
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-surface-400 !border-surface-300" />
    </div>
  )
}

export const nodeTypes = { atlasNode: memo(AtlasNode) }
