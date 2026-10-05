import { api } from './client'
const portal = admin => admin ? 'admin' : 'recruiters'
export const changeDriveState = async (admin, id, input) => (await api.post(`/${portal(admin)}/jobs/${id}/state`, input)).data
export const getRecordedDemand = async admin => (await api.get(`/${portal(admin)}/analytics/demand`)).data
export const getApplicationProfile = async (admin, job, application) => (await api.get(`/${portal(admin)}/jobs/${job}/applications/${application}/profile`)).data
export const checkDueReminders = async () => (await api.post('/admin/reminders/run')).data
