import { api } from '@/config/api.js'
export const simulationService = {
  run:                (scenario_id) => api.post('/simulations/run', { scenario_id }),
  getStatus:          (run_id)      => api.get(`/simulations/${run_id}`),
  getRunsForScenario: (scenario_id) => api.get(`/simulations/scenario/${scenario_id}`),
}
