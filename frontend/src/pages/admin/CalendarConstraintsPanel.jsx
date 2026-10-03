import { useCallback, useEffect, useState } from 'react'
import { getCalendarConstraints, cancelCalendarConstraint, calendarErrorMessage } from '../../api/calendar'
import DashboardCard from '../../components/DashboardCard'
import { Message, secondaryStyle } from '../../components/FormField'
import CalendarConstraintList from '../../components/CalendarConstraintList'
import Pagination from '../../components/Pagination'
import CalendarConstraintForm from './CalendarConstraintForm'

export default function CalendarConstraintsPanel({ students, onChanged }) {
  const [data, setData] = useState(null), [offset, setOffset] = useState(0), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const refresh = useCallback(async () => {
    setBusy(true); setError('')
    try { setData(await getCalendarConstraints(offset)) } catch (failure) { setError(calendarErrorMessage(failure)) }
    finally { setBusy(false) }
  }, [offset])
  useEffect(() => { refresh() }, [refresh])
  async function changed() { await refresh(); await onChanged() }
  async function cancel(id, input) { await cancelCalendarConstraint(id, input); await changed() }
  const resourceName = item => item.scope === 'student' ? students.find(student => student.id === item.student_id)?.name || 'Student #' + item.student_id
    : item.scope === 'campus' ? 'Entire college' : (item.scope === 'branch' ? 'Branch: ' : 'Panel: ') + item.resource_name
  return <DashboardCard title="Availability and exam calendar" label="Dated windows · recorded history">
    <p className="mb-4 text-sm text-muted">Dated entries apply independently of working hours. Changes do not move or cancel confirmed interviews; they raise calendar alerts for administrator review.</p>
    <details className="mb-5 rounded-xl border border-line p-4"><summary className="cursor-pointer text-sm font-semibold text-navy">Add student/panel availability or an exam block</summary>
      <div className="mt-4"><CalendarConstraintForm students={students} onSaved={changed} /></div>
    </details>
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold text-navy">Calendar entry history</h3><button className={secondaryStyle} disabled={busy} onClick={refresh}>{busy ? 'Refreshing…' : 'Refresh entries'}</button></div>
    <Message error>{error}</Message><CalendarConstraintList data={data} resourceName={resourceName} onCancel={cancel} busy={busy} />
    <div className="mt-4"><Pagination data={data} busy={busy} onPage={setOffset} /></div>
  </DashboardCard>
}
