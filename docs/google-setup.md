# Google Cloud setup

1. Create a Google Cloud project and enable the Gmail API and Google Calendar API.
2. Configure Google Auth Platform: Audience = External, status = Testing, add your Google account as a test user.
3. Add scopes: gmail.readonly, gmail.compose, calendar.events.
4. Create an OAuth client (Web application) with redirect URI `http://localhost:8000/auth/callback`.
5. Download the JSON, rename it to `credentials.json`, and place it in `backend/`. Never commit this file.