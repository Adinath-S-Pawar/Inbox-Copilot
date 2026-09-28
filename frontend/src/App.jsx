import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL

const badgeStyles = {
  ok: 'bg-green-100 text-green-700',
  unreachable: 'bg-red-100 text-red-700',
  checking: 'bg-slate-200 text-slate-600',
}

export default function App() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col items-center justify-center gap-4">
      <h1 className="text-3xl font-bold text-slate-900">Inbox Copilot</h1>
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${badgeStyles[status]}`}>
        Backend: {status}
      </span>
    </main>
  )
}