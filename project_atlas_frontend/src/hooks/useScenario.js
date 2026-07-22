import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { scenarioService, disruptionService } from '@/services/scenarioService.js'

export function useScenarios(type='mine') {
  const { data, isLoading, error } = useQuery({
    queryKey: ['scenarios', type],
    queryFn:  () => (type==='public' ? scenarioService.getPublic : scenarioService.getMine)({ limit:100 }).then((r)=>r.data),
  })
  return { scenarios: data?.items||[], total: data?.total||0, isLoading, error }
}

export function useScenario(scenarioId) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['scenario', scenarioId],
    queryFn:  () => scenarioService.getById(scenarioId).then((r)=>r.data),
    enabled:  !!scenarioId,
  })
  return { scenario:data, isLoading, error }
}

export function useScenarioMutations() {
  const qc = useQueryClient()
  const invalidate = () => qc.invalidateQueries({ queryKey:['scenarios'] })

  const createScenario = useMutation({
    mutationFn: (data) => scenarioService.create(data).then((r)=>r.data),
    onSuccess: (s) => { toast.success('Scenario created'); invalidate(); qc.setQueryData(['scenario',s.scenario_id],s) },
    onError: (err) => toast.error(err.response?.data?.message||'Failed to create scenario'),
  })

  const updateScenario = useMutation({
    mutationFn: ({ id, data }) => scenarioService.update(id, data).then((r)=>r.data),
    onSuccess: (s) => { toast.success('Scenario updated'); invalidate(); qc.setQueryData(['scenario',s.scenario_id],s) },
    onError: (err) => toast.error(err.response?.data?.message||'Failed to update scenario'),
  })

  const deleteScenario = useMutation({
    mutationFn: (id) => scenarioService.delete(id),
    onSuccess: () => { toast.success('Scenario deleted'); invalidate() },
    onError: (err) => toast.error(err.response?.data?.message||'Failed to delete scenario'),
  })

  return { createScenario, updateScenario, deleteScenario }
}

export function useDisruptionTypes(category) {
  const { data, isLoading } = useQuery({
    queryKey: ['disruption-types', category||'all'],
    queryFn:  () => disruptionService.getAll(category?{ category }:{}).then((r)=>r.data),
    staleTime: 10*60_000,
  })
  return { disruptionTypes: data||[], isLoading }
}
