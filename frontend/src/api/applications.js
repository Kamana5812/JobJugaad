import { api } from './client'
export const getApplications = async (studentId, offset = 0) => (await api.get(`/students/${studentId}/applications`, { params: { offset, limit: 10 } })).data
export const submitApplication = async (studentId, input) => (await api.post(`/students/${studentId}/applications`, input)).data
export const withdrawApplication = async (studentId, id, input) => (await api.post(`/students/${studentId}/applications/${id}/withdraw`, input)).data
export const getJobApplications = async (jobId, offset = 0) => (await api.get(`/recruiters/jobs/${jobId}/applications`, { params: { offset, limit: 10 } })).data
export const reviewApplication = async (jobId, id, input) => (await api.post(`/recruiters/jobs/${jobId}/applications/${id}/review`, input)).data
