import { api } from './client'

export async function registerUser(username: string, email: string, password: string) {
  const response = await api.post('/users/', {
    username,
    email,
    password,
  })
  return response.data
}

export async function loginUser(identifier: string, password: string) {
  const response = await api.post('/auth/login', {
    identifier,
    password,
  })
  return response.data
}
