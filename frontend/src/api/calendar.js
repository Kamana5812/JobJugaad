import { api } from './client'
import { errorMessage } from './student'

export function calendarErrorMessage(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail.map(item => item.msg).filter(message => typeof message === 'string')
    if (messages.length) return messages.join(' ').replaceAll('Value error, ', '')
  }
  return errorMessage(error)
}

export const getCalendarSettings = async () => (await api.get('/admin/calendar/settings')).data
export const saveCalendarSettings = async input => (await api.put('/admin/calendar/settings', input)).data
export const getCalendarConstraints = async (offset = 0) => (await api.get('/admin/calendar/constraints', { params: { offset, limit: 20 } })).data
export const createCalendarConstraint = async input => (await api.post('/admin/calendar/constraints', input)).data
export const cancelCalendarConstraint = async (id, input) => (await api.put(`/admin/calendar/constraints/${id}/cancel`, input)).data
export const getStudentAvailability = async (studentId, offset = 0) => (await api.get(`/students/${studentId}/availability`, { params: { offset, limit: 10 } })).data
export const createStudentAvailability = async (studentId, input) => (await api.post(`/students/${studentId}/availability`, input)).data
export const cancelStudentAvailability = async (studentId, id, input) => (await api.put(`/students/${studentId}/availability/${id}/cancel`, input)).data
