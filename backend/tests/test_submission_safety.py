
from copy import deepcopy

import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.models import Dispute, Evidence, Report
from app import submission_service
from app.ai_service import verify


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as test_session:
        yield test_session

    SQLModel.metadata.drop_all(engine)
    engine.dispose()


def create_test_data(session, verified=True, invalid_source_ids=None):
    dispute_id = "TEST-DISPUTE-001"
    evidence_id = "TEST-EVIDENCE-001"

    dispute = Dispute(
        id=dispute_id,
        status="UNDER_REVIEW",
        reason="MERCHANDISE_OR_SERVICE_NOT_RECEIVED",
    )

    evidence = Evidence(
        id=evidence_id,
        dispute_id=dispute_id,
        type="tracking_number",
        source="merchant_upload",
        value="TEST123456",
    )

    report = Report(
        dispute_id=dispute_id,
        verified=verified,
        data={
            "findings": [
                {
                    "statement": "Test finding supported by evidence.",
                    "source_ids": [evidence_id],
                }
            ],
            "source_ids": [evidence_id],
            "invalid_source_ids": invalid_source_ids or [],
            "response_draft": "Test response draft.",
        },
    )

    session.add(dispute)
    session.add(evidence)
    session.add(report)
    session.commit()
    session.refresh(report)

    return dispute_id, report


def test_unverified_report_cannot_be_approved(session):
    dispute_id, report = create_test_data(session, verified=False)

    with pytest.raises(ValueError, match="Only a verified report"):
        submission_service.approve(session, dispute_id, report.id)


def test_invalid_evidence_references_block_approval(session):
    dispute_id, report = create_test_data(
        session,
        verified=True,
        invalid_source_ids=["INVALID-EVIDENCE-ID"],
    )

    with pytest.raises(ValueError, match="invalid evidence references"):
        submission_service.approve(session, dispute_id, report.id)


def test_valid_report_can_be_approved(session):
    dispute_id, report = create_test_data(session)

    approved_report = submission_service.approve(
        session,
        dispute_id,
        report.id,
        approved_by="test-merchant",
        edited_draft="Approved test response.",
    )

    assert approved_report.verified is True
    assert approved_report.approved is True
    assert approved_report.data["approval"]["approved"] is True
    assert approved_report.data["response_draft"] == "Approved test response."


def test_unapproved_report_cannot_be_submitted(session, monkeypatch):
    dispute_id, report = create_test_data(session)

    def unexpected_paypal_call(*args, **kwargs):
        pytest.fail("PayPal must not be called before merchant approval.")

    monkeypatch.setattr(
        submission_service.paypal_service,
        "get_dispute",
        unexpected_paypal_call,
    )

    with pytest.raises(PermissionError, match="Merchant approval is required"):
        submission_service.submit(session, dispute_id)


def test_approved_report_uses_mocked_paypal_submission(session, monkeypatch):
    dispute_id, report = create_test_data(session)

    submission_service.approve(
        session,
        dispute_id,
        report.id,
        edited_draft="Approved test response.",
    )

    monkeypatch.setattr(
        submission_service.paypal_service,
        "get_dispute",
        lambda dispute_id: {"status": "UNDER_REVIEW"},
    )

    monkeypatch.setattr(
        submission_service.paypal_service,
        "allowed_actions",
        lambda dispute: ["provide_supporting_info"],
    )

    monkeypatch.setattr(
        submission_service.paypal_service,
        "provide_supporting_info",
        lambda dispute_id, notes: {"status": "MOCK_ACCEPTED"},
    )

    result = submission_service.submit(session, dispute_id)

    assert result["method"] == "provide_supporting_info"
    assert result["result"]["status"] == "MOCK_ACCEPTED"

    session.refresh(report)
    assert report.data["submission"]["submitted"] is True
    assert (
        report.data["submission"]["paypal_response"]["status"]
        == "MOCK_ACCEPTED"
    )


def test_finding_without_evidence_is_rejected(session):
    dispute_id, report = create_test_data(session)

    data = deepcopy(report.data)
    data["findings"][0]["source_ids"] = []
    report.data = data
    session.add(report)
    session.commit()

    with pytest.raises(ValueError, match="no supporting evidence"):
        submission_service.approve(session, dispute_id, report.id)


def test_already_submitted_report_cannot_be_submitted_again(session):
    dispute_id, report = create_test_data(session)

    data = deepcopy(report.data)
    data["approval"] = {"approved": True}
    data["submission"] = {"submitted": True}
    report.data = data
    report.approved = True
    session.add(report)
    session.commit()

    with pytest.raises(PermissionError, match="already been submitted"):
        submission_service.submit(session, dispute_id)


def test_submission_blocked_when_paypal_action_unavailable(
    session, monkeypatch
):
    dispute_id, report = create_test_data(session)

    submission_service.approve(
        session,
        dispute_id,
        report.id,
        edited_draft="Approved test response.",
    )

    monkeypatch.setattr(
        submission_service.paypal_service,
        "get_dispute",
        lambda dispute_id: {"status": "UNDER_REVIEW"},
    )

    monkeypatch.setattr(
        submission_service.paypal_service,
        "allowed_actions",
        lambda dispute: [],
    )

    def unexpected_submission(*args, **kwargs):
        pytest.fail(
            "PayPal submission must not happen without an allowed action."
        )

    monkeypatch.setattr(
        submission_service.paypal_service,
        "provide_supporting_info",
        unexpected_submission,
    )
    monkeypatch.setattr(
        submission_service.paypal_service,
        "provide_evidence",
        unexpected_submission,
    )

    with pytest.raises(RuntimeError, match="does not currently allow"):
        submission_service.submit(session, dispute_id)


def test_unreliable_required_evidence_blocks_approval(session):
    dispute_id, report = create_test_data(session)

    evidence = session.get(Evidence, "TEST-EVIDENCE-001")
    evidence.value = "placeholder tracking number"
    session.add(evidence)
    session.commit()

    with pytest.raises(ValueError, match="unreliable"):
        submission_service.approve(session, dispute_id, report.id)


def test_contradictory_required_evidence_blocks_approval(session):
    dispute_id, report = create_test_data(session)

    session.add(
        Evidence(
            id="SHIPPING-001",
            dispute_id=dispute_id,
            type="shipping_address",
            source="merchant_upload",
            value="123 Main Street",
        )
    )

    session.add(
        Evidence(
            id="DELIVERY-001",
            dispute_id=dispute_id,
            type="delivery_address",
            source="carrier_record",
            value="456 Different Street",
        )
    )
    session.commit()

    with pytest.raises(ValueError, match="contradictory"):
        submission_service.approve(session, dispute_id, report.id)


def test_report_with_no_findings_is_not_verified():
    data = {
        "findings": [],
        "source_ids": [],
    }

    verified_data, all_verified = verify(data, set())

    assert verified_data["findings"] == []
    assert all_verified is False
@pytest.mark.parametrize("missing_type", ["tracking_number", "carrier"])
def test_proof_of_fulfillment_requires_tracking_details(
    session, missing_type
):
    dispute_id, report = create_test_data(session)
    dispute = session.get(Dispute, dispute_id)

    if missing_type == "tracking_number":
        tracking = session.get(Evidence, "TEST-EVIDENCE-001")
        tracking.value = ""
        session.add(tracking)

        session.add(
            Evidence(
                id="TEST-CARRIER-001",
                dispute_id=dispute_id,
                type="carrier",
                source="merchant_upload",
                value="Test Carrier",
            )
        )
    else:
        # The test data already has a tracking number,
        # but no carrier.
        pass

    session.commit()

    dispute.raw = {
        "evidences": [
            {
                "source": "REQUESTED_FROM_SELLER",
                "evidence_type": "PROOF_OF_FULFILLMENT",
            }
        ]
    }

    with pytest.raises(ValueError, match="tracking number and a carrier"):
        submission_service._build_evidence_payload(
            session,
            dispute,
            "Test response draft.",
        )
def test_changed_evidence_blocks_submission(session, monkeypatch):
    dispute_id, report = create_test_data(session)

    # Merchant approves the report using the original evidence.
    submission_service.approve(
        session,
        dispute_id,
        report.id,
        edited_draft="Approved test response.",
    )

    # Change the evidence after approval.
    evidence = session.get(Evidence, "TEST-EVIDENCE-001")
    evidence.value = "CHANGED-TRACKING-999"
    session.add(evidence)
    session.commit()

    # PayPal must never be contacted.
    def unexpected_paypal_call(*args, **kwargs):
        pytest.fail(
            "PayPal must not be contacted when evidence changes after approval."
        )

    monkeypatch.setattr(
        submission_service.paypal_service,
        "get_dispute",
        unexpected_paypal_call,
    )

    with pytest.raises(
        PermissionError,
        match="evidence has changed since approval",
    ):
        submission_service.submit(session, dispute_id)