import { api } from './client'

export async function getAdminOverview() {
  const response = await api.get('/admin/overview')
  return response.data
}

export async function getAdminCatalogOptions() {
  const response = await api.get('/admin/catalog/options')
  return response.data
}

export async function getAdminDocuments(params?: Record<string, string | number>) {
  const response = await api.get('/admin/documents', { params })
  return response.data
}

export async function getAdminDocument(documentId: number) {
  const response = await api.get(`/admin/documents/${documentId}`)
  return response.data
}

export async function createAdminDocument(payload: Record<string, unknown>) {
  const response = await api.post('/admin/documents', payload)
  return response.data
}

export async function updateAdminDocument(documentId: number, payload: Record<string, unknown>) {
  const response = await api.put(`/admin/documents/${documentId}`, payload)
  return response.data
}

export async function deleteAdminDocument(documentId: number) {
  const response = await api.delete(`/admin/documents/${documentId}`)
  return response.data
}

export async function importAdminDocuments() {
  const response = await api.post('/admin/documents/import-csv')
  return response.data
}

export async function importDvfuDocuments(payload: { query: string; pages?: number; max_records?: number }) {
  const response = await api.post('/admin/documents/import-dvfu', payload)
  return response.data
}

export async function autocategorizeAdminDocuments() {
  const response = await api.post('/admin/documents/autocategorize')
  return response.data
}

export async function mergeAdminDocuments(sourceDocumentId: number, targetDocumentId: number) {
  const response = await api.post('/admin/documents/merge', {
    source_document_id: sourceDocumentId,
    target_document_id: targetDocumentId,
  })
  return response.data
}

export async function getAdminUsers() {
  const response = await api.get('/admin/users')
  return response.data
}

export async function getAdminUser(userId: number) {
  const response = await api.get(`/admin/users/${userId}`)
  return response.data
}

export async function updateAdminUser(userId: number, payload: Record<string, unknown>) {
  const response = await api.patch(`/admin/users/${userId}`, payload)
  return response.data
}

export async function deleteAdminUser(userId: number) {
  const response = await api.delete(`/admin/users/${userId}`)
  return response.data
}

export async function getAdminInteractions(params?: Record<string, string | number>) {
  const response = await api.get('/admin/interactions', { params })
  return response.data
}

export async function deleteAdminInteraction(interactionId: number) {
  const response = await api.delete(`/admin/interactions/${interactionId}`)
  return response.data
}

export async function getAdminRatings(params?: Record<string, string | number>) {
  const response = await api.get('/admin/ratings', { params })
  return response.data
}

export async function deleteAdminRating(ratingId: number) {
  const response = await api.delete(`/admin/ratings/${ratingId}`)
  return response.data
}

export async function getAdminSearchHistory(params?: Record<string, string | number>) {
  const response = await api.get('/admin/search-history', { params })
  return response.data
}

export async function deleteAdminSearchRecord(searchId: number) {
  const response = await api.delete(`/admin/search-history/${searchId}`)
  return response.data
}

export async function cleanupAdminDuplicates() {
  const response = await api.post('/admin/cleanup-duplicates')
  return response.data
}

export async function getAdminRecommendationDiagnostics(userId: number) {
  const response = await api.get(`/admin/recommendations/${userId}`)
  return response.data
}

export async function getAdminLogs() {
  const response = await api.get('/admin/logs')
  return response.data
}

export async function downloadAdminExport(entity: 'documents' | 'users' | 'history') {
  const response = await api.get(`/admin/export/${entity}`, { responseType: 'blob' })
  return response.data as Blob
}

export async function downloadAdminBackup() {
  const response = await api.get('/admin/backup', { responseType: 'blob' })
  return response.data as Blob
}
