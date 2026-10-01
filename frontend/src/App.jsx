import { useEffect, useState, useCallback } from 'react'
import { api } from './api'

const CATEGORY_STYLES = {
  reply: 'bg-blue-100 text-blue-700',
  schedule: 'bg-purple-100 text-purple-700',
  deadline: 'bg-amber-100 text-amber-700',
}

function ActionCard({ action, onApprove, onReject, onProposeTime, busy }) {
  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${CATEGORY_STYLES[action.category] || 'bg-slate-100 text-slate-600'}`}>
          {action.category}
        </span>
        <span className="text-xs text-slate-400">{action.sender_email}</span>
      </div>
      <h3 className="font-semibold text-slate-900">{action.subject}</h3>
      <p className="text-sm text-slate-500 mt-1">{action.reason}</p>

      {action.category === 'reply' && (
        <div className="mt-3 bg-slate-50 border border-slate-100 rounded p-3 text-sm text-slate-700 whitespace-pre-wrap">
          {action.draft_text || <span className="text-slate-400 italic">No draft generated yet.</span>}
        </div>
      )}

      {action.category === 'schedule' && (
        <div className="mt-3 text-sm text-slate-700">
          {action.proposed_time
            ? <>Proposed time: <span className="font-medium">{new Date(action.proposed_time).toLocaleString()}</span></>
            : <span className="text-slate-400 italic">No time proposed yet.</span>}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        {action.category === 'schedule' && !action.proposed_time && (
          <button disabled={busy} onClick={() => onProposeTime(action.id)}
            className="px-3 py-1.5 text-sm rounded bg-slate-200 hover:bg-slate-300 disabled:opacity-50">
            Propose time
          </button>
        )}
        <button disabled={busy} onClick={() => onApprove(action.id)}
          className="px-3 py-1.5 text-sm rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50">
          Approve
        </button>
        <button disabled={busy} onClick={() => onReject(action.id)}
          className="px-3 py-1.5 text-sm rounded bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50">
          Reject
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const [source, setSource] = useState('demo')
  const [authenticated, setAuthenticated] = useState(false)
  const [actions, setActions] = useState([])
  const [loading, setLoading] = useState(false)
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState(null)

  const loadActions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getActions(source, 'pending')
      setActions(data.actions)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [source])

  useEffect(() => {
    api.authStatus().then((d) => setAuthenticated(d.authenticated)).catch(() => setAuthenticated(false))
  }, [])

  useEffect(() => {
    loadActions()
  }, [loadActions])

  async function handleSync() {
    setLoading(true)
    setError(null)
    try {
      await api.syncInbox(source)
      await api.generateDrafts(source)
      await loadActions()
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  async function withBusy(id, fn) {
    setBusyId(id)
    setError(null)
    try {
      await fn()
      await loadActions()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Inbox Copilot</h1>
          <div className="flex items-center gap-2">
            <button onClick={() => setSource('demo')}
              className={`px-3 py-1.5 text-sm rounded ${source === 'demo' ? 'bg-slate-900 text-white' : 'bg-slate-200'}`}>
              Demo
            </button>
            <button onClick={() => setSource('real')}
              className={`px-3 py-1.5 text-sm rounded ${source === 'real' ? 'bg-slate-900 text-white' : 'bg-slate-200'}`}>
              My Inbox
            </button>
          </div>
        </header>

        {source === 'real' && !authenticated && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800">
            Not signed in. <a href={api.loginUrl()} className="underline font-medium">Sign in with Google</a> to use your real inbox.
          </div>
        )}

        <div className="flex items-center justify-between mb-4">
          <button onClick={handleSync} disabled={loading}
            className="px-4 py-2 text-sm rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50">
            {loading ? 'Syncing…' : 'Sync inbox'}
          </button>
          <span className="text-sm text-slate-500">{actions.length} pending</span>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{error}</div>
        )}

        <div className="space-y-3">
          {actions.map((action) => (
            <ActionCard key={action.id} action={action} busy={busyId === action.id}
              onApprove={(id) => withBusy(id, () => api.approveAction(id))}
              onReject={(id) => withBusy(id, () => api.rejectAction(id))}
              onProposeTime={(id) => withBusy(id, () => api.proposeTime(id))}
            />
          ))}
          {!loading && actions.length === 0 && (
            <p className="text-center text-slate-400 py-8">No pending actions. Click "Sync inbox" to check for new emails.</p>
          )}
        </div>
      </div>
    </main>
  )
}