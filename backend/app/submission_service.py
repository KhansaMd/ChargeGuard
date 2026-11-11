
from datetime import datetime, timezone
import hashlib
import json

from sqlmodel import Session, select

from app import paypal_service
from app.audit import log
from app.evidence_service import check_evidence
from app.models import Dispute, Evidence, Report


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _evidence_fingerprint(session: Session, dispute_id: str) -> str:
    """Create a consistent fingerprint of all evidence for a dispute."""

    rows = session.exec(
        select(Evidence).where(Evidence.dispute_id == dispute_id)
    ).all()

    evidence_data = [
        {
            "id": row.id,
            "type": row.type,
            "source": row.source,
            "value": row.value,
        }
        for row in rows
    ]

    evidence_data.sort(key=lambda item: item["id"])

    serialized = json.dumps(
        evidence_data,
        sort_keys=True,
        ensure_ascii=False,
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _get_report(
    session: Session,
    dispute_id: str,
    report_id: int | None = None,
) -> Report:
    if report_id is not None:
        report = session.get(Report, report_id)
    else:
        report = session.exec(
            select(Report)
            .where(Report.dispute_id == dispute_id)
            .order_by(Report.id.desc())
        ).first()

    if not report or report.dispute_id != dispute_id:
        raise ValueError("Report not found for this dispute.")

    return report


def _validate_report(session: Session, report: Report) -> None:
    """Validate report verification and evidence references."""

    data = report.data or {}

    if not report.verified:
        raise ValueError(
            "Only a verified report can be approved or submitted."
        )

    if data.get("invalid_source_ids"):
        raise ValueError(
            "The report contains invalid evidence references. "
            "Investigate the dispute again before approval."
        )

    evidence_rows = session.exec(
        select(Evidence).where(Evidence.dispute_id == report.dispute_id)
    ).all()

    # Check the reliability of required evidence.
    checklist = check_evidence(session, report.dispute_id)

    blocked_evidence = [
        item
        for item in checklist["checklist"]
        if item["status"] in ("unreliable", "contradictory")
    ]

    if blocked_evidence:
        blocked_types = [
            f"{item['type']} ({item['status']})"
            for item in blocked_evidence
        ]

        raise ValueError(
            "Approval blocked because required evidence is unreliable "
            "or contradictory: " + ", ".join(blocked_types)
        )

    valid_ids = {e.id for e in evidence_rows}
    findings = data.get("findings", [])

    if not findings:
        raise ValueError("The report has no findings to validate.")

    for index, finding in enumerate(findings, start=1):
        source_ids = finding.get("source_ids", [])

        if not source_ids:
            raise ValueError(
                f"Finding {index} has no supporting evidence. "
                "Investigate again before approval."
            )

        invalid = [
            source_id
            for source_id in source_ids
            if source_id not in valid_ids
        ]

        if invalid:
            raise ValueError(
                f"Finding {index} references evidence that does not exist: "
                f"{invalid}"
            )

    report_source_ids = data.get("source_ids", [])

    invalid_report_ids = [
        source_id
        for source_id in report_source_ids
        if source_id not in valid_ids
    ]

    if invalid_report_ids:
        raise ValueError(
            "Report contains invalid evidence references: "
            f"{invalid_report_ids}"
        )


def approve(
    session: Session,
    dispute_id: str,
    report_id: int,
    approved_by: str = "merchant",
    edited_draft: str | None = None,
) -> Report:
    """Save the merchant's edited response and explicit approval."""

    report = _get_report(session, dispute_id, report_id)
    data = dict(report.data or {})

    if data.get("submission"):
        raise ValueError("This report has already been submitted to PayPal.")

    _validate_report(session, report)

    draft = (
        edited_draft
        if edited_draft is not None
        else data.get("response_draft", "")
    )
    draft = draft.strip()

    if not draft:
        raise ValueError("The response draft cannot be empty.")

    data["response_draft"] = draft
    data["approval"] = {
        "approved": True,
        "approved_by": approved_by.strip() or "merchant",
        "approved_at": _now(),
        "evidence_fingerprint": _evidence_fingerprint(
            session,
            dispute_id,
        ),
    }

    report.data = data
    report.approved = True

    session.add(report)
    session.commit()
    session.refresh(report)

    log(
        session,
        "approve_report",
        dispute_id,
        report_id=report.id,
        approved_by=approved_by,
    )
    session.commit()

    return report


def _build_evidence_payload(
    session: Session,
    dispute: Dispute,
    draft: str,
) -> list[dict]:
    """Build a PayPal evidence entry using the requested evidence type."""

    raw = dispute.raw or {}
    requested_types = []

    for item in raw.get("evidences", []):
        if item.get("source") == "REQUESTED_FROM_SELLER":
            evidence_type = item.get("evidence_type")

            if evidence_type:
                requested_types.append(evidence_type)

    evidence_type = requested_types[0] if requested_types else "OTHER"

    payload = {
        "evidence_type": evidence_type,
        "notes": draft[:2000],
    }

    if evidence_type == "PROOF_OF_FULFILLMENT":
        rows = session.exec(
            select(Evidence).where(Evidence.dispute_id == dispute.id)
        ).all()

        values = {row.type.lower(): row.value for row in rows}

        tracking_number = (values.get("tracking_number") or "").strip()
        carrier = (values.get("carrier") or "").strip()

        if not tracking_number or not carrier:
            raise ValueError(
                "Submission blocked: proof of fulfilment requires "
                "both a tracking number and a carrier."
            )

        payload["evidence_info"] = {
            "tracking_info": [
                {
                    "carrier_name": carrier,
                    "tracking_number": tracking_number,
                }
            ]
        }

    return [payload]


def submit(session: Session, dispute_id: str) -> dict:
    """Submit an approved merchant response to PayPal."""

    dispute = session.get(Dispute, dispute_id)

    if not dispute:
        raise ValueError("Dispute not found.")

    report = _get_report(session, dispute_id)
    data = dict(report.data or {})

    if not report.approved or not data.get("approval", {}).get("approved"):
        raise PermissionError(
            "Merchant approval is required before PayPal submission."
        )

    if data.get("submission"):
        raise PermissionError("This report has already been submitted.")

    # Revalidate the report immediately before submission.
    _validate_report(session, report)

    approved_fingerprint = data.get("approval", {}).get(
        "evidence_fingerprint"
    )
    current_fingerprint = _evidence_fingerprint(
        session,
        dispute_id,
    )

    if not approved_fingerprint:
        raise PermissionError(
            "Submission blocked: this approval has no evidence snapshot. "
            "Please review the report and approve it again."
        )

    if approved_fingerprint != current_fingerprint:
        raise PermissionError(
            "Submission blocked: evidence has changed since approval. "
            "Please review the updated evidence and approve again."
        )

    draft = (data.get("response_draft") or "").strip()

    if not draft:
        raise ValueError("There is no approved response draft to submit.")

    # Check PayPal's current dispute actions before submitting.
    paypal_dispute = paypal_service.get_dispute(dispute_id)
    actions = paypal_service.allowed_actions(paypal_dispute)

    if "provide_supporting_info" in actions:
        result = paypal_service.provide_supporting_info(
            dispute_id,
            draft,
        )
        method = "provide_supporting_info"

    elif "provide_evidence" in actions:
        evidences = _build_evidence_payload(
            session,
            dispute,
            draft,
        )

        result = paypal_service.provide_evidence(
            dispute_id,
            evidences,
        )
        method = "provide_evidence"

    else:
        raise RuntimeError(
            "PayPal does not currently allow evidence submission. "
            f"Available actions: {actions}"
        )

    data["submission"] = {
        "submitted": True,
        "method": method,
        "submitted_at": _now(),
        "paypal_response": result,
    }

    report.data = data
    session.add(report)
    session.commit()
    session.refresh(report)

    log(
        session,
        "submit_to_paypal",
        dispute_id,
        report_id=report.id,
        method=method,
    )
    session.commit()

    return {
        "method": method,
        "result": result,
    }
