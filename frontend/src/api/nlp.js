import { api } from './client'
export const getResumeSuggestions = async id => (await api.get(`/students/${id}/resume/suggestions`)).data
export const compareSemantics = async ({ studentId, jobId, applicationId, admin }) => {
  const path = studentId ? `/students/${studentId}/semantic-match/${jobId}`
    : `/${admin ? 'admin' : 'recruiters'}/jobs/${jobId}/applications/${applicationId}/semantic`
  return (await api.post(path, null, { timeout: 90000 })).data
}
