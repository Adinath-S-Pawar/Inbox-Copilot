# Inbox Copilot

An AI agent that reads your inbox, drafts replies, schedules calls, and tracks deadlines and always asks before it acts.

Built for **BFWAI/HACK 26** (AI Build Challenge 2026, by Build Fast with AI) — Track 01: Autonomous Agents for Everyday Apps.
Team Lone Vector.

## The problem

Students and freelancers lose hours daily reading emails, drafting replies, scheduling calls, and tracking deadlines repetitive work that still needs judgment, which rule-based tools like Zapier or IFTTT can't handle.

## What it does

Inbox Copilot connects to Gmail and Calendar, reads incoming mail, classifies what each message needs, and proposes an action: a drafted reply, a calendar invite, or a tracked deadline. Nothing is sent or created without explicit approval.

- **Inbox triage** — classifies each email as needing a reply, a scheduled call, a tracked deadline, or no action
- **Draft replies** — writes context-aware reply drafts, flags missing information instead of inventing it
- **Smart scheduling** — checks real calendar availability and proposes free time slots
- **Deadline tracking** — extracts due dates and keeps them sorted, soonest first
- **One-tap approval** — every action is held for review; approving a reply creates a real Gmail draft (never sent automatically), approving a schedule creates a real tentative calendar event (no invite auto-sent)

## Safety

- **Sensitive content never reaches the AI.** Emails matching OTP, verification code, or financial-alert patterns are detected locally and excluded from any LLM call, before triage even runs. Their content is cleared even from the app's own API response.
- **Nothing is sent automatically.** Replies are created as Gmail *drafts*, never sent. Calendar events are created as *tentative*, with no invite emailed to the attendee — confirming with them is a manual step.
- **Minimal OAuth scopes.** `gmail.readonly`, `gmail.compose` (draft only, not send), `calendar.events`, `calendar.readonly`.
- **Drafts never fabricate missing facts.** When a reply would need information the AI doesn't have, it's marked `[NEEDS INPUT: ...]` instead of guessing.

## Demo

- **Live app:** https://inbox-copilot-tan.vercel.app — Demo mode works immediately, no sign-in required, and is fully stateless (safe for multiple concurrent visitors).
- **Demo video (public):** https://youtu.be/Q-Lq2hAwKOQ
- **Real-Gmail/Calendar walkthrough (public):** https://youtu.be/gJyrQudVv4I

## Tech stack

- **Backend:** FastAPI (Python), SQLite
- **Frontend:** React + Vite + Tailwind CSS
- **AI:** Google Gemini (`gemini-3.5-flash-lite`, free tier)
- **Integrations:** Gmail API, Google Calendar API (OAuth 2.0)
- **Deployment:** Render (backend), Vercel (frontend)

## Why Gemini free tier, and why this model

Newer Gemini models (`gemini-3.8-flash`, `gemini-3.5-flash-lite`) carry very restrictive free-tier daily quotas (as low as 20 requests/day) under high demand. `gemini-3.5-flash-lite` offers a workable balance for this project; all triage/draft/deadline calls are batched into one request per inbox sync rather than one call per email, to stay well within free-tier limits.

## Setup (local development)

### Prerequisites
- Python 3.10+, Node.js 20+, a Google account, a free Gemini API key

### 1. Clone and install
```bash
git clone <repo-url>
cd InboxCopilot

cd backend
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

cd ../frontend
npm install
```

### 2. Google Cloud setup
See `docs/google-setup.md` for full steps. Summary:
1. Create a Google Cloud project, enable the Gmail API and Google Calendar API.
2. Configure the OAuth consent screen (External, Testing mode), add your Google account as a test user.
3. Add scopes: `gmail.readonly`, `gmail.compose`, `calendar.events`, `calendar.readonly`.
4. Create an OAuth client (Web application), redirect URI `http://localhost:8000/auth/callback`.
5. Download the credentials JSON, save as `backend/credentials.json`.

### 3. Environment variables
Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env`, then fill in:
- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com/apikey)
- `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_REDIRECT_URI` — as set up above

### 4. Run
```bash
# Terminal 1 — backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```
Open http://localhost:5173. Demo mode works immediately. For "My Inbox," sign in via the prompt (only works for Google accounts added as test users — see Known Limitations).

## Testing
```bash
cd backend
pytest -v                    # fast tests, no API calls
pytest -v -m accuracy -s     # triage accuracy against the labeled sample inbox (1 real Gemini call)
```
Triage accuracy on the 25-email labeled sample set: **100%** (25/25).

## Known limitations

- **OAuth Testing mode:** the Google app is unverified and in Testing status, so real Gmail/Calendar sign-in only works for pre-approved test accounts not for arbitrary visitors. This is why Demo mode exists as the primary way to experience the app without setup.
- **Single shared login per deployment:** the deployed backend currently stores one OAuth token per server instance rather than one per visitor/session, so "My Inbox" is effectively single-user on the live deployment today.
- **Ephemeral storage on Render's free tier:** the SQLite database resets on redeploy/restart; demo mode is intentionally stateless and unaffected by this.
- **Hardcoded sign-off name** in generated drafts, not yet pulled from the signed-in account's real profile.
- **Slot suggestion** doesn't yet match the specific time an email actually requested — it offers the next generally-free slot.
- **Working hours are fixed to IST**; not yet timezone-aware per user.
