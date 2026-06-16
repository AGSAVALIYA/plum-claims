"""Initial schema — all core tables

Revision ID: 001
Revises:
Create Date: 2026-06-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Members ──────────────────────────────────────────────
    op.create_table(
        "members",
        sa.Column("member_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.Text(), nullable=False),
        sa.Column("relationship", sa.Text(), nullable=False),
        sa.Column("join_date", sa.Date(), nullable=False),
        sa.Column("primary_member_id", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("member_id"),
        sa.CheckConstraint("gender IN ('M','F','O')", name="ck_member_gender"),
        sa.CheckConstraint(
            "relationship IN ('SELF','SPOUSE','CHILD','PARENT')",
            name="ck_member_relationship",
        ),
    )
    op.create_index("idx_members_primary", "members", ["primary_member_id"])
    op.create_index("idx_members_join_date", "members", ["join_date"])

    # ── Member Claims Summary ─────────────────────────────────
    op.create_table(
        "member_claims_summary",
        sa.Column("summary_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("total_claims_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_claims_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("approved_claims_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_claims_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("last_claim_date", sa.Date(), nullable=True),
        sa.Column("primary_member_id", sa.Text(), nullable=True),
        sa.Column("family_approved_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("family_combined_limit", sa.Numeric(12, 2), nullable=True),
        sa.Column("sessions_used_this_year", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("same_day_claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("summary_id"),
        sa.UniqueConstraint("member_id", "year", name="uq_member_summary_year"),
        sa.ForeignKeyConstraint(["member_id"], ["members.member_id"]),
    )
    op.create_index("idx_member_summary_member", "member_claims_summary", ["member_id"])
    op.create_index(
        "idx_member_summary_primary",
        "member_claims_summary",
        ["primary_member_id"],
        postgresql_where=sa.text("primary_member_id IS NOT NULL"),
    )

    # ── Claims ────────────────────────────────────────────────
    op.create_table(
        "claims",
        sa.Column("claim_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Text(), nullable=False),
        sa.Column("policy_id", sa.Text(), nullable=False),
        sa.Column("claim_category", sa.Text(), nullable=False),
        sa.Column("treatment_date", sa.Date(), nullable=False),
        sa.Column("claimed_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("approved_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="SUBMITTED"),
        sa.Column("hospital_name", sa.Text(), nullable=True),
        sa.Column("manual_review_recommended", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("degraded_components", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("processing_trace", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("claim_id"),
        sa.CheckConstraint(
            "claim_category IN ('CONSULTATION','DIAGNOSTIC','PHARMACY','DENTAL','VISION','ALTERNATIVE_MEDICINE')",
            name="ck_claim_category",
        ),
        sa.CheckConstraint(
            "status IN ('SUBMITTED','VALIDATING','PROCESSING','DECIDED','DOCUMENT_ERROR','ERROR','CLOSED')",
            name="ck_claim_status",
        ),
        sa.CheckConstraint(
            "decision IS NULL OR decision IN ('APPROVED','PARTIAL','REJECTED','MANUAL_REVIEW')",
            name="ck_claim_decision",
        ),
        sa.CheckConstraint("claimed_amount > 0", name="ck_claimed_amount_positive"),
        sa.CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_confidence_range",
        ),
    )
    op.create_index("idx_claims_member_id", "claims", ["member_id"])
    op.create_index("idx_claims_policy_id", "claims", ["policy_id"])
    op.create_index("idx_claims_status", "claims", ["status"])
    op.create_index("idx_claims_decision", "claims", ["decision"], postgresql_where=sa.text("decision IS NOT NULL"))
    op.create_index("idx_claims_treatment_date", "claims", ["treatment_date"])
    op.create_index("idx_claims_submitted_at", "claims", ["submitted_at"])
    op.create_index("idx_claims_member_date", "claims", ["member_id", "treatment_date"])

    # ── Claim Documents ──────────────────────────────────────
    op.create_table(
        "claim_documents",
        sa.Column("document_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("claim_id", sa.BigInteger(), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("document_type", sa.Text(), nullable=True),
        sa.Column("detected_type", sa.Text(), nullable=True),
        sa.Column("extraction_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("quality_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("verification_status", sa.Text(), nullable=False, server_default="PENDING"),
        sa.Column("patient_name_on_doc", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("document_id"),
        sa.CheckConstraint(
            "verification_status IN ('PENDING','VERIFIED','WRONG_TYPE','UNREADABLE','PATIENT_MISMATCH','FAILED')",
            name="ck_doc_verification_status",
        ),
        sa.CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="ck_quality_range",
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.claim_id"], ondelete="CASCADE"),
    )
    op.create_index("idx_claim_documents_claim_id", "claim_documents", ["claim_id"])
    op.create_index("idx_claim_documents_status", "claim_documents", ["verification_status"])

    # ── Claim Line Items ─────────────────────────────────────
    op.create_table(
        "claim_line_items",
        sa.Column("line_item_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("claim_id", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("approved_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_covered", sa.Boolean(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("category_match", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("line_item_id"),
        sa.CheckConstraint("amount >= 0", name="ck_line_item_amount_nonnegative"),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.claim_id"], ondelete="CASCADE"),
    )
    op.create_index("idx_claim_line_items_claim_id", "claim_line_items", ["claim_id"])

    # ── Claim Processing Steps ────────────────────────────────
    op.create_table(
        "claim_processing_steps",
        sa.Column("step_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("claim_id", sa.BigInteger(), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("step_name", sa.Text(), nullable=False),
        sa.Column("agent_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("output_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("checks_performed", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("step_id"),
        sa.CheckConstraint(
            "status IN ('STARTED','COMPLETED','FAILED','SKIPPED')",
            name="ck_step_status",
        ),
        sa.UniqueConstraint("claim_id", "step_index", name="uq_claim_step"),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.claim_id"], ondelete="CASCADE"),
    )
    op.create_index("idx_processing_steps_claim_id", "claim_processing_steps", ["claim_id"])
    op.create_index("idx_processing_steps_agent", "claim_processing_steps", ["agent_name"])

    # ── Policies ──────────────────────────────────────────────
    op.create_table(
        "policies",
        sa.Column("policy_id", sa.Text(), nullable=False),
        sa.Column("policy_name", sa.Text(), nullable=False),
        sa.Column("insurer", sa.Text(), nullable=False),
        sa.Column("policy_data", sa.JSON(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("policy_id"),
    )
    op.create_index(
        "idx_policies_active", "policies", ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_table("claim_processing_steps")
    op.drop_table("claim_line_items")
    op.drop_table("claim_documents")
    op.drop_table("claims")
    op.drop_table("member_claims_summary")
    op.drop_table("members")
    op.drop_table("policies")
