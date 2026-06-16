"""Add claim_events, claim_retry_attempts tables and role column to members

Revision ID: 003
Revises: 002
Create Date: 2026-06-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column to members
    op.add_column("members", sa.Column("role", sa.Text(), nullable=False, server_default="member"))
    op.create_check_constraint("ck_member_role", "members", "role IN ('member','admin','reviewer')")

    # Create claim_events table
    op.create_table(
        "claim_events",
        sa.Column("event_id", sa.BigInteger(), sa.Identity(always=False), autoincrement=True, nullable=False),
        sa.Column("claim_id", sa.BigInteger(), sa.ForeignKey("claims.claim_id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("previous_status", sa.Text(), nullable=True),
        sa.Column("new_status", sa.Text(), nullable=True),
        sa.Column("actor_type", sa.Text(), nullable=False, server_default="SYSTEM"),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
        sa.CheckConstraint(
            "event_type IN ('SUBMITTED','PROCESSING_STARTED','STEP_COMPLETED','STEP_FAILED',"
            "'RETRY_REQUESTED','RETRY_STARTED','DECISION_MADE','ADMIN_OVERRIDE','COMMENT_ADDED')",
            name="ck_event_type",
        ),
        sa.CheckConstraint(
            "actor_type IN ('USER','SYSTEM','ADMIN')",
            name="ck_actor_type",
        ),
    )
    op.create_index("ix_claim_events_claim_id", "claim_events", ["claim_id"])

    # Create claim_retry_attempts table
    op.create_table(
        "claim_retry_attempts",
        sa.Column("retry_id", sa.BigInteger(), sa.Identity(always=False), autoincrement=True, nullable=False),
        sa.Column("claim_id", sa.BigInteger(), sa.ForeignKey("claims.claim_id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("retry_reason", sa.Text(), nullable=True),
        sa.Column("failed_step_index", sa.Integer(), nullable=True),
        sa.Column("new_documents", sa.JSON(), nullable=True),
        sa.Column("requested_by", sa.Text(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_status", sa.Text(), nullable=False, server_default="PENDING"),
        sa.PrimaryKeyConstraint("retry_id"),
        sa.CheckConstraint(
            "result_status IN ('PENDING','PROCESSING','SUCCEEDED','FAILED')",
            name="ck_retry_result_status",
        ),
    )
    op.create_index("ix_claim_retry_attempts_claim_id", "claim_retry_attempts", ["claim_id"])


def downgrade() -> None:
    op.drop_table("claim_retry_attempts")
    op.drop_table("claim_events")
    op.drop_constraint("ck_member_role", "members", type_="check")
    op.drop_column("members", "role")
