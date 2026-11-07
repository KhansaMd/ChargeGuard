"""Go/no-go test: send a seller response to a sandbox dispute.

Usage (from backend/, with the venv active):
    python -m scripts.test_submit PP-R-XXX-12345678
"""
import sys

from app import paypal_service as pp

if len(sys.argv) < 2:
    sys.exit("Usage: python -m scripts.test_submit <DISPUTE_ID>")

dispute_id = sys.argv[1]

try:
    before = pp.get_dispute(dispute_id)
    print("Status before:", before.get("status"), "| allowed actions:", pp.allowed_actions(before))

    sent = pp.submit_seller_response(dispute_id, [{
        "evidence_type": "PROOF_OF_FULFILLMENT",
        "evidence_info": {"tracking_info": [{"carrier_name": "UPS", "tracking_number": "1Z999AA10123456784"}]},
        "notes": "Test submission from ChargeGuard. The order was shipped with UPS tracking 1Z999AA10123456784.",
    }])
    print("Submitted via:", sent["method"])
    print("PayPal response:", sent["result"] or "(empty, which means accepted)")

    after = pp.get_dispute(dispute_id)
    print("Status after:", after.get("status"), "| allowed actions:", pp.allowed_actions(after))
    print("\nGO: the backend can send a seller response to PayPal.")
except pp.PayPalError as exc:
    sys.exit(f"\nNO-GO for now: {exc}")
