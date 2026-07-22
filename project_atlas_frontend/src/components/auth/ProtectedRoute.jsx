import { Navigate, useLocation } from 'react-router-dom'
import toast from 'react-hot-toast'
import useAuthStore from '@/store/authStore.js'
import { PageSpinner } from '@/components/ui/Spinner.jsx'

export function ProtectedRoute({ children, requiredRole }) {
  const isLoading       = useAuthStore((s) => s.isLoading)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const isAdmin         = useAuthStore((s) => s.isAdmin)
  const isAnalyst       = useAuthStore((s) => s.isAnalyst)
  const location        = useLocation()

  if (isLoading) return <PageSpinner message="Verifying session…" />
  if (!isAuthenticated) return <Navigate to="/auth" state={{ from: location }} replace />

  if (requiredRole) {
    const ok = requiredRole==='viewer'?true:requiredRole==='analyst'?isAnalyst():requiredRole==='admin'?isAdmin():false
    if (!ok) { toast.error(`This page requires ${requiredRole} access.`); return <Navigate to="/dashboard" replace /> }
  }
  return children
}
