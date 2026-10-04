import { api } from './client'
import { errorMessage } from './student'

const documentsPath = (offerId, studentId) => (studentId ? `/students/${studentId}/offers/${offerId}` : `/admin/offers/${offerId}`) + '/documents'
export const getOfferDocuments = async (offerId, studentId = null, offset = 0) => (await api.get(documentsPath(offerId, studentId), { params: { offset, limit: 10 } })).data
export const getOfferDocumentEvents = async (offerId, documentId, studentId = null, offset = 0) => (await api.get(`${documentsPath(offerId, studentId)}/${documentId}/events`, { params: { offset, limit: 10 } })).data
export const reviewOfferDocument = async (offerId, documentId, input) => (await api.post(`${documentsPath(offerId, null)}/${documentId}/review`, input)).data
export async function uploadOfferDocument(offerId, studentId, input) {
  const body = new FormData()
  body.append('file', input.file)
  for (const key of ['version', 'reason', 'label', 'idempotency_key', 'replaces_document_id']) {
    if (input[key] !== null && input[key] !== undefined && input[key] !== '') body.append(key, String(input[key]))
  }
  if (!studentId) body.append('kind', 'offer_letter')
  return (await api.post(documentsPath(offerId, studentId), body)).data
}
export async function downloadOfferDocument(offerId, documentId, studentId = null) {
  try { return (await api.get(`${documentsPath(offerId, studentId)}/${documentId}/download`, { responseType: 'blob' })).data }
  catch (failure) {
    if (failure.response?.data instanceof Blob) {
      try { failure.response.data = JSON.parse(await failure.response.data.text()) }
      catch { failure.response.data = { detail: 'The private PDF could not be downloaded. Please refresh and retry.' } }
    }
    throw failure
  }
}
export function offerDocumentErrorMessage(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail.map(item => item?.msg).filter(message => typeof message === 'string')
    if (messages.length) return messages.join(' ').replaceAll('Value error, ', '')
  }
  return errorMessage(error)
}
export function saveDownloadedPdf(blob, offerId, documentId) {
  const url = URL.createObjectURL(blob), anchor = document.createElement('a')
  anchor.href = url; anchor.download = `offer-document-${documentId}.pdf`
  document.body.appendChild(anchor)
  try { anchor.click() } finally { anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000) }
}
