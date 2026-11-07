import sys

from app import paypal_service as pp

dispute_id = sys.argv[1]
d = pp.get_dispute(dispute_id)
actions = pp.allowed_actions(d)
if "provide_evidence" not in actions:
    print("Evidence not allowed right now. Allowed actions:", actions)
    sys.exit(1)

result = pp.provide_evidence(dispute_id, [{
    "evidence_type": "PROOF_OF_FULFILLMENT",
    "evidence_info": {"tracking_info": [{"carrier_name": "UPS", "tracking_number": "1Z999AA10123456784"}]},
    "notes": "Test submission from ChargeGuard.",
}])
print("Submitted:", result)
print("New status:", pp.get_dispute(dispute_id).get("status"))