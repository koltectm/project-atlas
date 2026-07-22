import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from '@/store/authStore.js'
import { AppShell }          from '@/components/layout/AppShell.jsx'
import { ProtectedRoute }    from '@/components/auth/ProtectedRoute.jsx'
import { LandingPage }       from '@/pages/LandingPage.jsx'
import { AuthPage }           from '@/pages/AuthPage.jsx'
import { DashboardPage }      from '@/pages/DashboardPage.jsx'
import { NetworkPage }        from '@/pages/NetworkPage.jsx'
import { ScenariosPage }      from '@/pages/ScenariosPage.jsx'
import { ScenarioDetailPage } from '@/pages/ScenarioDetailPage.jsx'
import { SimulationPage }     from '@/pages/SimulationPage.jsx'
import { ResultsPage }        from '@/pages/ResultsPage.jsx'
import { AnalyticsPage }      from '@/pages/AnalyticsPage.jsx'
import { ComparePage }        from '@/pages/ComparePage.jsx'
import { NotFoundPage }       from '@/pages/NotFoundPage.jsx'

export default function App() {
  const initializeAuth = useAuthStore((s) => s.initializeAuth)
  useEffect(() => { initializeAuth() }, [initializeAuth])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"     element={<LandingPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
          <Route path="/dashboard"               element={<DashboardPage />} />
          <Route path="/network"                 element={<NetworkPage />} />
          <Route path="/scenarios"               element={<ScenariosPage />} />
          <Route path="/scenarios/new"           element={<ScenarioDetailPage mode="create" />} />
          <Route path="/scenarios/:id"           element={<ScenarioDetailPage mode="view" />} />
          <Route path="/scenarios/:id/edit"      element={<ScenarioDetailPage mode="edit" />} />
          <Route path="/simulation"              element={<SimulationPage />} />
          <Route path="/simulation/:runId"       element={<SimulationPage />} />
          <Route path="/results/:runId"          element={<ResultsPage />} />
          <Route path="/analytics"               element={<AnalyticsPage />} />
          <Route path="/compare"                 element={<ComparePage />} />
          <Route path="/compare/:runId1/:runId2" element={<ComparePage />} />
        </Route>
        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*"    element={<Navigate to="/404" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
