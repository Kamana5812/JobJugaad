import { api } from './client'

export const getPostSelection = async ({ scope = 'recorded', job_id = '', offset = 0 } = {}) =>
  (await api.get('/admin/analytics/post-selection', {
    params: { scope, ...(job_id ? { job_id: Number(job_id) } : {}), offset, limit: 20 },
  })).data

export function postSelectionErrorMessage(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(item => item.msg?.replace(/^Value error, /, '')).filter(Boolean).join(' ') || 'Check the analytics filters and retry.'
  return 'Could not load the recorded journey. Please retry; the service may be waking up.'
}
