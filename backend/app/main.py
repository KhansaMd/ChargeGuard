"""ChargeGuard API.

AI routes (/investigate, /draft, /approve, /submit) switch on automatically once
app/ai_service.py has investigate() and app/submission_service.py has
latest_report(), approve() and submit(). Until then they return 501 "coming soon",
so nobody needs to edit this file to connect Steps 8 and 9.
"""
import importlib
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from app import dispute_service
from app.audit import log
from app.config import settings
from app.db import get_session, init_db
from app.evidence_service import check_evidence
from app.models import AuditLog, Dispute, Evidence, Report, Transaction
from app.paypal_service import PayPalError
from app.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        seed()
    except Exception as exc:  # the API still starts if PayPal is unreachable
        print("Startup seed failed:", exc)
    yield


app = FastAPI(title="ChargeGuard API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.frontend_origin.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- helpers ----------

class EvidenceIn(BaseModel):
    type: str
    value: str


class ApproveIn(BaseModel):
    report_id: int
    approved_by: str = "merchant"
    edited_draft: str | None = None


def dispute_or_404(session: Session, dispute_id: str) -> Dispute:
    dispute = session.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(404, "Dispute not found. Run POST /api/disputes/sync first.")
    return dispute


def feature(module: str, *names: str):
    """Return the module if Steps 8/9 code exists, else raise 501 'coming soon'."""
    try:
        mod = importlib.import_module(f"app.{module}")
    except ModuleNotFoundError:
        mod = None
    if mod is None or not all(hasattr(mod, n) for n in names):
        raise HTTPException(501, f"Coming soon: {module}.py is not finished yet.")
    return mod


def latest_report(session: Session, dispute_id: str) -> Report | None:
    return session.exec(select(Report).where(Report.dispute_id == dispute_id)
                        .order_by(Report.id.desc())).first()


# ---------- general ----------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- disputes ----------

@app.post("/api/disputes/sync")
def sync(session: Session = Depends(get_session)):
    try:
        return {"synced": dispute_service.sync_disputes(session)}
    except PayPalError as exc:
        raise HTTPException(502, str(exc))


@app.get("/api/disputes")
def list_disputes(session: Session = Depends(get_session)):
    return [d.model_dump(exclude={"raw"}) for d in session.exec(select(Dispute)).all()]


@app.get("/api/disputes/{dispute_id}")
def dispute_detail(dispute_id: str, session: Session = Depends(get_session)):
    dispute = dispute_or_404(session, dispute_id)
    report = latest_report(session, dispute_id)
    return {
        "dispute": dispute.model_dump(exclude={"raw"}),
        "evidence_check": check_evidence(session, dispute_id),
        "report": report.model_dump() if report else None,
    }


@app.post("/api/disputes/{dispute_id}/evidence")
def add_evidence(dispute_id: str, body: EvidenceIn, session: Session = Depends(get_session)):
    dispute_or_404(session, dispute_id)
    session.merge(Evidence(id=f"ev_{dispute_id}_{body.type}", dispute_id=dispute_id,
                           type=body.type, source="merchant_upload", value=body.value))
    session.commit()
    log(session, "add_evidence", dispute_id, type=body.type)
    return check_evidence(session, dispute_id)


# ---------- AI and submission (Steps 8 and 9) ----------

@app.post("/api/disputes/{dispute_id}/investigate")
def investigate(dispute_id: str, session: Session = Depends(get_session)):
    ai = feature("ai_service", "investigate")
    dispute_or_404(session, dispute_id)
    return ai.investigate(session, dispute_id).model_dump()


@app.post("/api/disputes/{dispute_id}/draft")
def draft(dispute_id: str, session: Session = Depends(get_session)):
    ai = feature("ai_service", "investigate")
    dispute_or_404(session, dispute_id)
    report = latest_report(session, dispute_id) or ai.investigate(session, dispute_id)
    return {"report_id": report.id, "response_draft": report.data.get("response_draft"),
            "verified": report.verified}


@app.post("/api/disputes/{dispute_id}/approve")
def approve(dispute_id: str, body: ApproveIn, session: Session = Depends(get_session)):
    sub = feature("submission_service", "approve")
    dispute_or_404(session, dispute_id)
    try:
        report = sub.approve(session, dispute_id, body.report_id, body.approved_by, body.edited_draft)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return report.model_dump()


@app.post("/api/disputes/{dispute_id}/submit")
def submit(dispute_id: str, session: Session = Depends(get_session)):
    sub = feature("submission_service", "submit")
    dispute_or_404(session, dispute_id)
    try:
        result = sub.submit(session, dispute_id)
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    except RuntimeError as exc:  # includes PayPalError
        raise HTTPException(502, str(exc))
    return {"submitted": True, "paypal_response": result,
            "dispute": session.get(Dispute, dispute_id).model_dump(exclude={"raw"})}


# ---------- other data ----------

@app.get("/api/transactions")
def transactions(session: Session = Depends(get_session)):
    return session.exec(select(Transaction)).all()


@app.get("/api/audit")
def audit(dispute_id: str | None = None, session: Session = Depends(get_session)):
    query = select(AuditLog).order_by(AuditLog.id.desc())
    if dispute_id:
        query = query.where(AuditLog.dispute_id == dispute_id)
    return session.exec(query).all()
