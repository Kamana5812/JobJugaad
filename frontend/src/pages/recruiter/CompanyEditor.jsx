import { useState } from 'react'
import { saveCompany } from '../../api/recruiter'
import { errorMessage } from '../../api/student'
import { FormField, secondaryStyle, Message } from '../../components/FormField'

export default function CompanyEditor({ company, onSaved }) {
  const [name, setName] = useState(company.name)
  const [industry, setIndustry] = useState(company.industry)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('')
    try { onSaved(await saveCompany({ name, industry })); setMessage('Company profile saved.') }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <details className="rounded-2xl border border-line bg-white p-5">
    <summary className="cursor-pointer font-bold text-navy">Company profile · {company.name}</summary>
    <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={submit}>
      <FormField label="Company name" required maxLength="160" value={name} onChange={e => setName(e.target.value)} />
      <FormField label="Industry" required maxLength="100" value={industry} onChange={e => setIndustry(e.target.value)} />
      <div className="space-y-3 sm:col-span-2"><Message error>{error}</Message><Message>{message}</Message>
        <button disabled={busy} className={secondaryStyle}>{busy ? 'Saving…' : 'Save company'}</button></div>
    </form>
  </details>
}
