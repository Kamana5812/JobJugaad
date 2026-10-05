import { api } from './client'
export const getCollegeStudents = async params => (await api.get('/admin/students', { params })).data
export const getCollegeStudentProfile = async id => (await api.get(`/admin/students/${id}/profile`)).data
export const getCollegeJobs = async () => (await api.get('/admin/jobs')).data
export const getCollegeMatches = async (id, status, offset) => (await api.get(`/admin/jobs/${id}/matches`, { params: {status, offset, limit:5} })).data
export const runCollegeMatching = async id => (await api.post(`/admin/jobs/${id}/matching`, null, {timeout:120000})).data
export const overrideCollegeMatch = async (job, match, input) => (await api.post(`/admin/jobs/${job}/matches/${match}/override`, input)).data
export const getCollegeApplications = async (id, offset=0) => (await api.get(`/admin/jobs/${id}/applications`, {params:{offset,limit:10}})).data
export const reviewCollegeApplication = async (job, id, input) => (await api.post(`/admin/jobs/${job}/applications/${id}/review`, input)).data
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
