# Senselytics Frontend

React + TypeScript + Vite frontend for the Senselytics FastAPI backend.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL if the backend isn't on :8000
npm run dev
```

## Backend requirement

The backend needs `BACKEND_CORS_ORIGINS` set to include the frontend's
origin, e.g. in the backend's `.env`:

```
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

`app/main.py` was updated to actually register `CORSMiddleware` using this
setting — previously the setting existed but was never wired up, so no
cross-origin requests would have been allowed.

## What's implemented vs. what's missing on the backend

Built strictly against the existing API (`app/api/routes/*.py`):

- **Auth** — register (`POST /auth/register`), login (`POST /auth/login`,
  form-encoded per `OAuth2PasswordRequestForm`), current user
  (`GET /users/me`). JWT stored in `localStorage`, attached as a Bearer
  header by a central Axios client.
- **Datasets** — upload, list, get, rename, delete, matching
  `app/schemas/dataset.py` exactly. There is no schema/column-preview
  endpoint on the backend, so the Datasets UI only shows what
  `DatasetListResponse`/`DatasetResponse` return (row/column counts, type,
  status) — it does not show a data preview table or column schema, since
  the backend doesn't expose one yet.
- **Ask Data** — `POST /queries/` for the question, `POST
  /queries/{thread_id}/resume` for the human-in-the-loop clarification flow
  in the LangGraph workflow. The loading UI's stage list mirrors the graph's
  real node names (`policy_check`, `detect_ambiguity`, `generate_sql`,
  `validate_sql`, `execute_sql`, `build_response`) but its *timing* is
  simulated client-side, not driven by real events — see the note in
  `AskDataPage.tsx` for why `/queries/stream` (which does emit real
  per-node SSE events) wasn't used as the source of truth: its interrupt
  payload shape for the clarification path isn't something that could be
  verified without running the backend, so the non-streaming endpoint
  (whose response shape is fully specified in `QueryResponse`) is used
  instead for correctness. A `streamQuery()` helper for the SSE endpoint
  still exists in `src/services/queryService.ts` if you want to wire it up
  after confirming the interrupt payload shape against a running backend.
- **Query History** — the backend has no history table or endpoint, so this
  is a session-local log kept in `localStorage`, clearly labeled as such in
  the UI. It is not synced across devices or browsers.
- **Visualization** — results are auto-charted per the brief's rules (date
  column + numeric → line chart, category column + numeric → bar chart,
  otherwise a table), implemented in `ResultVisualization.tsx`.
