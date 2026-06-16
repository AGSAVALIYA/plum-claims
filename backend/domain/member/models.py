"""SQLAlchemy models for the Member bounded context."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.providers.db.session import Base


class Member(Base):
    """Member (employee or dependent) table."""

    __tablename__ = "members"

    member_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(Text, nullable=False)
    relationship: Mapped[str] = mapped_column(Text, nullable=False)
    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    primary_member_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("gender IN ('M','F','O')", name="ck_member_gender"),
        CheckConstraint(
            "relationship IN ('SELF','SPOUSE','CHILD','PARENT')",
            name="ck_member_relationship",
        ),
        CheckConstraint(
            "role IN ('member','admin','reviewer')",
            name="ck_member_role",
        ),
        Index("idx_members_primary", "primary_member_id"),
    )


class MemberClaimsSummary(Base):
    """Materialized view of member claims aggregation for fast policy checks."""

    __tablename__ = "member_claims_summary"

    summary_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    member_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_claims_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_claims_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    approved_claims_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_claims_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    last_claim_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    primary_member_id: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    family_approved_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    family_combined_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    sessions_used_this_year: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    same_day_claim_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("member_id", "year", name="uq_member_summary_year"),)
