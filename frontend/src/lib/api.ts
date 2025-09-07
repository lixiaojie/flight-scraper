import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API endpoints
export const endpoints = {
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    me: '/auth/me',
    logout: '/auth/logout',
  },
  dashboard: {
    stats: '/dashboard/stats',
    recentTasks: '/dashboard/recent-tasks',
    priceTrends: '/dashboard/price-trends',
  },
  tasks: {
    list: '/tasks',
    create: '/tasks',
    get: (id: number) => `/tasks/${id}`,
    update: (id: number) => `/tasks/${id}`,
    delete: (id: number) => `/tasks/${id}`,
    start: (id: number) => `/tasks/${id}/start`,
    stop: (id: number) => `/tasks/${id}/stop`,
    results: (id: number) => `/tasks/${id}/results`,
    export: (id: number) => `/tasks/${id}/export`,
  },
  platforms: {
    list: '/platforms/',
    create: '/platforms/',
    get: (id: number) => `/platforms/${id}/`,
    update: (id: number) => `/platforms/${id}/`,
    delete: (id: number) => `/platforms/${id}/`,
    accounts: (id: number) => `/platforms/${id}/accounts/`,
    createAccount: (id: number) => `/platforms/${id}/accounts/`,
    getAccount: (id: number) => `/platforms/accounts/${id}/`,
    updateAccount: (id: number) => `/platforms/accounts/${id}/`,
    deleteAccount: (id: number) => `/platforms/accounts/${id}/`,
  },
}

export default api
