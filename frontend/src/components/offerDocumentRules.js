export const formatFileSize = bytes => bytes >= 1024 * 1024 ? (bytes / (1024 * 1024)).toFixed(1) + ' MiB' : Math.ceil(bytes / 1024) + ' KiB'
export const openOffer = offer => offer.offer_letter_status !== 'withdrawn' && offer.acceptance_status !== 'declined' && offer.joining_status === 'pending'
export const canUploadOfferDocument = (offer, admin) => openOffer(offer) && (admin ? offer.offer_letter_status === 'draft' : offer.offer_letter_status === 'issued' && ['pending', 'changes_requested'].includes(offer.documents_status))
export const canReviewOfferDocument = (file, offer, admin) => admin && openOffer(offer) && file.is_active && file.review_status === 'pending' && (file.kind === 'offer_letter' ? offer.offer_letter_status === 'draft' : offer.offer_letter_status === 'issued' && offer.documents_status === 'submitted')
export const studentLetterAvailable = offer => offer.offer_letter_status === 'issued' || offer.audit?.some(event => event.action === 'offer_letter_status:issued' || event.snapshot?.after?.offer_letter_status === 'issued')

export function uploadDocumentInput(file, form, version, limits, key) {
  if (!file || file.size === 0) throw new Error('Choose a non-empty PDF file.')
  if (!file.name.toLowerCase().endsWith('.pdf')) throw new Error('Choose a file with a .pdf extension; the server also checks its PDF structure.')
  if (file.size > limits.max_bytes) throw new Error('Choose a PDF no larger than ' + formatFileSize(limits.max_bytes) + '.')
  if (limits.stored_files >= limits.max_files || limits.stored_bytes + file.size > limits.max_offer_bytes) throw new Error('This offer has reached its retained-file storage limit. Replacements also retain the earlier file.')
  const label = form.label.trim(), reason = form.reason.trim()
  if (label.length < 3 || label.length > 160) throw new Error('Enter a file label between 3 and 160 characters.')
  if (reason.length < 10 || reason.length > 1000) throw new Error('Enter an upload reason between 10 and 1000 characters.')
  return { file, version, label, reason, idempotency_key: key, replaces_document_id: form.replaces_document_id ? Number(form.replaces_document_id) : null }
}
