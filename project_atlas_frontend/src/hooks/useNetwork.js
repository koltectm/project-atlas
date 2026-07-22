import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import { analyticsService } from '@/services/analyticsService.js'
import { transformGraphData } from '@/utils/networkHelpers.js'
import useUiStore from '@/store/uiStore.js'

export function useNetwork() {
  const layout           = useUiStore((s) => s.networkLayout)
  const nodeFilters      = useUiStore((s) => s.nodeFilters)
  const showCriticalPath = useUiStore((s) => s.showCriticalPath)

  const { data:graphData, isLoading, error, refetch } = useQuery({
    queryKey: ['network-graph'],
    queryFn:  () => analyticsService.getNetworkGraph().then((r) => r.data),
    staleTime: 5*60_000,
  })

  const { nodes, edges } = useMemo(() => {
    if (!graphData) return { nodes:[], edges:[] }
    return transformGraphData(graphData, layout, nodeFilters, showCriticalPath)
  }, [graphData, layout, nodeFilters, showCriticalPath])

  return { nodes, edges, graphData, isLoading, error, refetch }
}
