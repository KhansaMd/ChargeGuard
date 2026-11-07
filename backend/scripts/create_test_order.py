import sys

from app import paypal_service as pp

with_tracking = "--no-tracking" not in sys.argv

order = pp.create_order()
link = next(l["href"] for l in order["links"] if l["rel"] in ("payer-action", "approve"))
print("Order ID:", order["id"])
print("Open this link and pay as the sandbox BUYER:\n", link)
input("After paying (you will land on example.com), press Enter here...")

captured = pp.capture_order(order["id"])
capture_id = captured["purchase_units"][0]["payments"]["captures"][0]["id"]
print("Capture (transaction) ID:", capture_id)

if with_tracking:
    pp.add_tracking(order["id"], capture_id, "1Z999AA10123456784")
    print("Tracking added.")
else:
    print("No tracking added (missing-evidence scenario).")