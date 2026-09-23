import { secondaryStyle } from './FormField'
export default function Pagination({ data, busy, onPage }) {
  if (!data?.total) return null
  return <nav aria-label="Results pages" className="flex flex-wrap items-center gap-4 text-sm">
    <button type="button" className={secondaryStyle} disabled={busy || data.offset === 0} onClick={() => onPage(Math.max(0, data.offset - data.limit))}>Previous</button>
    <span>{data.offset + 1}–{Math.min(data.offset + data.limit, data.total)} of {data.total}</span>
    <button type="button" className={secondaryStyle} disabled={busy || data.offset + data.limit >= data.total} onClick={() => onPage(data.offset + data.limit)}>Next</button>
  </nav>
}
