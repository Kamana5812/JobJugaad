import { api } from './client'
export const getOffers = async (studentId, offset = 0) => (await api.get(studentId ? `/students/${studentId}/offers` : '/admin/offers', { params: { offset, limit: 10 } })).data
export const getOfferCandidates = async (search = '', offset = 0) => (await api.get('/admin/offers/eligible-interviews', { params: { search, offset, limit: 20 } })).data
export const createOffer = async input => (await api.post('/admin/offers', input)).data
export const updateOffer = async (id, input) => (await api.put(`/admin/offers/${id}`, input)).data
export const respondToOffer = async (studentId, id, input) => (await api.post(`/students/${studentId}/offers/${id}/actions`, input)).data
