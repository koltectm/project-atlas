/**
 * src/pages/NetworkPage.jsx
 * ============================
 * Supply chain map page. Wraps SupplyChainMap in ReactFlowProvider
 * (required for useReactFlow hook usage in child components).
 */
import { ReactFlowProvider } from 'reactflow'
import { SupplyChainMap }   from '@/components/network/SupplyChainMap.jsx'
import { NetworkControls }  from '@/components/network/NetworkControls.jsx'
import { NetworkLegend }    from '@/components/network/NetworkLegend.jsx'

export function NetworkPage() {
  return (
    <div className="-m-6 h-[calc(100vh-4rem)] relative">
      <ReactFlowProvider>
        <SupplyChainMap />

        {/* Floating controls — top-left */}
        <div className="absolute top-4 left-4 z-10 w-64 max-h-[calc(100%-2rem)] overflow-y-auto">
          <NetworkControls />
        </div>

        {/* Floating legend — bottom-left, above minimap controls */}
        <div className="absolute bottom-20 left-4 z-10 w-56">
          <NetworkLegend />
        </div>
      </ReactFlowProvider>
    </div>
  )
}
