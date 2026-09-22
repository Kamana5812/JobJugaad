import { api } from './client'

export function setAccessToken(token) {
  if (token) api.defaults.headers.common.Authorization = `Bearer ${token}`
  else delete api.defaults.headers.common.Authorization
}
export const signUp = async (input) => (await api.post('/auth/signup', input)).data
export const logIn = async (input) => (await api.post('/auth/login', input)).data
export const getMe = async () => (await api.get('/auth/me')).data
export const getProfile = async (id) => (await api.get(`/students/${id}`)).data
export const saveProfile = async (id, input) => (await api.put(`/students/${id}`, input)).data
export async function uploadResume(id, file) {
  const body = new FormData()
  body.append('file', file)
  return (await api.post(`/students/${id}/resume`, body)).data
}
export function errorMessage(error) {
  const detail = error.response?.data?.detail
  return typeof detail === 'string' ? detail : 'Could not reach JobJugaad. Please retry; the demo server may be waking up.'
}
