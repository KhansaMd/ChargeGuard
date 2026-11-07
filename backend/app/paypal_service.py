import json
import time

import httpx

from app.config import settings

_token = {"value": None, "expires_at": 0.0}


class PayPalError(RuntimeError):
    """A PayPal API call failed. Carries the HTTP status and PayPal's error body."""

    def __init__(self, status: int, body: dict | str, message: str):
        super().__init__(message)
        self.status = status
        self.body = body


def _error_message(r: httpx.Response) -> tuple[dict | str, str]:
    try:
        body = r.json()
    except ValueError:
        return r.text, f"PayPal {r.status_code}: {r.text}"
    issues = [d.get("issue") for d in body.get("details", []) if d.get("issue")]
    name = body.get("name") or body.get("error") or "ERROR"
    text = body.get("message") or body.get("error_description") or ""
    debug = body.get("debug_id")
    msg = f"PayPal {r.status_code} {name}"
    if issues:
        msg += f" ({', '.join(issues)})"
    if text:
        msg += f": {text}"
    if debug:
        msg += f" [debug_id {debug}]"
    return body, msg


def get_token() -> str:
    """Get a PayPal access token, reusing it until it is about to expire."""
    if _token["value"] and time.time() < _token["expires_at"] - 60:
        return _token["value"]
    r = httpx.post(
        f"{settings.paypal_base}/v1/oauth2/token",
        auth=(settings.paypal_client_id, settings.paypal_secret),
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    if r.status_code == 401:
        raise PayPalError(401, r.text, "PayPal rejected the Client ID or Secret in backend/.env. "
                          "Re-copy both from the SANDBOX app in Apps & Credentials.")
    if r.status_code >= 400:
        body, msg = _error_message(r)
        raise PayPalError(r.status_code, body, msg)
    data = r.json()
    _token["value"] = data["access_token"]
    _token["expires_at"] = time.time() + data["expires_in"]
    return _token["value"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}


def _check(r: httpx.Response) -> dict:
    if r.status_code >= 400:
        body, msg = _error_message(r)
        raise PayPalError(r.status_code, body, msg)
    return r.json() if r.content else {}


def get(path: str, params: dict | None = None) -> dict:
    return _check(httpx.get(settings.paypal_base + path, headers=_headers(), params=params, timeout=30))


def post(path: str, body: dict | None = None) -> dict:
    return _check(httpx.post(settings.paypal_base + path, headers=_headers(), json=body or {}, timeout=30))


# ---------- Orders ----------

def create_order(amount: str = "49.99", description: str = "ChargeGuard test item") -> dict:
    return post("/v2/checkout/orders", {
        "intent": "CAPTURE",
        "purchase_units": [{
            "description": description,
            "amount": {"currency_code": "USD", "value": amount},
        }],
        "payment_source": {"paypal": {"experience_context": {
            "brand_name": "ChargeGuard Demo Store",
            "shipping_preference": "GET_FROM_FILE",  # buyer's sandbox address, needed as dispute evidence
            "user_action": "PAY_NOW",
            "return_url": "https://example.com/return",
            "cancel_url": "https://example.com/cancel",
        }}},
    })


def approval_link(order: dict) -> str:
    """The checkout URL the buyer must open to approve the order."""
    for link in order.get("links", []):
        if link.get("rel") in ("payer-action", "approve"):
            return link["href"]
    raise PayPalError(0, order, "PayPal did not return an approval link for this order.")


def get_order(order_id: str) -> dict:
    return get(f"/v2/checkout/orders/{order_id}")


def wait_for_approval(order_id: str, timeout_s: int = 600, interval_s: int = 3) -> str:
    """Poll the order until the buyer approves it. Returns the final status.

    CREATED / PAYER_ACTION_REQUIRED = buyer hasn't finished checkout yet.
    APPROVED = ready to capture. COMPLETED = already captured. VOIDED = cancelled/expired.
    """
    deadline = time.time() + timeout_s
    status = None
    while time.time() < deadline:
        status = get_order(order_id).get("status")
        if status in ("APPROVED", "COMPLETED", "VOIDED"):
            return status
        time.sleep(interval_s)
    return status or "UNKNOWN"


def capture_order(order_id: str) -> dict:
    return post(f"/v2/checkout/orders/{order_id}/capture")


def capture_id_from(captured: dict) -> str:
    return captured["purchase_units"][0]["payments"]["captures"][0]["id"]


def get_capture(capture_id: str) -> dict:
    return get(f"/v2/payments/captures/{capture_id}")


def add_tracking(order_id: str, capture_id: str, tracking_number: str, carrier: str = "UPS") -> dict:
    return post(f"/v2/checkout/orders/{order_id}/track", {
        "capture_id": capture_id,
        "tracking_number": tracking_number,
        "carrier": carrier,
        "notify_payer": False,
    })


# ---------- Disputes ----------

def list_disputes() -> dict:
    return get("/v1/customer/disputes", params={"page_size": 50})


def get_dispute(dispute_id: str) -> dict:
    return get(f"/v1/customer/disputes/{dispute_id}")


def allowed_actions(dispute: dict) -> list[str]:
    """The actions PayPal allows right now, from the dispute's links."""
    return [link["rel"] for link in dispute.get("links", [])]


def provide_evidence(dispute_id: str, evidences: list[dict], files: list[tuple] | None = None) -> dict:
    """Multipart request: a JSON part named 'input' plus optional files (name, bytes, mime)."""
    parts = {"input": (None, json.dumps({"evidences": evidences}), "application/json")}
    for i, (name, content, mime) in enumerate(files or []):
        parts[f"file{i + 1}"] = (name, content, mime)
    r = httpx.post(
        f"{settings.paypal_base}/v1/customer/disputes/{dispute_id}/provide-evidence",
        headers={"Authorization": f"Bearer {get_token()}"},
        files=parts,
        timeout=60,
    )
    return _check(r)


def provide_supporting_info(dispute_id: str, notes: str, files: list[tuple] | None = None) -> dict:
    """Send the seller's information while PayPal reviews a dispute (status UNDER_REVIEW).

    Multipart request: a JSON part named 'input' with notes, plus optional files (name, bytes, mime).
    """
    parts = {"input": (None, json.dumps({"notes": notes[:2000]}), "application/json")}
    for i, (name, content, mime) in enumerate(files or []):
        parts[f"file{i + 1}"] = (name, content, mime)
    r = httpx.post(
        f"{settings.paypal_base}/v1/customer/disputes/{dispute_id}/provide-supporting-info",
        headers={"Authorization": f"Bearer {get_token()}"},
        files=parts,
        timeout=60,
    )
    return _check(r)


def submit_seller_response(dispute_id: str, evidences: list[dict], files: list[tuple] | None = None) -> dict:
    """Send the merchant's response using whichever action PayPal allows right now.

    WAITING_FOR_SELLER_RESPONSE -> provide_evidence (structured evidence)
    UNDER_REVIEW               -> provide_supporting_info (notes + files)
    Returns {"method": ..., "result": ...}.
    """
    actions = allowed_actions(get_dispute(dispute_id))
    if "provide_evidence" in actions:
        return {"method": "provide_evidence", "result": provide_evidence(dispute_id, evidences, files)}
    if "provide_supporting_info" in actions:
        lines = []
        for ev in evidences:
            for t in ev.get("evidence_info", {}).get("tracking_info", []):
                lines.append(f"Tracking: {t.get('carrier_name')} {t.get('tracking_number')}")
            if ev.get("notes"):
                lines.append(ev["notes"])
        notes = "\n".join(lines) or "Seller response from ChargeGuard."
        return {"method": "provide_supporting_info", "result": provide_supporting_info(dispute_id, notes, files)}
    raise PayPalError(0, {"allowed_actions": actions},
                      f"PayPal does not accept a seller response on this dispute right now. Allowed actions: {actions}")


def sandbox_require_evidence(dispute_id: str, action: str = "SELLER_EVIDENCE") -> dict:
    """Sandbox only: moves a dispute into the state where the seller must send evidence."""
    return post(f"/v1/customer/disputes/{dispute_id}/require-evidence", {"action": action})
