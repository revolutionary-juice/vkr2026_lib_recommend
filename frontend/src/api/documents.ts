import { api } from './client'
import type { Document, PopularDocument } from '../types/document'

export async function getRecentDocuments(): Promise<Document[]> {
  const response = await api.get('/documents/recent')
  return response.data
}

export async function getPopularDocuments(): Promise<PopularDocument[]> {
  const response = await api.get('/documents/popular')
  return response.data
}

export async function getDocuments(search?: string, category?: string): Promise<Document[]> {
  const response = await api.get('/documents/', {
    params: { search, category },
  })
  return response.data
}

export async function getDocumentById(id: string): Promise<Document> {
  const response = await api.get(`/documents/${id}`)
  return response.data
}

export async function addView(userId: number, documentId: number) {
  const response = await api.post('/actions/view', null, {
    params: {
      user_id: userId,
      document_id: documentId,
    },
  })
  return response.data
}

export async function addFavorite(userId: number, documentId: number) {
  const response = await api.post('/actions/favorite', null, {
    params: {
      user_id: userId,
      document_id: documentId,
    },
  })
  return response.data
}

export async function removeFavorite(userId: number, documentId: number) {
  const response = await api.delete('/actions/favorite', {
    params: {
      user_id: userId,
      document_id: documentId,
    },
  })
  return response.data
}

export async function addRating(userId: number, documentId: number, score: number) {
  const response = await api.post('/actions/rate', null, {
    params: {
      user_id: userId,
      document_id: documentId,
      score,
    },
  })
  return response.data
}