import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: `${API_URL}/api` })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('devguard_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('devguard_token')
      localStorage.removeItem('devguard_user')
      if (!location.pathname.includes('/login')) location.href = '/login'
    }
    return Promise.reject(error)
  }
)
