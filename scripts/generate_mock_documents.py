#!/usr/bin/env python3
"""Generate mock medical documents for evaluation test cases.

Creates JSON-based mock documents that simulate the extraction output
expected from real document processing. Used by the eval runner and tests.

Usage:
    uv run python scripts/generate_mock_documents.py
"""

from __future__ import annotations

import json
from pathlib import Path

# Output directory
OUTPUT_DIR = Path("/workspace/uploads/mock")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Mock Document Templates ──────────────────────────────────────

PRESCRIPTION_TEMPLATE = {
    "doctor_name": "Dr. {doctor}",
    "doctor_registration": "{reg}",
    "patient_name": "{patient}",
    "date": "{date}",
    "diagnosis": "{diagnosis}",
    "medicines": [],
    "tests_ordered": [],
}

HOSPITAL_BILL_TEMPLATE = {
    "hospital_name": "{hospital}",
    "patient_name": "{patient}",
    "date": "{date}",
    "line_items": [],
    "total": 0,
}

PHARMACY_BILL_TEMPLATE = {
    "pharmacy_name": "{pharmacy}",
    "patient_name": "{patient}",
    "date": "{date}",
    "medicines": [],
    "total": 0,
}

LAB_REPORT_TEMPLATE = {
    "lab_name": "{lab}",
    "patient_name": "{patient}",
    "test_name": "{test}",
    "result": "{result}",
    "date": "{date}",
}

DENTAL_REPORT_TEMPLATE = {
    "dentist_name": "{dentist}",
    "patient_name": "{patient}",
    "procedure": "{procedure}",
    "date": "{date}",
}

# ── Test Case Document Sets ──────────────────────────────────────

TEST_CASE_DOCUMENTS = {
    "TC001": {
        "description": "Wrong document — two prescriptions for consultation",
        "documents": [
            {
                "file_id": "F001",
                "file_name": "dr_sharma_prescription.jpg",
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
                "file_id": "F002",
                "file_name": "another_prescription.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Rajesh Kumar",
                "content": {
                    "doctor_name": "Dr. Priya Nair",
                    "doctor_registration": "KA/12345/2018",
                    "patient_name": "Rajesh Kumar",
                    "date": "2024-11-01",
                    "diagnosis": "Viral Fever",
                },
            },
        ],
    },
    "TC002": {
        "description": "Unreadable document — blurry pharmacy bill",
        "documents": [
            {
                "file_id": "F003",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Priya Singh",
                "content": {
                    "doctor_name": "Dr. Mehta",
                    "patient_name": "Priya Singh",
                    "diagnosis": "Migraine",
                },
            },
            {
                "file_id": "F004",
                "file_name": "blurry_bill.jpg",
                "actual_type": "PHARMACY_BILL",
                "quality": "UNREADABLE",
                "patient_name_on_doc": "Priya Singh",
            },
        ],
    },
    "TC003": {
        "description": "Patient name mismatch",
        "documents": [
            {
                "file_id": "F005",
                "file_name": "rx_rajesh.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Rajesh Kumar",
            },
            {
                "file_id": "F006",
                "file_name": "bill_arjun.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Arjun Mehta",
            },
        ],
    },
    "TC004": {
        "description": "Clean consultation — full approval",
        "documents": [
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
        ],
    },
    "TC005": {
        "description": "Diabetes — within 90-day waiting period",
        "documents": [
            {
                "file_id": "F009",
                "file_name": "rx_diabetes.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Vikram Joshi",
                "content": {
                    "diagnosis": "Type 2 Diabetes Mellitus",
                    "doctor_name": "Dr. Sunil Mehta",
                    "doctor_registration": "GJ/56789/2014",
                },
            },
            {
                "file_id": "F010",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Vikram Joshi",
                "content": {"total": 3000},
            },
        ],
    },
    "TC006": {
        "description": "Dental — partial approval with cosmetic exclusion",
        "documents": [
            {
                "file_id": "F011",
                "file_name": "dental_bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Priya Singh",
                "content": {
                    "hospital_name": "Smile Dental Clinic",
                    "total": 12000,
                    "line_items": [
                        {"description": "Root Canal Treatment", "amount": 8000},
                        {"description": "Teeth Whitening", "amount": 4000},
                    ],
                },
            },
        ],
    },
    "TC007": {
        "description": "MRI without pre-authorization",
        "documents": [
            {
                "file_id": "F012",
                "file_name": "rx_mri.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Sneha Patil",
                "content": {
                    "diagnosis": "Chronic Lower Back Pain",
                    "doctor_name": "Dr. K. Rao",
                    "doctor_registration": "MH/34567/2016",
                },
            },
            {
                "file_id": "F013",
                "file_name": "bill_mri.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Sneha Patil",
                "content": {
                    "line_items": [
                        {"description": "MRI Lumbar Spine", "amount": 15000},
                    ],
                    "total": 15000,
                },
            },
        ],
    },
    "TC008": {
        "description": "Per-claim limit exceeded",
        "documents": [
            {
                "file_id": "F015",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Amit Verma",
                "content": {
                    "diagnosis": "Gastroenteritis",
                    "doctor_name": "Dr. R. Gupta",
                },
            },
            {
                "file_id": "F016",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Amit Verma",
                "content": {
                    "total": 7500,
                    "line_items": [
                        {"description": "Consultation Fee", "amount": 2000},
                        {"description": "Medicines", "amount": 5500},
                    ],
                },
            },
        ],
    },
    "TC009": {
        "description": "Multiple same-day claims — fraud signal",
        "documents": [
            {
                "file_id": "F017",
                "file_name": "rx_migraine.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Ravi Menon",
                "content": {
                    "diagnosis": "Migraine",
                    "doctor_name": "Dr. S. Khan",
                },
            },
            {
                "file_id": "F018",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Ravi Menon",
                "content": {"total": 4800},
            },
        ],
    },
    "TC010": {
        "description": "Network hospital — discount before co-pay",
        "documents": [
            {
                "file_id": "F019",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Deepak Shah",
                "content": {
                    "diagnosis": "Acute Bronchitis",
                    "doctor_name": "Dr. S. Iyer",
                },
            },
            {
                "file_id": "F020",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Deepak Shah",
                "content": {
                    "hospital_name": "Apollo Hospitals",
                    "total": 4500,
                    "line_items": [
                        {"description": "Consultation Fee", "amount": 1500},
                        {"description": "Medicines", "amount": 3000},
                    ],
                },
            },
        ],
    },
    "TC011": {
        "description": "Component failure — graceful degradation",
        "documents": [
            {
                "file_id": "F021",
                "file_name": "rx_ayur.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Kavita Nair",
                "content": {
                    "diagnosis": "Chronic Joint Pain",
                    "treatment": "Panchakarma Therapy",
                },
            },
            {
                "file_id": "F022",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Kavita Nair",
                "content": {
                    "total": 4000,
                    "line_items": [
                        {"description": "Panchakarma Therapy (5 sessions)", "amount": 3000},
                    ],
                },
            },
        ],
    },
    "TC012": {
        "description": "Excluded treatment — obesity/bariatric",
        "documents": [
            {
                "file_id": "F023",
                "file_name": "rx_obesity.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Anita Desai",
                "content": {
                    "diagnosis": "Morbid Obesity — BMI 37",
                    "treatment": "Bariatric Consultation and Customised Diet Plan",
                },
            },
            {
                "file_id": "F024",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Anita Desai",
                "content": {
                    "total": 8000,
                    "line_items": [
                        {"description": "Bariatric Consultation", "amount": 3000},
                        {"description": "Personalised Diet and Nutrition Program", "amount": 5000},
                    ],
                },
            },
        ],
    },
}


def generate_all() -> None:
    """Generate mock document sets for all test cases."""
    for case_id, case_data in TEST_CASE_DOCUMENTS.items():
        output_path = OUTPUT_DIR / f"{case_id}.json"
        with open(output_path, "w") as f:
            json.dump(case_data, f, indent=2)

    print(f"Generated {len(TEST_CASE_DOCUMENTS)} mock document sets in {OUTPUT_DIR}")
    for case_id in sorted(TEST_CASE_DOCUMENTS.keys()):
        print(f"  {case_id}: {TEST_CASE_DOCUMENTS[case_id]['description']}")


def get_documents_for_case(case_id: str) -> list[dict] | None:
    """Get mock documents for a specific test case."""
    case = TEST_CASE_DOCUMENTS.get(case_id)
    return case["documents"] if case else None


if __name__ == "__main__":
    generate_all()
