import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

const DEFAULT = {
  scenario_name: '', description: '', time_horizon_days: 90,
  simulation_iterations: 10_000, is_public: false, tags: [], disruptions: [],
}

const useScenarioStore = create(devtools((set, get) => ({
  draft: { ...DEFAULT }, currentStep: 0, isDirty: false, disruptionTypes: [],

  setDraft: (updates) => set((s) => ({ draft: { ...s.draft, ...updates }, isDirty: true })),

  addDisruption: (d) => set((s) => ({
    draft: { ...s.draft, disruptions: [...s.draft.disruptions, {
      disruption_type_id: d.disruption_type_id, probability_override: null,
      severity_override: null, duration_days_override: null,
      target_node_id: null, target_link_id: null, is_active: true,
      _name: d.name, _category: d.category, _default_probability: d.typical_annual_probability,
    }]}, isDirty: true,
  })),

  updateDisruption: (index, updates) => set((s) => {
    const disruptions = [...s.draft.disruptions]
    disruptions[index] = { ...disruptions[index], ...updates }
    return { draft: { ...s.draft, disruptions }, isDirty: true }
  }),

  removeDisruption: (index) => set((s) => ({
    draft: { ...s.draft, disruptions: s.draft.disruptions.filter((_, i) => i !== index) },
    isDirty: true,
  })),

  setStep: (step) => set({ currentStep: step }),
  nextStep: () => set((s) => ({ currentStep: Math.min(s.currentStep + 1, 2) })),
  prevStep: () => set((s) => ({ currentStep: Math.max(s.currentStep - 1, 0) })),
  resetDraft: () => set({ draft: { ...DEFAULT }, currentStep: 0, isDirty: false }),

  loadScenarioForEdit: (scenario) => set({
    draft: {
      scenario_name: scenario.scenario_name, description: scenario.description || '',
      time_horizon_days: scenario.time_horizon_days, simulation_iterations: scenario.simulation_iterations,
      is_public: scenario.is_public, tags: scenario.tags || [],
      disruptions: (scenario.disruptions || []).map((sd) => ({
        disruption_type_id: sd.disruption_type_id, probability_override: sd.probability_override,
        severity_override: sd.severity_override, duration_days_override: sd.duration_days_override,
        target_node_id: sd.target_node_id, target_link_id: sd.target_link_id,
        is_active: sd.is_active, _name: sd._name, _category: sd._category,
        _default_probability: sd._default_probability,
      })),
    },
    currentStep: 0, isDirty: false,
  }),

  setDisruptionTypes: (types) => set({ disruptionTypes: types }),
}), { name: 'atlas-scenario' }))

export default useScenarioStore
