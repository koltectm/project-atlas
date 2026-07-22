import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

const useUiStore = create(devtools(persist((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  networkLayout: 'hierarchical', showCriticalPath: false,
  nodeFilters: { stages: [], types: [], statuses: [], zones: [] },

  setNetworkLayout: (layout) => set({ networkLayout: layout }),
  toggleCriticalPath: () => set((s) => ({ showCriticalPath: !s.showCriticalPath })),
  setNodeFilters: (filters) => set((s) => ({ nodeFilters: { ...s.nodeFilters, ...filters } })),
  resetNodeFilters: () => set({ nodeFilters: { stages: [], types: [], statuses: [], zones: [] } }),

  compareRunId: null,
  setCompareRunId: (id) => set({ compareRunId: id }),

  selectedEntity: null,
  setSelectedEntity: (entity) => set({ selectedEntity: entity }),

  activeModal: null,
  openModal: (name) => set({ activeModal: name }),
  closeModal: () => set({ activeModal: null }),
}), {
  name: 'atlas-ui',
  partialize: (s) => ({
    sidebarCollapsed: s.sidebarCollapsed, networkLayout: s.networkLayout,
    showCriticalPath: s.showCriticalPath, nodeFilters: s.nodeFilters,
  }),
}), { name: 'atlas-ui' }))

export default useUiStore
