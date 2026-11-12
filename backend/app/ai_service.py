
import json

from anthropic import Anthropic
from sqlmodel import Session

from app.audit import log
from app.config import settings
from app.evidence_service import check_evidence
from app.models import Report


# Connect to Claude using the API key in .env
client = Anthropic(
    api_key=settings.anthropic_api_key
)


SYSTEM = """
You are ChargeGuard, an AI-powered PayPal dispute investigation assistant.

Your responsibility is to investigate payment disputes using only
the evidence records provided to you.

STRICT RULES:

1. Use only the evidence records provided.
   Never invent facts, dates, tracking numbers, or documents.

2. Generate factual findings from the available evidence.
   Do not return an empty findings array when the evidence
   contains usable factual records.

   Every finding must include at least one valid evidence ID
   that directly supports it in source_ids.

   Describe what the records actually show, using careful
   wording such as "The payment record shows" or
   "The PayPal order lists".

   Never treat demo, sample, test, or placeholder records
   as genuine proof.

   Do not put claims about absent evidence in findings.
   Put all missing or unavailable evidence in
   missing_information instead.


3. List all missing information in missing_information.

4. Identify conflicting evidence in contradictions.
   Do not describe uncertainty or missing evidence as a proven
   contradiction.

5. Never promise that the merchant will win the dispute.
   If evidence is weak or incomplete, explain this in
   recommended_action.

6. Always generate a complete, non-empty, case-specific response_draft.

   The draft must:
   - Address the actual dispute reason.
   - Refer to relevant evidence provided in the investigation.
   - Clearly disclose missing, weak, or unverified evidence.
   - Never claim delivery or payment settlement unless verified.
   - Use a professional and respectful tone.
   - Avoid inventing facts or making unsupported claims.
   - Be suitable for merchant review and editing before submission.

7. Never create fake evidence IDs or reference evidence
   that was not provided.

8. Be transparent about uncertainty.
   If something cannot be verified, say so.
"""


REPORT_TOOL = {
    "name": "submit_report",
    "description": (
        "Submit the completed PayPal dispute investigation report, "
        "including a case-specific response draft."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "case_summary": {
                "type": "string"
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "statement": {
                            "type": "string"
                        },
                        "source_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": [
                        "statement",
                        "source_ids"
                    ],
                    "additionalProperties": False
                }
            },
            "available_evidence": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "missing_information": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "contradictions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "issue": {
                            "type": "string"
                        },
                        "evidence_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": [
                        "issue",
                        "evidence_ids"
                    ],
                    "additionalProperties": False
                }
            },
            "recommended_action": {
                "type": "string"
            },
            "response_draft": {
                "type": "string",
                "description": (
                    "A complete, non-empty, case-specific response "
                    "to the PayPal dispute. Address the dispute "
                    "reason, reference relevant provided evidence, "
                    "disclose missing or unverified proof, and "
                    "avoid unsupported claims. Use a professional "
                    "tone suitable for merchant review."
                )
            },
            "source_ids": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": [
            "case_summary",
            "findings",
            "available_evidence",
            "missing_information",
            "contradictions",
            "recommended_action",
            "response_draft",
            "source_ids"
        ],
        "additionalProperties": False
    }
}


def verify(data: dict, valid_ids: set[str]) -> tuple[dict, bool]:
    """
    Verify Claude's findings reference real evidence IDs.
    Findings without evidence references remain unverified.
    """

    findings = data.get("findings", [])

    if not isinstance(findings, list):
        findings = []

    # Normalize findings so strings cannot crash verification.
    normalized_findings = []

    for finding in findings:
        if isinstance(finding, str):
            finding = {
                "statement": finding,
                "source_ids": [],
            }

        elif not isinstance(finding, dict):
            continue

        source_ids = finding.get("source_ids", [])

        if not isinstance(source_ids, list):
            source_ids = []

        source_ids = [
            evidence_id
            for evidence_id in source_ids
            if isinstance(evidence_id, str)
        ]

        finding["source_ids"] = source_ids
        normalized_findings.append(finding)

    data["findings"] = normalized_findings

    all_verified = bool(normalized_findings)
    invalid_ids = []

    for finding in normalized_findings:
        source_ids = finding["source_ids"]

        valid_sources = [
            evidence_id
            for evidence_id in source_ids
            if evidence_id in valid_ids
        ]

        invalid_sources = [
            evidence_id
            for evidence_id in source_ids
            if evidence_id not in valid_ids
        ]

        finding["verified"] = (
            bool(source_ids)
            and len(valid_sources) == len(source_ids)
        )

        if not finding["verified"]:
            all_verified = False

        invalid_ids.extend(invalid_sources)

    report_source_ids = data.get("source_ids", [])

    if not isinstance(report_source_ids, list):
        report_source_ids = []

    report_source_ids = [
        evidence_id
        for evidence_id in report_source_ids
        if isinstance(evidence_id, str)
    ]

    invalid_report_ids = [
        evidence_id
        for evidence_id in report_source_ids
        if evidence_id not in valid_ids
    ]

    invalid_ids.extend(invalid_report_ids)

    finding_source_ids = [
        evidence_id
        for finding in normalized_findings
        for evidence_id in finding["source_ids"]
    ]

    combined_source_ids = list(dict.fromkeys(
        report_source_ids + finding_source_ids
    ))

    data["source_ids"] = [
        evidence_id
        for evidence_id in combined_source_ids
        if evidence_id in valid_ids
    ]

    data["invalid_source_ids"] = list(set(invalid_ids))

    if invalid_ids:
        all_verified = False

    return data, all_verified


def investigate(session: Session, dispute_id: str) -> Report:
    """
    Investigate a PayPal dispute using Claude and available evidence.
    """

    # Step 1: Collect evidence for the dispute.
    facts = check_evidence(session, dispute_id)

    # Step 2: Identify valid evidence IDs.
    valid_ids = {
        evidence["id"]
        for evidence in facts.get("evidence", [])
    }

    # Step 3: Send evidence to Claude for investigation.
    response = client.messages.create(
        model=settings.ai_model,
        max_tokens=3000,
        system=SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    "Investigate this PayPal dispute using only "
                    "the following evidence. Complete every "
                    "required report field, especially response_draft.\n\n"
                    + json.dumps(facts, indent=2)
                )
            }
        ],
        tools=[REPORT_TOOL],
        tool_choice={
            "type": "tool",
            "name": "submit_report"
        }
    )

    # Step 4: Extract Claude's investigation report.
    tool_result = next(
        (
            block
            for block in response.content
            if block.type == "tool_use"
            and block.name == "submit_report"
        ),
        None
    )

    if tool_result is None:
        raise ValueError(
            "Claude did not return an investigation report."
        )

    data = dict(tool_result.input)

    # Step 5: Ensure a response draft is available.
    if not data.get("response_draft"):

        summary = data.get(
            "case_summary",
            "We reviewed the evidence currently available."
        )

        missing = data.get("missing_information", [])

        missing_text = (
            "\n\nThe following information is still missing "
            "or requires verification:\n- "
            + "\n- ".join(missing)
            if missing
            else ""
        )

        recommendation = data.get("recommended_action", "")

        recommendation_text = (
            "\n\nOur recommended next step is: "
            + recommendation
            if recommendation
            else ""
        )

        data["response_draft"] = (
            f"Dear PayPal Disputes Team,\n\n"
            f"We are responding to dispute {dispute_id}. "
            f"{summary}"
            f"{missing_text}"
            f"{recommendation_text}\n\n"
            "We respectfully request that the available "
            "information be considered during the review. "
            "We will provide additional supporting documentation "
            "where it becomes available.\n\n"
            "Kind regards,\n"
            "Merchant"
        )

    # Step 6: Verify Claude's evidence references.
    data, verified = verify(data, valid_ids)

    # Step 7: Save the investigation report.
    report = Report(
        dispute_id=dispute_id,
        data=data,
        verified=verified
    )

    session.add(report)
    session.commit()
    session.refresh(report)

    # Step 8: Record the investigation in the audit log.
    log(
        session,
        "investigate",
        dispute_id,
        report_id=report.id,
        verified=verified,
        model=settings.ai_model
    )

    return report
