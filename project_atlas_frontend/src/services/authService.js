import { api } from '@/config/api.js'
export const authService = {
  login:   (email, password) => api.post('/auth/login', { email, password }),
  refresh: (refresh_token)   => api.post('/auth/refresh', { refresh_token }),
  getMe:   ()                => api.get('/auth/me'),
  updateMe:(data)            => api.patch('/auth/me', data),
}
