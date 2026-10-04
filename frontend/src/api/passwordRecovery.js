import { api } from './client'

export const requestPasswordReset = async payload => (await api.post('/auth/password-reset-request', payload)).data
export const resetPassword = async payload => (await api.post('/auth/reset-password', payload)).data
