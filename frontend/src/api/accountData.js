import { api } from './client'
export const revokeSessions = async () => (await api.post('/auth/logout')).data
export const exportAccount = async () => (await api.get('/account/export')).data
export const getDataRequests = async () => (await api.get('/account/data-requests')).data
export const requestDeletion = async payload => (await api.post('/account/data-requests', payload)).data
export const withdrawDeletion = async id => (await api.post(`/account/data-requests/${id}/withdraw`)).data
export const getDeletionQueue = async () => (await api.get('/admin/data-requests')).data
export const reviewDeletion = async (id, payload) => (await api.post(`/admin/data-requests/${id}/review`, payload)).data
