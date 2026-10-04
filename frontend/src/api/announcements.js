import { api } from './client'
import { errorMessage } from './student'

export const getAnnouncementOptions = async () => (await api.get('/admin/announcements/options')).data
export const previewAnnouncement = async input => (await api.post('/admin/announcements/preview', input)).data
export const publishAnnouncement = async input => (await api.post('/admin/announcements', input)).data
export const getAnnouncements = async (offset = 0) => (await api.get('/admin/announcements', { params: { offset, limit: 10 } })).data
export const getAnnouncementRecipients = async (id, offset = 0) => (await api.get(`/admin/announcements/${id}/recipients`, { params: { offset, limit: 10 } })).data

export function announcementErrorMessage(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail.map(item => item?.msg).filter(message => typeof message === 'string')
    if (messages.length) return messages.join(' ').replaceAll('Value error, ', '')
  }
  return errorMessage(error)
}
