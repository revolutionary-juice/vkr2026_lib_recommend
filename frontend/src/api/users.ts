import { api } from './client'

export async function getUsers() {
  const response = await api.get('/users/')
  return response.data
}

export async function getUserProfile(userId: number) {
  const response = await api.get(`/users/${userId}`)
  return response.data
}

export async function getUserHistory(userId: number) {
  const response = await api.get(`/users/${userId}/history`)
  return response.data
}

export async function getUserFavorites(userId: number) {
  const response = await api.get(`/users/${userId}/favorites`)
  return response.data
}

export async function getUserRatings(userId: number) {
  const response = await api.get(`/ratings/user/${userId}`)
  return response.data
}

export async function getUserSearchHistory(userId: number) {
  const response = await api.get(`/search-history/user/${userId}`)
  return response.data
}