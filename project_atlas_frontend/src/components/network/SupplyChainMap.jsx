import { useCallback, useState } from 'react'
import ReactFlow, { Background, Controls, MiniMap, BackgroundVariant, useNodesState, useEdgesState } from 'reactflow'
import 'reactflow/dist/style.css'
import { nodeTypes } from './NodeCustom.jsx'
import { NodeCard }   from './NodeCard.jsx'
import { LinkDetail } from './LinkDetail.jsx'
import { Spinner }    from '@/components/ui/Spinner.jsx'
import { AlertBanner }from '@/components/ui/AlertBanner.jsx'
import { useNetwork } from '@/hooks/useNetwork.js'
import useUiStore     from '@/store/uiStore.js'

const edgeTypes = {}

export function SupplyChainMap({ className='' }) {
  const { nodes:initialNodes, edges:initialEdges, isLoading, error } = useNetwork()
  const [nodes, ,onNodesChange] = useNodesState(initialNodes)
  const [edges, ,onEdgesChange] = useEdgesState(initialEdges)
  const layout             = useUiStore((s) => s.networkLayout)
  const setSelectedEntity  = useUiStore((s) => s.setSelectedEntity)
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)

  const onNodeClick = useCallback((_, node) => { setSelectedNode(node); setSelectedEdge(null); setSelectedEntity({type:'node',data:node.data}) }, [setSelectedEntity])
  const onEdgeClick = useCallback((_, edge) => { setSelectedEdge(edge); setSelectedNode(null); setSelectedEntity({type:'edge',data:edge.data}) }, [setSelectedEntity])
  const onPaneClick = useCallback(() => { setSelectedNode(null); setSelectedEdge(null); setSelectedEntity(null) }, [setSelectedEntity])

  if (isLoading) return <div className="flex items-center justify-center h-full"><div className="flex flex-col items-center gap-3"><Spinner size="lg"/><p className="text-sm text-gray-400">Loading supply chain network…</p></div></div>
  if (error) return <div className="p-6"><AlertBanner variant="error" title="Failed to load network graph">{error.message}</AlertBanner></div>

  return (
    <div id="supply-chain-map" className={`relative w-full h-full ${className}`}>
      <ReactFlow key={layout} nodes={initialNodes} edges={initialEdges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick} onEdgeClick={onEdgeClick} onPaneClick={onPaneClick}
        nodeTypes={nodeTypes} edgeTypes={edgeTypes} fitView fitViewOptions={{padding:0.15}} minZoom={0.2} maxZoom={2.5}
        proOptions={{hideAttribution:true}} className="bg-surface-900">
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#1e2d45"/>
        <Controls showInteractive={false} className="!bottom-4 !left-4"/>
        <MiniMap nodeColor={(node)=>node.data?.typeColor||'#3b82f6'} maskColor="rgba(10,15,30,0.7)" className="!bottom-4 !right-4" style={{background:'#0f1629'}}/>
      </ReactFlow>
      {selectedNode && <NodeCard node={selectedNode} onClose={()=>setSelectedNode(null)}/>}
      {selectedEdge && !selectedNode && <LinkDetail edge={selectedEdge} onClose={()=>setSelectedEdge(null)}/>}
    </div>
  )
}
