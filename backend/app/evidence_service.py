
from sqlmodel import Session, select

from app.models import Dispute, Evidence

REQUIRED = {
    "MERCHANDISE_OR_SERVICE_NOT_RECEIVED": [
        "payment_record",
        "shipping_address",
        "carrier",
        "tracking_number",
        "delivery_confirmation",
    ],
    "MERCHANDISE_OR_SERVICE_NOT_AS_DESCRIBED": [
        "payment_record",
        "item_description",
        "product_photos",
        "return_policy",
    ],
    "UNAUTHORISED": [
        "payment_record",
        "shipping_address",
        "previous_orders",
        "customer_communication",
    ],
}

DEFAULT_REQUIRED = ["payment_record", "item_description"]


def find_contradictions(by_type: dict) -> list[dict]:
    issues = []

    ship = by_type.get("shipping_address")
    delivered_to = by_type.get("delivery_address")

    if ship and delivered_to and delivered_to.value.lower() not in ship.value.lower():
        issues.append({
            "issue": "Delivery address does not match the order's shipping address",
            "evidence_ids": [ship.id, delivered_to.id],
        })

    status = by_type.get("shipment_status")

    if status and "delivery_confirmation" in by_type and status.value.upper() == "CANCELLED":
        issues.append({
            "issue": "Delivery is confirmed but PayPal shows the shipment as cancelled",
            "evidence_ids": [status.id, by_type["delivery_confirmation"].id],
        })

    return issues


def check_evidence(session: Session, dispute_id: str) -> dict:
    dispute = session.get(Dispute, dispute_id)

    if not dispute:
        raise ValueError(f"Dispute not found: {dispute_id}")

    rows = session.exec(
        select(Evidence).where(Evidence.dispute_id == dispute_id)
    ).all()

    by_type = {e.type: e for e in rows}
    contradictions = find_contradictions(by_type)
    contradicted = {
        evidence_id
        for issue in contradictions
        for evidence_id in issue["evidence_ids"]
    }

    checklist = []

    for evidence_type in REQUIRED.get(dispute.reason, DEFAULT_REQUIRED):
        ev = by_type.get(evidence_type)

        if not ev:
            status = "missing"
        elif ev.id in contradicted:
            status = "contradictory"
        elif any(
            marker in (ev.value or "").lower()
            for marker in ("demo", "sample record", "test record", "placeholder")
        ):
            status = "unreliable"
        else:
            status = "available"

        checklist.append({
            "type": evidence_type,
            "status": status,
            "evidence_id": ev.id if ev else None,
        })

    return {
        "dispute_id": dispute_id,
        "reason": dispute.reason,
        "checklist": checklist,
        "contradictions": contradictions,
        "evidence": [
            {
                "id": e.id,
                "type": e.type,
                "source": e.source,
                "value": e.value,
            }
            for e in rows
        ],
    }
