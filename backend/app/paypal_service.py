import json
import time

import httpx

from app.config import settings

_token = {"value": None, "expires_at": 0.0}


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
    r.raise_for_status()
    data = r.json()
    _token["value"] = data["access_token"]
    _token["expires_at"] = time.time() + data["expires_in"]
    return _token["value"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}


def _check(r: httpx.Response) -> dict:
    if r.status_code >= 400:
        raise RuntimeError(f"PayPal {r.status_code}: {r.text}")
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
            "return_url": "https://example.com/return",
            "cancel_url": "https://example.com/cancel",
            "user_action": "PAY_NOW",
        }}},
    })


def capture_order(order_id: str) -> dict:
    return post(f"/v2/checkout/orders/{order_id}/capture")


def get_order(order_id: str) -> dict:
    return get(f"/v2/checkout/orders/{order_id}")


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


def sandbox_require_evidence(dispute_id: str, action: str = "SELLER_EVIDENCE") -> dict:
    """Sandbox only: moves a dispute into the state where the seller must send evidence."""
    return post(f"/v1/customer/disputes/{dispute_id}/require-evidence", {"action": action})
