import { api } from './client'

export async function getHybridRecommendations(userId: number) {
  const response = await api.get(`/recommendations/hybrid/${userId}`)
  return response.data
}

export async function getSimilarDocuments(documentId: string) {
  const response = await api.get(`/recommendations/similar/${documentId}`)
  return response.data
}