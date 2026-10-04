import { api } from './client'

export const getAssessments = async (studentId, params = {}) => (await api.get(
  studentId ? `/students/${studentId}/assessments` : '/admin/assessments', { params })).data
export const recordAssessment = async payload => (await api.post('/admin/assessments', payload)).data
export const withdrawAssessment = async (id, reason) => (await api.post(`/admin/assessments/${id}/withdraw`, { reason })).data
