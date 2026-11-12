ChargeGuard

AI-powered dispute investigation and fraud prevention for small merchants using PayPal.

ChargeGuard helps merchants investigate payment disputes, organise transaction evidence, identify missing or conflicting information, and prepare responses for merchant review.

Key Features

Dispute Dashboard: View and manage disputes in one workspace.

AI Investigation: Analyse available transaction evidence and generate findings with references to source records.

Evidence Management: Add and review evidence associated with a dispute.

Evidence Checklist: Identify available, missing, unreliable, or contradictory evidence.

Response Drafting: Generate a merchant response draft for review and editing.

Approval Safeguards: Block approval when evidence is unreliable, contradictory, or insufficient.

Fraud Monitoring: Provide a foundation for identifying potentially risky transactions.

Auditability: Keep investigation findings linked to their supporting evidence.

Demo Scenarios

ChargeGuard includes three clearly labelled synthetic demo disputes:

Demo ID

Scenario

Purpose

DEMO-CG-001

Complete evidence

Demonstrates an investigation with all five evidence types available.

DEMO-CG-002

Missing evidence

Demonstrates how missing delivery confirmation affects an investigation.

DEMO-CG-003

Conflicting evidence

Demonstrates how conflicting delivery and customer communication records are identified.

Demo safety: Synthetic demo disputes cannot be approved or submitted to PayPal. Demo records are not genuine transaction evidence.

Technology Stack

Frontend: React, Vite, JavaScript, AG Grid

Backend: Python, FastAPI

Database: SQLite, SQLModel

AI: Anthropic Claude

Payment integration: PayPal APIs and Sandbox

Project Structure

ChargeGuard/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── ai_service.py
│   │   ├── dispute_service.py
│   │   ├── evidence_service.py
│   │   ├── submission_service.py
│   │   ├── seed.py
│   │   └── models.py
│   ├── tests/
│   └── demo_evidence.json
└── frontend/
    └── src/
        ├── pages/
        ├── services/
        ├── App.jsx
        └── main.jsx

Getting Started

Prerequisites

Python 3.11 or later

Node.js and npm

PayPal Sandbox credentials

Anthropic API key

1. Clone the repository

git clone https://github.com/KhansaMd/ChargeGuard.git
cd ChargeGuard

2. Set up the backend

cd backend
python -m venv .venv

Activate the virtual environment.

Windows PowerShell:

.\.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Create a .env file in the backend directory and configure the required environment variables using the names expected by the application. Never commit API keys or credentials.

Start the backend:

uvicorn app.main:app --reload --port 8001

3. Set up the frontend

Open a second terminal:

cd frontend
npm install
npm run dev

Open the local URL displayed by Vite, normally:

http://localhost:5173

Testing

Run the backend test suite from the backend directory:

python -m pytest

The current submission-safety test suite contains 14 passing tests.

Build the frontend for production:

cd frontend
npm run build

Important Safety Notes

AI-generated findings and response drafts must be reviewed by a merchant.

A source reference being valid does not automatically mean the underlying evidence is authentic.

Missing, unreliable, or contradictory evidence must not be presented as verified proof.

Synthetic demo disputes are blocked from approval and PayPal submission.

ChargeGuard stores the prepared evidence and response within the application; it does not automatically submit evidence to PayPal.

Project Status

ChargeGuard is a hackathon prototype demonstrating AI-assisted dispute investigation, evidence management, response drafting, and approval safeguards. Some integrations and production capabilities may require further development.

Built for the PayPal Hackathon.