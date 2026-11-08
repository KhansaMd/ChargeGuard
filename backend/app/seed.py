import json
from pathlib import Path

from sqlmodel import Session

from app.db import engine
from app.dispute_service import sync_disputes
from app.models import Evidence

DEMO_FILE = Path(__file__).resolve().parent.parent / "demo_evidence.json"


def seed() -> None:
    """Sync real disputes from PayPal, then add the labelled merchant demo records.

    Runs on every API start, so a fresh database (new laptop, Render restart) rebuilds itself.
    """
    with Session(engine) as session:
        sync_disputes(session)
        if DEMO_FILE.exists():
            for dispute_id, items in json.loads(DEMO_FILE.read_text()).items():
                for item in items:
                    session.merge(Evidence(id=f"ev_{dispute_id}_{item['type']}", dispute_id=dispute_id,
                                           type=item["type"], source="merchant_upload", value=item["value"]))
            session.commit()
