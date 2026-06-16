#!/usr/bin/env python3
"""Seed the database with initial policy data and member roster.

Usage:
    uv run python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path so 'backend' package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.config import settings
from backend.core.logging import setup_logging, get_logger
from backend.providers.db.session import DatabaseSession

logger = get_logger(__name__)

# Default passwords for all members (member_id → password)
DEFAULT_PASSWORDS = {
    "EMP001": "pass001",
    "EMP002": "pass002",
    "EMP003": "pass003",
    "EMP004": "pass004",
    "EMP005": "pass005",
    "EMP006": "pass006",
    "EMP007": "pass007",
    "EMP008": "pass008",
    "EMP009": "pass009",
    "EMP010": "pass010",
    "DEP001": "pass001",
    "DEP002": "pass002",
}

# Admin accounts to seed
ADMIN_ACCOUNTS = {
    "ADMIN001": {"password": "admin123", "name": "System Admin"},
}


async def seed() -> None:
    """Seed the database with initial data."""
    setup_logging()
    logger.info("seeding_started")

    db = DatabaseSession(settings.database_url)
    await db.create_all()

    async with db.session_factory() as session:
        # Load members from policy file
        from backend.domain.member.service import MemberService
        member_service = MemberService(session)
        count = await member_service.load_members_from_policy()
        logger.info("members_loaded", count=count)

        # Set default passwords for all members
        for member_id, password in DEFAULT_PASSWORDS.items():
            await member_service.set_password(member_id, password)
        logger.info("passwords_set", count=len(DEFAULT_PASSWORDS))

        # Create admin accounts
        from datetime import UTC, date, datetime as dt
        from backend.domain.member.models import Member

        for admin_id, admin_info in ADMIN_ACCOUNTS.items():
            existing = await session.get(Member, admin_id)
            if existing is None:
                admin_member = Member(
                    member_id=admin_id,
                    name=admin_info["name"],
                    date_of_birth=date(1990, 1, 1),
                    gender="O",
                    relationship="SELF",
                    join_date=date(2024, 1, 1),
                    role="admin",
                    created_at=dt.now(UTC),
                    updated_at=dt.now(UTC),
                )
                session.add(admin_member)
                await session.flush()
                logger.info("admin_created", member_id=admin_id)

            await member_service.set_password(admin_id, admin_info["password"])
            # Set role to admin for existing or new members
            member = await session.get(Member, admin_id)
            if member:
                member.role = "admin"
                member.updated_at = dt.now(UTC)

        await session.commit()

    await db.close()
    logger.info("seeding_complete")


if __name__ == "__main__":
    asyncio.run(seed())
