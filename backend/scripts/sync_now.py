import json

from sqlmodel import Session, select

from app.db import engine, init_db
from app.dispute_service import sync_disputes
from app.evidence_service import check_evidence
from app.models import Dispute

init_db()
with Session(engine) as session:
    print("Synced:", sync_disputes(session))
    for d in session.exec(select(Dispute)).all():
        print(json.dumps(check_evidence(session, d.id)["checklist"], indent=2))