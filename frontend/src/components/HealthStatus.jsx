import { useEffect, useState } from 'react'
import { getHealth } from '../api/health'

export default function HealthStatus() {
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState({ state: 'checking' })

  useEffect(() => {
    const controller = new AbortController()
    getHealth(controller.signal)
      .then((data) => setResult({ state: 'connected', data }))
      .catch((error) => {
        if (!controller.signal.aborted) {
          setResult({
            state: 'error',
            message: error.response?.data?.detail || error.message,
          })
        }
      })
    return () => controller.abort()
  }, [attempt])

  const connected = result.state === 'connected'
  const checking = result.state === 'checking'

  function retry() {
    setResult({ state: 'checking' })
    setAttempt((value) => value + 1)
  }

  return (
    <section id="connection" className="rounded-2xl border border-line bg-white p-6 shadow-sm sm:p-8" aria-labelledby="connection-heading">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-muted">Live connection check</p>
      <div role="status" aria-live="polite" className="mt-5">
        <span className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${connected ? 'bg-[#E2F3E9] text-growth' : 'bg-[#FDF0E3] text-saffron-deep'}`}>
          {checking ? 'Checking connection…' : connected ? '✓ Backend connected' : '⚠ Connection needs attention'}
        </span>
        <h2 id="connection-heading" className="mt-4 text-2xl font-bold text-navy">
          {connected ? 'Jugaad Ho Gaya ✓' : checking ? 'Connecting the dots.' : 'Let’s get connected.'}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          {connected
            ? 'This page received a successful response from the JobJugaad backend.'
            : checking
              ? 'Checking the backend now. It may take a moment to wake up.'
              : result.message}
        </p>
        {connected && (
          <dl className="mt-5 divide-y divide-line border-y border-line text-sm">
            <div className="flex justify-between gap-4 py-3"><dt className="text-muted">API status</dt><dd className="font-semibold text-navy">Healthy</dd></div>
            <div className="flex justify-between gap-4 py-3"><dt className="text-muted">PostgreSQL</dt><dd className="font-semibold text-navy">{result.data.database === 'connected' ? 'Connected' : 'Not configured yet'}</dd></div>
          </dl>
        )}
      </div>
      <button type="button" onClick={retry} disabled={checking} className="mt-6 rounded-lg bg-saffron px-5 py-3 text-sm font-bold text-navy-dark transition hover:bg-saffron-deep focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-navy disabled:cursor-wait disabled:opacity-60">
        {checking ? 'Checking…' : 'Check connection again'}
      </button>
    </section>
  )
}
