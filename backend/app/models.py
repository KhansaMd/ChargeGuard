from datetime import datetime, timezone

from sqlmodel import JSON, Column, Field, SQLModel


def now() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(SQLModel, table=True):
    id: str = Field(primary_key=True)  # PayPal capture ID
    order_id: str | None = None
    amount: str | None = None
    currency: str | None = None
    payer_email: str | None = None
    shipping_address: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: str | None = None
    is_synthetic: bool = False  # True for labelled demo data


class Dispute(SQLModel, table=True):
    id: str = Field(primary_key=True)  # PayPal dispute ID
    transaction_id: str | None = Field(default=None, index=True)
    reason: str | None = None
    status: str | None = None
    stage: str | None = None
    amount: str | None = None
    currency: str | None = None
    due_date: str | None = None
    created_at: str | None = None
    raw: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Evidence(SQLModel, table=True):
    id: str = Field(primary_key=True)  # e.g. ev_PP-D-123_tracking_number
    dispute_id: str = Field(index=True)
    type: str  # tracking_number, shipping_address, delivery_confirmation...
    source: str  # paypal_dispute, paypal_capture, paypal_order, merchant_upload
    value: str


class Report(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dispute_id: str = Field(index=True)
    data: dict = Field(default_factory=dict, sa_column=Column(JSON))
    verified: bool = False
    approved: bool = False
    created_at: datetime = Field(default_factory=now)


class AuditLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dispute_id: str | None = Field(default=None, index=True)
    action: str
    detail: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now)
