import { api } from './client'

export async function getSystemStats() {
  const response = await api.get('/analytics/system-stats')
  return response.data
}