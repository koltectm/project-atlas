import { api } from '@/config/api.js'
export const scenarioService = {
  getPublic:     (params={}) => api.get('/scenarios/public', { params }),
  getMine:       (params={}) => api.get('/scenarios/mine',   { params }),
  getById:       (id)        => api.get(`/scenarios/${id}`),
  create:        (data)      => api.post('/scenarios', data),
  update:        (id, data)  => api.patch(`/scenarios/${id}`, data),
  delete:        (id)        => api.delete(`/scenarios/${id}`),
  addDisruption: (id, data)  => api.post(`/scenarios/${id}/disruptions`, data),
}
export const disruptionService = {
  getAll:  (params={}) => api.get('/disruptions', { params }),
  getById: (id)        => api.get(`/disruptions/${id}`),
}
