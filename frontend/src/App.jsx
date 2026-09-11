import { useState, useEffect } from 'react'
import axios from 'axios'

function App() {
  const [healthStatus, setHealthStatus] = useState('Checking...')
  const [error, setError] = useState(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const response = await axios.get(`${apiUrl}/health`)
        setHealthStatus(response.data.status === 'ok' ? 'Online' : 'Unexpected response')
      } catch (err) {
        setError(err.message)
        setHealthStatus('Offline')
      }
    }
    
    checkHealth()
  }, [])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-sm border border-line w-full max-w-md text-center">
        <h1 className="text-3xl font-bold text-navy mb-2">JobJugaad</h1>
        <p className="text-muted mb-6">Placement ka Jugaad, AI ke Saath.</p>
        
        <div className="flex flex-col gap-4">
          <div className="p-4 rounded bg-paper border border-line">
            <p className="text-sm font-semibold text-muted mb-1">Backend Status</p>
            <div className="flex items-center justify-center gap-2">
              <div className={`w-3 h-3 rounded-full ${healthStatus === 'Online' ? 'bg-green-subtle' : 'bg-red-500'}`}></div>
              <span className={`font-bold ${healthStatus === 'Online' ? 'text-green-subtle' : 'text-red-500'}`}>
                {healthStatus}
              </span>
            </div>
            {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
