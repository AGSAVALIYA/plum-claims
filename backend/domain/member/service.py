"""Domain service for member operations and claims summary management."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.container import get_container
from backend.core.logging import get_logger
from backend.domain.member.models import Member, MemberClaimsSummary

logger = get_logger(__name__)


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash a password with a salt using SHA-256. Returns (hash, salt)."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{hashed}", salt


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    parts = stored_hash.split(":", 1)
    if len(parts) != 2:
        return False
    salt, _ = parts
    computed, _ = _hash_password(password, salt)
    return computed == stored_hash


class MemberService:
    """Handles member lookups, loading from policy file, and claims summary updates."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._policy_data = None

    @property
    def policy_data(self) -> dict:
        if self._policy_data is None:
            self._policy_data = get_container().policy_data
        return self._policy_data

    async def load_members_from_policy(self) -> int:
        """Load all members from the policy file into the database."""
        members_data = self.policy_data.get("members", [])
        count = 0
        for mdata in members_data:
            existing = await self.session.get(Member, mdata["member_id"])
            if existing is None:
                member = Member(
                    member_id=mdata["member_id"],
                    name=mdata["name"],
                    date_of_birth=date.fromisoformat(mdata["date_of_birth"]),
                    gender=mdata["gender"],
                    relationship=mdata["relationship"],
                    join_date=date.fromisoformat(mdata.get("join_date", "2024-04-01")),
                    primary_member_id=mdata.get("primary_member_id"),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                self.session.add(member)
                count += 1
            else:
                # Update join_date if it changed in the policy file
                new_join_date = date.fromisoformat(mdata.get("join_date", "2024-04-01"))
                if existing.join_date != new_join_date:
                    existing.join_date = new_join_date
                    existing.updated_at = datetime.now(UTC)
                    logger.info("member_join_date_updated", member_id=mdata["member_id"], new_join_date=new_join_date.isoformat())
        await self.session.flush()
        logger.info("members_loaded", count=count)
        return count

    async def get_member(self, member_id: str) -> Member | None:
        """Get a member by ID."""
        result = await self.session.execute(select(Member).where(Member.member_id == member_id))
        return result.scalar_one_or_none()

    async def get_primary_member_id(self, member_id: str) -> str:
        """Get the primary (SELF) member ID for a member or dependent."""
        member = await self.get_member(member_id)
        if member is None:
            return member_id
        if member.relationship == "SELF":
            return member.member_id
        return member.primary_member_id or member_id

    async def get_claims_summary(
        self, member_id: str, year: int | None = None
    ) -> MemberClaimsSummary | None:
        """Get the claims summary for a member in a given year."""
        if year is None:
            year = date.today().year
        result = await self.session.execute(
            select(MemberClaimsSummary).where(
                MemberClaimsSummary.member_id == member_id,
                MemberClaimsSummary.year == year,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_summary(self, member_id: str, year: int) -> MemberClaimsSummary:
        """Get existing or create new summary for a member."""
        summary = await self.get_claims_summary(member_id, year)
        if summary is None:
            primary_id = await self.get_primary_member_id(member_id)
            family_limit = Decimal(
                str(
                    self.policy_data.get("coverage", {})
                    .get("family_floater", {})
                    .get("combined_limit", 150000)
                )
            )
            summary = MemberClaimsSummary(
                member_id=member_id,
                year=year,
                total_claims_count=0,
                total_claims_amount=Decimal("0"),
                approved_claims_count=0,
                approved_claims_amount=Decimal("0"),
                primary_member_id=primary_id,
                family_approved_amount=Decimal("0"),
                family_combined_limit=family_limit,
                sessions_used_this_year=0,
                same_day_claim_count=0,
                updated_at=datetime.now(UTC),
            )
            self.session.add(summary)
            await self.session.flush()
        return summary

    async def get_family_total(self, primary_member_id: str, year: int) -> Decimal:
        """Get total approved amount across a family (primary + dependents)."""
        result = await self.session.execute(
            select(MemberClaimsSummary).where(
                MemberClaimsSummary.primary_member_id == primary_member_id,
                MemberClaimsSummary.year == year,
            )
        )
        summaries = result.scalars().all()
        return sum((s.approved_claims_amount for s in summaries), Decimal("0"))

    async def update_on_claim_decision(
        self,
        member_id: str,
        approved_amount: Decimal,
        treatment_date: date,
        claim_category: str,
        sessions_count: int = 0,
    ) -> None:
        """Update member claims summary after a claim decision."""
        year = treatment_date.year
        summary = await self.get_or_create_summary(member_id, year)

        summary.total_claims_count += 1
        summary.total_claims_amount += approved_amount
        if approved_amount > 0:
            summary.approved_claims_count += 1
            summary.approved_claims_amount += approved_amount
        if summary.last_claim_date is None or treatment_date > summary.last_claim_date:
            summary.last_claim_date = treatment_date

        # Track same-day claims (check if same as last claim date for simplicity)
        if summary.last_claim_date == treatment_date:
            summary.same_day_claim_count += 1
        else:
            summary.same_day_claim_count = 1

        # Sessions for alternative medicine
        if claim_category == "ALTERNATIVE_MEDICINE":
            summary.sessions_used_this_year += sessions_count

        # Family floater update
        primary_id = await self.get_primary_member_id(member_id)
        if primary_id != member_id:
            # Dependent — update family total on primary member's summary
            primary_summary = await self.get_or_create_summary(primary_id, year)
            family_total = await self.get_family_total(primary_id, year)
            primary_summary.family_approved_amount = family_total
            # Also update family on this dependent's record
            summary.family_approved_amount = family_total

        summary.updated_at = datetime.now(UTC)
        await self.session.flush()
        logger.info(
            "member_summary_updated",
            member_id=member_id,
            approved_amount=str(approved_amount),
            ytd_approved=str(summary.approved_claims_amount),
        )

    async def register_member(self, member_id: str, password: str) -> Member | None:
        """Register a member with a password. Returns None if member doesn't exist."""
        member = await self.get_member(member_id)
        if member is None:
            return None
        if member.password_hash:
            return member  # Already registered
        hashed, _ = _hash_password(password)
        member.password_hash = hashed
        member.updated_at = datetime.now(UTC)
        await self.session.flush()
        logger.info("member_registered", member_id=member_id)
        return member

    async def set_password(self, member_id: str, password: str) -> bool:
        """Set/reset password for a member."""
        member = await self.get_member(member_id)
        if member is None:
            return False
        hashed, _ = _hash_password(password)
        member.password_hash = hashed
        member.updated_at = datetime.now(UTC)
        await self.session.flush()
        return True

    async def authenticate(self, member_id: str, password: str) -> Member | None:
        """Authenticate a member. Returns Member if valid, None otherwise."""
        member = await self.get_member(member_id)
        if member is None or member.password_hash is None:
            return None
        if _verify_password(password, member.password_hash):
            return member
        return None
