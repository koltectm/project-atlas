import { useQuery } from '@tanstack/react-query'
import { resultsService } from '@/services/resultsService.js'
import { keyedAggregates } from '@/utils/chartHelpers.js'

export function useResults(runId) {
  const enabled = !!runId
  const aggregatesQuery    = useQuery({ queryKey:['results-aggregates',runId],    queryFn:()=>resultsService.getAggregates(runId).then((r)=>r.data),    enabled, staleTime:Infinity })
  const vulnerabilityQuery = useQuery({ queryKey:['results-vulnerability',runId], queryFn:()=>resultsService.getVulnerability(runId).then((r)=>r.data), enabled, staleTime:Infinity })
  const worstCasesQuery    = useQuery({ queryKey:['results-worst',runId],         queryFn:()=>resultsService.getWorstCases(runId,20).then((r)=>r.data),  enabled, staleTime:Infinity })
  const bestCasesQuery     = useQuery({ queryKey:['results-best',runId],          queryFn:()=>resultsService.getBestCases(runId,20).then((r)=>r.data),   enabled, staleTime:Infinity })

  const aggregates = aggregatesQuery.data||[]
  return {
    aggregates, keyed: keyedAggregates(aggregates),
    vulnerability: vulnerabilityQuery.data||[], worstCases: worstCasesQuery.data||[], bestCases: bestCasesQuery.data||[],
    isLoading: aggregatesQuery.isLoading||vulnerabilityQuery.isLoading, error: aggregatesQuery.error,
  }
}

export function useRunComparison(runId1, runId2) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['run-comparison', runId1, runId2],
    queryFn:  () => resultsService.compareRuns(runId1, runId2).then((r)=>r.data),
    enabled:  !!(runId1&&runId2), staleTime: Infinity,
  })
  return { comparison:data, isLoading, error }
}
