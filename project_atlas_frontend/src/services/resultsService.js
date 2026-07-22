import { api } from '@/config/api.js'
export const resultsService = {
  getAggregates:    (run_id)          => api.get(`/results/${run_id}/aggregates`),
  getIterations:    (run_id, params)  => api.get(`/results/${run_id}/iterations`, { params }),
  getVulnerability: (run_id)          => api.get(`/results/${run_id}/vulnerability`),
  getWorstCases:    (run_id, n=10)    => api.get(`/results/${run_id}/worst-cases`, { params: { n } }),
  getBestCases:     (run_id, n=10)    => api.get(`/results/${run_id}/best-cases`,  { params: { n } }),
  compareRuns:      (id1, id2)        => api.get(`/results/compare/${id1}/${id2}`),
}
