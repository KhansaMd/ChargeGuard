from app import paypal_service as pp

items = pp.list_disputes().get("items", [])
print(f"{len(items)} dispute(s) found")
for item in items:
    d = pp.get_dispute(item["dispute_id"])
    print("\n", d["dispute_id"], "|", d.get("reason"), "|", d.get("status"), "|",
          d.get("dispute_life_cycle_stage"), "| due:", d.get("seller_response_due_date"))
    print("  allowed actions:", pp.allowed_actions(d))