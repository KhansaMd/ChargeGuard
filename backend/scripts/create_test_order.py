"""Create a sandbox payment for ChargeGuard demos.

Usage (from backend/, with the venv active):
    python -m scripts.create_test_order                  # payment with tracking (Scenario 1)
    python -m scripts.create_test_order --no-tracking    # payment without tracking (Scenario 2)
    python -m scripts.create_test_order --order 5O1234   # resume an order you already created
"""
import argparse
import sys

from app import paypal_service as pp

parser = argparse.ArgumentParser(description="Create and capture a PayPal sandbox test payment.")
parser.add_argument("--no-tracking", action="store_true", help="skip adding tracking (missing-evidence scenario)")
parser.add_argument("--order", help="resume an existing order ID instead of creating a new one")
parser.add_argument("--amount", default="49.99", help="order amount in USD (default 49.99)")
args = parser.parse_args()

try:
    if args.order:
        order = pp.get_order(args.order)
        print("Resuming order:", order["id"], "| status:", order.get("status"))
    else:
        order = pp.create_order(amount=args.amount)
        print("Order ID:", order["id"])

    if order.get("status") not in ("APPROVED", "COMPLETED"):
        print("\n1. Open this link in a Chrome INCOGNITO window (Cmd + Shift + N):")
        print("  ", pp.approval_link(order))
        print("2. Log in with the sandbox BUYER (...@personal.example.com), not the business account.")
        print("3. Click Pay / Complete Purchase. You will land on an example.com page; that's expected.")
        print("\nWaiting for your payment (checks every 3 seconds, up to 10 minutes)... Ctrl + C to stop.")

    status = pp.wait_for_approval(order["id"])
    if status == "VOIDED":
        sys.exit("The order was cancelled or expired. Run the script again for a new one.")
    if status not in ("APPROVED", "COMPLETED"):
        sys.exit(f"Still not approved (status: {status}). Finish paying, then resume with:\n"
                 f"  python -m scripts.create_test_order --order {order['id']}")

    if status == "APPROVED":
        print("Payment approved. Capturing...")
        captured = pp.capture_order(order["id"])
    else:
        print("Order was already captured.")
        captured = pp.get_order(order["id"])

    capture_id = pp.capture_id_from(captured)
    print("Capture (transaction) ID:", capture_id)

    if args.no_tracking:
        print("No tracking added (missing-evidence scenario).")
    else:
        pp.add_tracking(order["id"], capture_id, "1Z999AA10123456784")
        print("Tracking added (UPS 1Z999AA10123456784).")

    print(f"\nDone. Save these in your notes:\n  Order ID:   {order['id']}\n  Capture ID: {capture_id}")

except KeyboardInterrupt:
    sys.exit("\nStopped. Resume later with: python -m scripts.create_test_order --order <ORDER_ID>")
except pp.PayPalError as exc:
    sys.exit(f"\n{exc}")
