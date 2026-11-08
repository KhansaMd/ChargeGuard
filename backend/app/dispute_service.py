from sqlmodel import Session

from app import paypal_service as pp
from app.audit import log
from app.models import Dispute, Evidence, Transaction


def _ev(session: Session, dispute_id: str, type_: str, source: str, value) -> None:
    """Save one fact as an evidence row (skips empty values)."""
    if value in (None, "", []):
        return
    session.merge(Evidence(id=f"ev_{dispute_id}_{type_}", dispute_id=dispute_id,
                           type=type_, source=source, value=str(value)))


def sync_disputes(session: Session) -> int:
    items = pp.list_disputes().get("items", [])
    for item in items:
        sync_one(session, item["dispute_id"])
    log(session, "sync", count=len(items))
    return len(items)


def sync_one(session: Session, dispute_id: str) -> None:
    d = pp.get_dispute(dispute_id)
    tx = (d.get("disputed_transactions") or [{}])[0]
    capture_id = tx.get("seller_transaction_id")
    amount = d.get("dispute_amount", {})

    session.merge(Dispute(
        id=dispute_id, transaction_id=capture_id, reason=d.get("reason"),
        status=d.get("status"), stage=d.get("dispute_life_cycle_stage"),
        amount=amount.get("value"), currency=amount.get("currency_code"),
        due_date=d.get("seller_response_due_date"), created_at=d.get("create_time"), raw=d,
    ))
    _ev(session, dispute_id, "dispute_reason", "paypal_dispute", d.get("reason"))
    for i, msg in enumerate(d.get("messages", []), start=1):
        _ev(session, dispute_id, f"message_{i}", "paypal_dispute",
            f"{msg.get('posted_by')} at {msg.get('time_posted')}: {msg.get('content')}")

    if capture_id:
        _order_evidence(session, dispute_id, capture_id)
    session.commit()


def _order_evidence(session: Session, dispute_id: str, capture_id: str) -> None:
    cap = pp.get_capture(capture_id)
    money = cap.get("amount", {})
    _ev(session, dispute_id, "payment_record", "paypal_capture",
        f"{money.get('value')} {money.get('currency_code')} captured {cap.get('create_time')}, status {cap.get('status')}")

    order_id = cap.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
    if not order_id:
        return
    order = pp.get_order(order_id)
    unit = order["purchase_units"][0]
    shipping = unit.get("shipping", {})
    address = shipping.get("address", {})

    _ev(session, dispute_id, "item_description", "paypal_order", unit.get("description"))
    _ev(session, dispute_id, "shipping_address", "paypal_order",
        ", ".join(v for v in address.values() if v))

    trackers = shipping.get("trackers", [])
    if trackers:
        t = trackers[0]
        # Tracker IDs look like "<capture_id>-<tracking_number>"; check your real response.
        _ev(session, dispute_id, "tracking_number", "paypal_order", t["id"].split("-", 1)[-1])
        _ev(session, dispute_id, "shipment_status", "paypal_order", t.get("status"))

    session.merge(Transaction(
        id=capture_id, order_id=order_id, amount=money.get("value"),
        currency=money.get("currency_code"),
        payer_email=order.get("payer", {}).get("email_address"),
        shipping_address=address, created_at=cap.get("create_time"),
    ))