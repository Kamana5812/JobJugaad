import { api } from './client'
export const recruiterSignup = async (input) => (await api.post('/auth/recruiter/signup', input)).data
export const getCompany = async () => (await api.get('/recruiters/company')).data
export const saveCompany = async (input) => (await api.put('/recruiters/company', input)).data
export const getJobs = async () => (await api.get('/recruiters/jobs')).data
export const createJob = async (input) => (await api.post('/recruiters/jobs', input)).data
export const runMatching = async (id) => (await api.post(`/recruiters/jobs/${id}/matching`, null, { timeout: 120000 })).data
export const getMatches = async (id, status, offset) => (await api.get(`/recruiters/jobs/${id}/matches`, { params: { status, offset, limit: 5 } })).data
export const overrideMatch = async (jobId, matchId, input) => (await api.post(`/recruiters/jobs/${jobId}/matches/${matchId}/override`, input)).data
