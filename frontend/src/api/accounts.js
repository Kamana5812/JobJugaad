import { api } from './client'
export const getAccess = async () => (await api.get('/auth/access')).data
export const requestVerification = async () => (await api.post('/auth/email-verification')).data
export const verifyEmail = async input => (await api.post('/auth/verify-email', input)).data
export const requestAccess = async input => (await api.post('/auth/access', input)).data
export const getAccountQueue = async (status, offset = 0) => (await api.get('/admin/accounts', { params: { status, offset, limit: 10 } })).data
export const reviewAccount = async (id, input) => (await api.post(`/admin/accounts/${id}/review`, input)).data
