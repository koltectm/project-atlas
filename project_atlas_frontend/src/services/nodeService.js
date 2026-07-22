import { api } from '@/config/api.js'
export const nodeService = {
  getAll:      (params={}) => api.get('/nodes', { params }),
  getById:     (id)        => api.get(`/nodes/${id}`),
  getCritical: (t=0.7)     => api.get('/nodes/critical', { params: { threshold: t } }),
  getByZone:   (zone)      => api.get(`/nodes/zone/${zone}`),
  getGraphData:()          => api.get('/nodes/graph'),
  updateStatus:(id,status) => api.patch(`/nodes/${id}/status`, null, { params: { status } }),
}
