import { useEffect, useState, useCallback, useRef } from 'react'
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
          <button disabled={busy} onClick={() => onProposeTime(action)}
            className="px-3 py-1.5 text-sm rounded bg-slate-200 hover:bg-slate-300 disabled:opacity-50">
            Propose time
          </button>
        )}
        {action.category === 'deadline' ? (
          <button disabled={busy} onClick={() => onReject(action)}
            className="px-3 py-1.5 text-sm rounded bg-slate-200 hover:bg-slate-300 disabled:opacity-50">
            Dismiss
          </button>
        ) : (
          <>
            <button disabled={busy} onClick={() => onApprove(action)}
              className="px-3 py-1.5 text-sm rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50">
              Approve
            </button>
            <button disabled={busy} onClick={() => onReject(action)}
              className="px-3 py-1.5 text-sm rounded bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50">
              Reject
            </button>
          </>
        )}
      </div>
    </div>
  )
}

function makeSlotTime(index) {
  const base = new Date()
  base.setDate(base.getDate() + 1)
  base.setHours(9, 0, 0, 0)
  base.setMinutes(base.getMinutes() + index * 30)
  return base.toISOString()
}

export default function App() {
  const [source, setSource] = useState('demo')
  const [authenticated, setAuthenticated] = useState(false)
  const [actions, setActions] = useState([])
  const [loading, setLoading] = useState(false)
  const [busyId, setBusyId] = useState(null)
  const [toast, setToast] = useState(null)
  const inFlightRef = useRef(new Set())
  const takenSlotsRef = useRef(new Set())

  function showToast(message, type = 'success') {
    setToast({ message, type })
    const duration = Math.min(10000, Math.max(3000, message.length * 70))
    setTimeout(() => setToast(null), duration)
  }

  const loadRealActions = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getActions('real', 'pending')
      setActions(data.actions)
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    api.authStatus().then((d) => setAuthenticated(d.authenticated)).catch(() => setAuthenticated(false))
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('login') === 'denied') {
      showToast("Sign-in isn't available for this account yet — this app is in Google's testing mode. Try Demo mode instead.", 'error')
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  useEffect(() => {
    if (source === 'real') loadRealActions()
    else setActions([]) // demo actions are only loaded via the Sync button, see below
  }, [source, loadRealActions])

  async function handleSync() {
    setLoading(true)
    try {
      if (source === 'demo') {
        const data = await api.getDemoActions() // stateless: computed fresh, nothing saved server-side
        setActions(data.actions)
        takenSlotsRef.current = new Set()
      } else {
        await api.syncInbox('real')
        await api.generateDrafts('real')
        await loadRealActions()
      }
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  async function withBusy(id, fn) {
    if (inFlightRef.current.has(id)) return
    inFlightRef.current.add(id)
    setBusyId(id)
    try {
      const message = await fn()
      if (message) showToast(message, 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      inFlightRef.current.delete(id)
      setBusyId(null)
    }
  }

  function handleApprove(action) {
    if (action.category === 'schedule' && !action.proposed_time) {
      showToast('Please propose a time before approving this meeting.', 'error')
      return
    }
    withBusy(action.id, async () => {
      if (source === 'demo') {
        setActions((prev) => prev.filter((a) => a.id !== action.id))
        return action.category === 'reply' ? 'Approved (demo mode — no real draft created)' : 'Approved (demo mode)'
      }
      const result = await api.approveAction(action.id)
      await loadRealActions()
      if (action.category === 'reply') return result.gmail_draft_id ? 'Draft ready in Gmail' : 'Approved'
      if (action.category === 'schedule') return result.calendar_event_id ? 'Event added to Calendar' : 'Approved'
      return 'Approved'
    })
  }

  function handleReject(action) {
    withBusy(action.id, async () => {
      if (source === 'demo') {
        if (action.category === 'schedule' && action._slotIndex !== undefined) {
          takenSlotsRef.current.delete(action._slotIndex)
        }
        setActions((prev) => prev.filter((a) => a.id !== action.id))
        return action.category === 'deadline' ? 'Dismissed' : 'Rejected'
      }
      await api.rejectAction(action.id)
      await loadRealActions()
      return action.category === 'deadline' ? 'Dismissed' : 'Rejected'
    })
  }

  function handleProposeTime(action) {
    withBusy(action.id, async () => {
      if (source === 'demo') {
        let index = 0
        while (takenSlotsRef.current.has(index)) index++
        takenSlotsRef.current.add(index)
        const time = makeSlotTime(index)
        setActions((prev) => prev.map((a) => (a.id === action.id ? { ...a, proposed_time: time, _slotIndex: index } : a)))
        return null
      }
      await api.proposeTime(action.id)
      await loadRealActions()
      return null
    })
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Inbox Copilot</h1>
          <div className="flex items-center gap-2">
            <button onClick={() => setSource('demo')}
              className={`px-3 py-2 text-sm rounded leading-none ${source === 'demo' ? 'bg-slate-900 text-white' : 'bg-slate-200'}`}>
              Demo
            </button>
            <button onClick={() => setSource('real')}
              className={`px-3 py-2 text-sm rounded leading-none ${source === 'real' ? 'bg-slate-900 text-white' : 'bg-slate-200'}`}>
              My Inbox
            </button>
          </div>
        </header>

        {source === 'real' && !authenticated && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800">
            Not signed in. <a href={api.loginUrl()} className="underline font-medium">Sign in with Google</a> to use your real inbox.
            This app is in Google's testing mode — sign-in only works for pre-approved test accounts.
          </div>
        )}

        <div className="flex items-center justify-between mb-4">
          <button onClick={handleSync} disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50">
            {loading && (
              <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            {loading ? 'Syncing…' : 'Sync inbox'}
          </button>
          <span className="text-sm text-slate-500">{actions.length} pending</span>
        </div>

        <div className="space-y-3">
          {actions.map((action) => (
            <ActionCard key={action.id} action={action} busy={busyId === action.id}
              onApprove={handleApprove} onReject={handleReject} onProposeTime={handleProposeTime}
            />
          ))}
          {!loading && actions.length === 0 && (
            <p className="text-center text-slate-400 py-8">No pending actions. Click "Sync inbox" to check for new emails.</p>
          )}
        </div>
      </div>

      {toast && (
        <div className={`fixed top-5 right-5 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium border
          ${toast.type === 'success' ? 'bg-green-50 text-green-800 border-green-300' : 'bg-red-50 text-red-800 border-red-300'}`}>
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} className="text-lg leading-none opacity-60 hover:opacity-100">×</button>
        </div>
      )}
    </main>
  )
}