import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { supabase } from '@/config/supabase.js'
import { api, setStoredToken, setStoredRefreshToken, clearStoredTokens } from '@/config/api.js'
import toast from 'react-hot-toast'

const useAuthStore = create(devtools((set, get) => ({
  user: null, profile: null, session: null,
  isLoading: true, isAuthenticated: false,

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      const { data } = await api.post('/auth/login', { email, password })
      setStoredToken(data.access_token)
      setStoredRefreshToken(data.refresh_token)
      const profileRes = await api.get('/auth/me')
      const { data: sbData } = await supabase.auth.signInWithPassword({ email, password })
      set({ user: sbData?.user || { email }, profile: profileRes.data, session: sbData?.session || null, isAuthenticated: true, isLoading: false })
      return { success: true }
    } catch (err) {
      set({ isLoading: false })
      return { success: false, error: err.response?.data?.message || 'Login failed' }
    }
  },

  register: async ({ email, password, full_name, organization }) => {
    set({ isLoading: true })
    try {
      const { error: sbError } = await supabase.auth.signUp({ email, password, options: { data: { full_name, organization } } })
      if (sbError) throw sbError
      return await get().login(email, password)
    } catch (err) {
      set({ isLoading: false })
      return { success: false, error: err.message || 'Registration failed' }
    }
  },

  logout: async () => {
    clearStoredTokens()
    await supabase.auth.signOut().catch(() => {})
    set({ user: null, profile: null, session: null, isAuthenticated: false, isLoading: false })
  },

  initializeAuth: async () => {
    set({ isLoading: true })
    try {
      const { data: profile } = await api.get('/auth/me')
      const { data: { session } } = await supabase.auth.getSession()
      set({ profile, user: session?.user || { email: profile.email }, session, isAuthenticated: true, isLoading: false })
    } catch {
      clearStoredTokens()
      set({ user: null, profile: null, session: null, isAuthenticated: false, isLoading: false })
    }
  },

  updateProfile: async (updates) => {
    try {
      const { data: profile } = await api.patch('/auth/me', updates)
      set({ profile })
      toast.success('Profile updated')
      return { success: true }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Update failed')
      return { success: false }
    }
  },

  isAdmin:           () => get().profile?.role === 'admin',
  isAnalyst:         () => ['admin', 'analyst'].includes(get().profile?.role),
  canRunSimulations: () => ['admin', 'analyst'].includes(get().profile?.role),
}), { name: 'atlas-auth' }))

if (typeof window !== 'undefined') {
  window.addEventListener('atlas:force-logout', () => {
    useAuthStore.getState().logout()
    toast.error('Session expired — please log in again')
  })
}

export default useAuthStore
