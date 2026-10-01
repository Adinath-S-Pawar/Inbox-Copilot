const API_URL = import.meta.env.VITE_API_URL

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${response.status}`)
  }
  return response.json()
}

export const api = {
  authStatus: () => request("/auth/status"),
  loginUrl: () => `${API_URL}/auth/login`,

  getActions: (source, status = "pending") =>
    request(`/actions?source=${source}&status=${status}`),
  approveAction: (id) => request(`/actions/${id}/approve`, { method: "POST" }),
  rejectAction: (id) => request(`/actions/${id}/reject`, { method: "POST" }),
  proposeTime: (id) => request(`/actions/${id}/propose-time`, { method: "POST" }),

  syncInbox: (source, limit = 10) =>
    request(source === "demo" ? "/triage/sync/demo" : `/triage/sync?limit=${limit}`, { method: "POST" }),
  generateDrafts: (source) => request(`/drafts/generate?source=${source}`, { method: "POST" }),
  syncDeadlines: (source) => request(`/deadlines/sync?source=${source}`, { method: "POST" }),
  getDeadlines: (source) => request(`/deadlines?source=${source}`),
}