from sqlmodel import Session

from app.models import AuditLog


def log(session: Session, action: str, dispute_id: str | None = None, **detail) -> None:
    session.add(AuditLog(action=action, dispute_id=dispute_id, detail=detail))
    session.commit()