import { NODE_TYPES, LINK_TYPES } from '@/config/constants.js'

const GEO_BOUNDS = { minLat:4.0, maxLat:14.5, minLon:2.0, maxLon:15.0 }
const CANVAS     = { width:1400, height:900, paddingX:100, paddingY:80 }

function geoToCanvas(lat, lon) {
  const x=((lon-GEO_BOUNDS.minLon)/(GEO_BOUNDS.maxLon-GEO_BOUNDS.minLon))*(CANVAS.width-2*CANVAS.paddingX)+CANVAS.paddingX
  const y=((GEO_BOUNDS.maxLat-lat)/(GEO_BOUNDS.maxLat-GEO_BOUNDS.minLat))*(CANVAS.height-2*CANVAS.paddingY)+CANVAS.paddingY
  return { x, y }
}

const STAGE_COLS = { upstream:0.10, midstream:0.45, downstream:0.85 }

function hierarchicalLayout(nodes) {
  const byStage = { upstream:[], midstream:[], downstream:[] }
  nodes.forEach((n)=>{ const s=n.data?.stage||'midstream'; (byStage[s]||byStage.midstream).push(n) })
  const positions={}
  Object.entries(byStage).forEach(([stage,stageNodes])=>{
    const x=(STAGE_COLS[stage]||0.5)*CANVAS.width
    const spacing=CANVAS.height/(stageNodes.length+1)
    stageNodes.forEach((n,i)=>{ positions[n.id]={ x, y:spacing*(i+1) } })
  })
  return positions
}

function nodeSize(c) { return c>0.8?60:c>0.5?45:30 }
function statusGlow(s) {
  if (s==='operational') return 'node-glow-operational'
  if (s==='degraded')    return 'node-glow-degraded'
  return 'node-glow-offline'
}

export function transformGraphData(graphData, layout='hierarchical', filters={}, showCriticalPath=false) {
  if (!graphData?.nodes) return { nodes:[], edges:[] }
  const { nodes:rawNodes, edges:rawEdges } = graphData
  const { stages=[], types=[], statuses=[], zones=[] } = filters

  const filteredNodes = rawNodes.filter((n)=>{
    if (stages.length   && !stages.includes(n.stage))           return false
    if (types.length    && !types.includes(n.node_type))        return false
    if (statuses.length && !statuses.includes(n.status))        return false
    if (zones.length    && !zones.includes(n.geopolitical_zone))return false
    return true
  })

  const visibleIds = new Set(filteredNodes.map((n)=>String(n.node_id||n.id)))

  const rfNodes = filteredNodes.map((n)=>{
    const id=String(n.node_id||n.id)
    const criticality=n.criticality_score??n.criticality??0
    const typeInfo=NODE_TYPES[n.node_type]||{}
    return {
      id, type:'atlasNode',
      data: {
        label:n.node_name||n.node_code||id, node_code:n.node_code, node_type:n.node_type,
        stage:n.stage, status:n.status||'operational', criticality,
        redundancy:n.redundancy_score??n.redundancy??0, capacity_bpd:n.capacity_bpd,
        utilization:n.current_utilization_pct??n.utilization??0,
        geopolitical_zone:n.geopolitical_zone, operator:n.operator,
        latitude:n.latitude, longitude:n.longitude,
        typeColor:typeInfo.color||'#6b7280', size:nodeSize(criticality), glowClass:statusGlow(n.status),
      },
      position: layout==='geographic'&&n.latitude&&n.longitude
        ? geoToCanvas(n.latitude,n.longitude)
        : { x:0, y:0 },
    }
  })

  if (layout==='hierarchical') {
    const positions=hierarchicalLayout(rfNodes)
    rfNodes.forEach((n)=>{ n.position=positions[n.id]||{ x:400, y:400 } })
  }

  const rfEdges=(rawEdges||[]).filter((e)=>{
    const src=String(e.source||e.source_node_id), tgt=String(e.target||e.target_node_id)
    return visibleIds.has(src)&&visibleIds.has(tgt)
  }).map((e)=>{
    const id=String(e.link_id||e.id||`${e.source}-${e.target}`)
    const src=String(e.source||e.source_node_id), tgt=String(e.target||e.target_node_id)
    const isCrit=e.is_critical_path&&showCriticalPath
    const typeInfo=LINK_TYPES[e.link_type]||{}
    const color=isCrit?'#f59e0b':(typeInfo.color||'#3b82f6')
    return {
      id, source:src, target:tgt, type:'default', animated:isCrit,
      data:{ link_id:id, link_type:e.link_type, link_code:e.link_code,
        reliability_score:e.reliability_score, vandalism_risk:e.vandalism_risk_score,
        max_capacity_bpd:e.max_capacity_bpd, transport_cost:e.cost_per_barrel,
        distance_km:e.distance_km, is_critical_path:e.is_critical_path,
        status:e.status||'operational', edgeColor:color, strokeWidth:isCrit?3:2 },
      style:{ stroke:color, strokeWidth:isCrit?3:2 },
      markerEnd:{ type:'arrowclosed', color },
    }
  })

  return { nodes:rfNodes, edges:rfEdges }
}
