import { api } from '@/config/api.js'
export const analyticsService = {
  getNetworkGraph:       ()             => api.get('/analytics/network/graph'),
  validateNetwork:       ()             => api.get('/analytics/network/validate'),
  getCriticalPath:       ()             => api.get('/analytics/network/critical-path'),
  getVulnerabilityReport:(run_id,w={})  => api.get(`/analytics/run/${run_id}/vulnerability-report`, { params: w }),
  optimiseMitigations:   (params)       => api.post('/analytics/optimise/mitigations', null, { params }),
}
