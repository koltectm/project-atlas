import useAuthStore from '@/store/authStore.js'
export function useAuth() {
  const user            = useAuthStore((s) => s.user)
  const profile         = useAuthStore((s) => s.profile)
  const isLoading       = useAuthStore((s) => s.isLoading)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const login           = useAuthStore((s) => s.login)
  const register        = useAuthStore((s) => s.register)
  const logout          = useAuthStore((s) => s.logout)
  const updateProfile   = useAuthStore((s) => s.updateProfile)
  const isAdmin         = useAuthStore((s) => s.isAdmin)
  const isAnalyst       = useAuthStore((s) => s.isAnalyst)
  const canRunSims      = useAuthStore((s) => s.canRunSimulations)
  return {
    user, profile, isLoading, isAuthenticated,
    login, register, logout, updateProfile,
    isAdmin: isAdmin(), isAnalyst: isAnalyst(), canRunSimulations: canRunSims(),
    role: profile?.role || 'viewer',
  }
}
