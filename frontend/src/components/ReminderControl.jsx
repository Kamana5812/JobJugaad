import { useState } from 'react'
import { checkDueReminders } from '../api/driveWorkflow'
import { errorMessage } from '../api/student'
import { Message, secondaryStyle } from './FormField'

export default function ReminderControl() {
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  async function run() {
    setBusy(true); setError(''); setMessage('')
    try { const data = await checkDueReminders(); setMessage(`${data.eligible_bookings_processed} eligible booking(s) processed. ${data.explanation}`) }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <aside className="space-y-3 rounded-xl border border-line bg-white p-5"><h3 className="font-bold text-navy">Due event reminders</h3>
    <p className="text-sm text-muted">Checks upcoming interviews and external assessment events in the next 24 hours. Notifications stay in-app and duplicate checks do not create duplicate reminders. The student feed also checks due reminders when opened. Service sleep can delay background checks.</p>
    <button className={secondaryStyle} disabled={busy} onClick={run}>{busy ? 'Checking…' : 'Check due in-app reminders'}</button><Message error>{error}</Message><Message>{message}</Message>
  </aside>
}
