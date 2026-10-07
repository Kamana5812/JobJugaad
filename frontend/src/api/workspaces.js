import { api } from './client'
export const getWorkspaces = async () => (await api.get('/recruiter/workspaces')).data
export const requestWorkspace = async input => (await api.post('/recruiter/workspaces', input)).data
export const switchWorkspace = async college_id => (await api.post('/recruiter/workspaces/switch', { college_id })).data
