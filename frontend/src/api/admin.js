import { api } from './client'
export const getAnalytics = async () => (await api.get('/admin/analytics/overview')).data
export const getCalendar = async () => (await api.get('/admin/schedules')).data
export const checkSlot = async input => (await api.post('/admin/schedules/check-conflict', input)).data
export const proposeSchedule = async input => (await api.post('/admin/schedules', input)).data
export const reviewSchedule = async (id, input) => (await api.post(`/admin/schedules/${id}/review`, input)).data
export const recheckSchedule = async (id, version) => (await api.post(`/admin/schedules/${id}/recheck`, { version })).data
export const updateInterview = async (id, input) => (await api.put(`/admin/interviews/${id}/status`, input)).data
export const getSupport = async jobId => (await api.get('/admin/support', { params: { job_id: jobId } })).data
export const runSupport = async jobId => (await api.post('/admin/support/run', { job_id: jobId }, { timeout: 120000 })).data
export const reviewSupport = async (id, input) => (await api.post(`/admin/support/${id}/review`, input)).data
