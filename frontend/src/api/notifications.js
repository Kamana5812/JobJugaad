import { api } from './client'
export const getNotifications = async (offset = 0) => (await api.get('/notifications', { params: { offset, limit: 20 } })).data
export const readNotification = async id => (await api.put(`/notifications/${id}/read`)).data
