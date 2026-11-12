# ChargeGuard

**AI-powered dispute investigation for small merchants on PayPal.**

ChargeGuard pulls a merchant's PayPal disputes, gathers the evidence behind each one, and uses Claude to write an investigation report and a response draft. Every finding cites the evidence record it relies on. The merchant reviews and approves, and only then does ChargeGuard send the response to PayPal.

Built for the **PayPal AI Hackathon 2026**.

- **Demo video:** _add YouTube link_
- **Live demo: [ChargeGuard live demo](https://charge-guard-jet.vercel.app/)

---

## The problem

Small online sellers lose money to "item not received" and "not as described" disputes because gathering evidence and replying before the deadline takes time they don't have. Many accept the loss. Generic AI tools make this worse: they write confident replies with no proof behind them.

## What ChargeGuard does

1. **Syncs disputes from PayPal**, including the reason, status, amount, messages and the actions PayPal currently allows.
2. **Collects evidence automatically** from the linked PayPal capture and order: payment record, item description, shipping address and shipment tracking.
3. **Checks the evidence with plain rules, before any AI runs.** Each item the dispute reason requires is marked **available**, **missing**, **unreliable** or **contradictory**.
4. **Investigates with Claude.** Claude sees only the checked evidence and returns a structured report: case summary, findings, missing information, contradictions, recommended action and a response draft.
5. **Verifies the AI's claims.** Every finding must cite evidence record IDs. The backend rejects any finding that cites a record that doesn't exist.
6. **Requires merchant approval.** Approval is blocked when evidence is unreliable, contradictory or insufficient, or when the report has unverified claims.
7. **Submits to PayPal**, only after approval, using the action PayPal allows for the dispute's current state.
8. **Logs everything.** Sync, investigation, approval, submission and failures are written to an audit log.

## How ChargeGuard uses PayPal

All calls use the free PayPal **Sandbox**.

| PayPal capability | API | Used for |
| --- | --- | --- |
| Authentication | OAuth 2.0 client credentials (`/v1/oauth2/token`) | Server-side access token, cached until expiry |
| Payments | Orders v2: create, capture | Real Sandbox test payments |
| Shipment tracking | Orders v2: add tracking | Tracking number that becomes dispute evidence |
| Payment details | Payments v2: captures | Payment record evidence |
| Disputes | Disputes API: list, get | Dispute sync, messages, deadlines, allowed actions |
| Merchant response | Disputes API: `provide-supporting-info` / `provide-evidence` | Sends the approved response; ChargeGuard reads the dispute's allowed actions and uses whichever PayPal permits right now |

The backend never attempts an action that PayPal hasn't listed as allowed for that dispute.

## Tools used

- **Anthropic Claude** (`claude-sonnet-5-5` for the demo, `claude-haiku-5-5` during development, set with `AI_MODEL`): reads the validated evidence and returns the investigation report and response draft through a forced structured tool call. The backend verifies every cited evidence ID before the report is shown.
- **PayPal Developer Platform (Sandbox)**: Orders v2, Payments, Disputes API.
- **AG Grid**: dispute and transaction tables in the dashboard.
- **Render**: hosting.
- **Postman**: testing PayPal API calls during development.

## Key features

| Feature | What it does |
| --- | --- |
| Dispute dashboard | All disputes in one AG Grid table, synced from PayPal |
| Evidence checklist | Required evidence per dispute reason, marked available, missing, unreliable or contradictory |
| Evidence management | Merchant can add evidence such as carrier or delivery confirmation |
| AI investigation | Structured report with findings linked to source records |
| Response drafting | Draft the merchant can edit before approving |
| Approval safeguards | Blocks approval on unreliable, contradictory or insufficient evidence |
| PayPal submission | Sends the approved response to PayPal after approval only |
| Audit log | Every action recorded with time and details |
| Fraud alerts (preview) | Page layout for risky-transaction alerts; currently shows sample data |

## Demo scenarios

Besides real Sandbox disputes, ChargeGuard loads three clearly labelled **synthetic** disputes so judges can see each case without creating payments:

| Demo ID | Scenario | What it shows |
| --- | --- | --- |
| DEMO-CG-001 | Complete evidence | Investigation with all five evidence types available |
| DEMO-CG-002 | Missing evidence | How missing delivery confirmation weakens the case |
| DEMO-CG-003 | Conflicting evidence | How conflicting delivery and customer records are flagged |

**Demo safety:** synthetic disputes can't be approved or submitted to PayPal, and their records are not genuine evidence. Real Sandbox disputes go through the full flow, including submission to PayPal.

## Tech stack

- **Frontend:** React, Vite, JavaScript, AG Grid, React Router
- **Backend:** Python, FastAPI, httpx
- **Database:** SQLite with SQLModel (created and filled automatically on startup)
- **AI:** Anthropic Claude via the Anthropic Python SDK
- **Payments:** PayPal REST APIs (Sandbox)

## Project structure

```
ChargeGuard/
├── backend/
│   ├── app/
│   │   ├── main.py                # API endpoints
│   │   ├── config.py              # settings from .env
│   │   ├── db.py                  # SQLite connection
│   │   ├── models.py              # database tables
│   │   ├── paypal_service.py      # all PayPal API calls
│   │   ├── dispute_service.py     # sync disputes and evidence from PayPal
│   │   ├── evidence_service.py    # evidence checklist and contradiction rules
│   │   ├── ai_service.py          # Claude investigation and claim verification
│   │   ├── submission_service.py  # approval safeguards and PayPal submission
│   │   ├── audit.py               # audit log
│   │   └── seed.py                # startup sync and demo disputes
│   ├── scripts/                   # create Sandbox payments, check disputes, test submission
│   ├── tests/
│   ├── demo_evidence.json
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── pages/                 # Overview, Disputes, Investigation, Transactions, Fraud Alerts, Audit Log
        ├── components/
        ├── services/api.js        # backend API client
        ├── App.jsx
        └── main.jsx
```

## Getting started

### Prerequisites

- Python 3.11 or later
- Node.js (LTS) and npm
- A PayPal Developer account with a **Sandbox** REST app (Client ID and Secret), with **Customer disputes** enabled
- An Anthropic API key from the Claude Console

### 1. Clone the repository

```bash
git clone https://github.com/KhansaMd/ChargeGuard.git
cd ChargeGuard
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

- **macOS / Linux:** `source .venv/bin/activate`
- **Windows PowerShell:** `.\.venv\Scripts\Activate.ps1`

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `backend/.env.example` to `backend/.env` and fill in your values:

| Variable | Example | Purpose |
| --- | --- | --- |
| `PAYPAL_CLIENT_ID` | from PayPal Sandbox app | PayPal OAuth |
| `PAYPAL_SECRET` | from PayPal Sandbox app | PayPal OAuth |
| `PAYPAL_BASE` | `https://api-m.sandbox.paypal.com` | PayPal Sandbox API |
| `ANTHROPIC_API_KEY` | from the Claude Console | Claude API |
| `AI_MODEL` | `claude-sonnet-5-5` | Claude model used for investigations |
| `DATABASE_URL` | `sqlite:///chargeguard.db` | Local database file |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed frontend URL (comma-separate several) |

Never commit `.env`. It is already listed in `.gitignore`.

### 4. Start the backend

```bash
uvicorn app.main:app --reload --port 8001
```

On startup the backend creates the database, syncs disputes from PayPal and loads the demo disputes. Interactive API docs: http://127.0.0.1:8001/docs

### 5. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

The frontend calls `http://127.0.0.1:8001` by default. To point it at another backend, set `VITE_API_BASE_URL` (for example in `frontend/.env.local`).

### 6. Optional: create a real Sandbox payment and dispute

From `backend/` with the virtual environment active:

```bash
python -m scripts.create_test_order                  # payment with tracking
python -m scripts.create_test_order --no-tracking    # payment without tracking
```

Open the printed link in a private browser window, log in as your **Sandbox personal (buyer)** account and pay. The script captures the payment automatically. Then log in to sandbox.paypal.com as the buyer, open the payment and report **"I didn't receive my item"**. After a few minutes:

```bash
python -m scripts.check_disputes    # lists disputes and the actions PayPal allows
```

Click **Sync** in the dashboard to load it.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/api/disputes/sync` | Pull disputes from PayPal |
| GET | `/api/disputes` | List disputes |
| GET | `/api/disputes/{id}` | Dispute, evidence checklist and latest report |
| POST | `/api/disputes/{id}/evidence` | Add merchant evidence |
| POST | `/api/disputes/{id}/investigate` | Run the Claude investigation |
| POST | `/api/disputes/{id}/draft` | Get the response draft |
| POST | `/api/disputes/{id}/approve` | Merchant approval |
| POST | `/api/disputes/{id}/submit` | Send the approved response to PayPal |
| GET | `/api/transactions` | Transactions |
| GET | `/api/audit` | Audit log (filter with `?dispute_id=`) |

## Testing

From `backend/`:

```bash
python -m pytest
```

The submission-safety tests check that approval and PayPal submission are blocked when they should be: synthetic disputes, unverified reports, and unreliable or contradictory evidence.

Frontend production build:

```bash
cd frontend
npm run build
```

## Safety notes

- AI findings and response drafts must be reviewed by the merchant before anything is sent.
- A valid source reference does not prove the underlying evidence is authentic.
- Missing, unreliable or contradictory evidence is never presented as verified proof.
- Nothing is sent to PayPal without explicit merchant approval.
- Synthetic demo disputes are blocked from approval and PayPal submission.
- API keys stay in the backend; the frontend never sees PayPal or Anthropic credentials.

## Project status and next steps

ChargeGuard is a hackathon prototype. Planned next steps:

- Fraud scoring on new orders before shipping (the Fraud Alerts page currently shows sample data)
- PayPal webhooks for instant dispute alerts instead of manual sync
- Attaching documents (receipts, photos) to submissions
- Persistent hosted database

## License

MIT. See [LICENSE](LICENSE).
