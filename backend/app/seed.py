import json
from pathlib import Path

from sqlmodel import Session

from app.db import engine
from app.dispute_service import sync_disputes
from app.models import Dispute, Evidence

DEMO_FILE = Path(__file__).resolve().parent.parent / "demo_evidence.json"


def seed() -> None:
    """Sync PayPal disputes and load separate, clearly labelled demo cases."""

    with Session(engine) as session:
        try:
            sync_disputes(session)
        except Exception as exc:
            print("PayPal sync skipped:", exc)

        # Remove only the two known legacy demo records attached
        # to the real PayPal dispute.
        legacy_records = {
            "ev_PP-R-NHW-10197039_carrier": "UPS",
            "ev_PP-R-NHW-10197039_delivery_confirmation":
                "Demo merchant record: delivered and left at front door",
        }

        for evidence_id, expected_value in legacy_records.items():
            record = session.get(Evidence, evidence_id)
            if (
                record
                and record.source == "merchant_upload"
                and record.value == expected_value
            ):
                session.delete(record)

        if DEMO_FILE.exists():
            demo_cases = json.loads(DEMO_FILE.read_text(encoding="utf-8"))

            for dispute_id, case in demo_cases.items():
                session.merge(
                    Dispute(
                        id=dispute_id,
                        transaction_id=case["transaction_id"],
                        reason=case["reason"],
                        status=case["status"],
                        stage=case["stage"],
                        amount=case["amount"],
                        currency=case["currency"],
                        due_date=case["due_date"],
                        created_at=case["created_at"],
                        raw={"is_demo": True, "label": case["label"]},
                    )
                )

                for item in case["evidence"]:
                    session.merge(
                        Evidence(
                            id=f"ev_{dispute_id}_{item['type']}",
                            dispute_id=dispute_id,
                            type=item["type"],
                            source="demo_seed",
                            value=item["value"],
                        )
                    )

        session.commit()
        print("ChargeGuard demo cases loaded.")