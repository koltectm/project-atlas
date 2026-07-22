import axios from 'axios'
import toast from 'react-hot-toast'
import { API_BASE_URL } from './constants.js'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
})

api.interceptors.request.use(
  (config) => {
    const token = getStoredToken()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (!error.response) {
      toast.error('Network error — check your connection')
      return Promise.reject(error)
    }

    if (error.response.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        }).catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = getStoredRefreshToken()
        if (!refreshToken) throw new Error('No refresh token')

        const { data } = await axios.post(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        )

        const newToken = data.access_token
        setStoredToken(newToken)
        setStoredRefreshToken(data.refresh_token)
        processQueue(null, newToken)

        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        window.dispatchEvent(new CustomEvent('atlas:force-logout'))
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    if (error.response.status === 429) {
      toast.error('Too many requests — please slow down')
    }

    if (error.response.status >= 500) {
      const msg = error.response.data?.message || 'Server error — try again shortly'
      toast.error(msg)
    }

    return Promise.reject(error)
  }
)

const TOKEN_KEY         = 'atlas_access_token'
const REFRESH_TOKEN_KEY = 'atlas_refresh_token'

export function getStoredToken()         { return localStorage.getItem(TOKEN_KEY) }
export function getStoredRefreshToken()  { return localStorage.getItem(REFRESH_TOKEN_KEY) }
export function setStoredToken(t)        { localStorage.setItem(TOKEN_KEY, t) }
export function setStoredRefreshToken(t) { localStorage.setItem(REFRESH_TOKEN_KEY, t) }
export function clearStoredTokens()      {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}
