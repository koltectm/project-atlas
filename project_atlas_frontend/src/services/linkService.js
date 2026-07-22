import { api } from '@/config/api.js'
export const linkService = {
  getAll:          (params={}) => api.get('/links', { params }),
  getById:         (id)        => api.get(`/links/${id}`),
  getCriticalPath: ()          => api.get('/links/critical-path'),
  getFromNode:     (nodeId)    => api.get(`/links/from/${nodeId}`),
  getToNode:       (nodeId)    => api.get(`/links/to/${nodeId}`),
}
