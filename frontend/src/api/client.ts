import axios from 'axios'
import { getCurrentUser } from '../utils/auth'

export const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
})

api.interceptors.request.use((config) => {
  const currentUser = getCurrentUser()
  if (currentUser?.role === 'admin') {
    config.headers['X-Admin-User-Id'] = String(currentUser.id)
  }
  return config
})
