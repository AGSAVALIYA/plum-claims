"""Test fixtures and configuration for pytest."""

import json
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.providers.db.session import Base

# ── Force mock LLM for all tests ──────────────────────────────
# Override the settings-based LLM provider to avoid rate limits.
from backend.core.config import settings
settings.llm_provider = "mock"

# ── Test Database ──────────────────────────────────────────


@pytest.fixture(scope="session")
def test_db_url():
    """Use SQLite for tests — no external dependencies needed."""
    return "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db_url):
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_async_engine(test_db_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ── Policy Fixture ─────────────────────────────────────────


@pytest.fixture(scope="session")
def policy_data():
    """Load policy terms from the test file."""
    path = Path(__file__).parent.parent.parent / "assignment" / "policy_terms.json"
    with open(path) as f:
        return json.load(f)


# ── Test Helpers ───────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_container():
    """Reset the DI container before each test so mock LLM provider is used."""
    from backend.core.container import get_container
    container = get_container()
    container._llm = None
    container._llm_raw = None
    container._cache = None
    container._policy_data = None


@pytest.fixture
def sample_documents_consultation():
    """Valid consultation claim documents."""
    return [
        {
            "file_id": "F007",
            "file_name": "prescription.jpg",
            "actual_type": "PRESCRIPTION",
            "quality": "GOOD",
            "patient_name_on_doc": "Rajesh Kumar",
            "content": {
                "doctor_name": "Dr. Arun Sharma",
                "doctor_registration": "KA/45678/2015",
                "patient_name": "Rajesh Kumar",
                "date": "2024-11-01",
                "diagnosis": "Viral Fever",
                "medicines": ["Paracetamol 650mg", "Vitamin C 500mg"],
            },
        },
        {
            "file_id": "F008",
            "file_name": "hospital_bill.jpg",
            "actual_type": "HOSPITAL_BILL",
            "quality": "GOOD",
            "patient_name_on_doc": "Rajesh Kumar",
            "content": {
                "hospital_name": "City Clinic, Bengaluru",
                "patient_name": "Rajesh Kumar",
                "date": "2024-11-01",
                "line_items": [
                    {"description": "Consultation Fee", "amount": 1000},
                    {"description": "CBC Test", "amount": 300},
                    {"description": "Dengue NS1 Test", "amount": 200},
                ],
                "total": 1500,
            },
        },
    ]


@pytest.fixture
def sample_documents_wrong_type():
    """Wrong document type — two prescriptions for consultation."""
    return [
        {
            "file_id": "F001",
            "file_name": "dr_sharma_prescription.jpg",
            "actual_type": "PRESCRIPTION",
            "quality": "GOOD",
            "patient_name_on_doc": "Rajesh Kumar",
        },
        {
            "file_id": "F002",
            "file_name": "another_prescription.jpg",
            "actual_type": "PRESCRIPTION",
            "quality": "GOOD",
            "patient_name_on_doc": "Rajesh Kumar",
        },
    ]
