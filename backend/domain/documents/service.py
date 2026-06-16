"""Document domain service — handles verification and extraction orchestration."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Orchestrates document verification and extraction for a claim."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def verify_documents(
        self,
        claim_id: int,
        claim_category: str,
        policy_doc_reqs: dict[str, Any],
        uploaded_docs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Verify uploaded documents against policy requirements.

        Performs three checks:
        1. Required document types are present
        2. Document readability/quality
        3. Patient name consistency across documents
        """
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        verified_docs: list[dict[str, Any]] = []

        required_types = policy_doc_reqs.get("required", [])
        uploaded_types = [d.get("actual_type", "") for d in uploaded_docs]
        uploaded_by_type: dict[str, list[dict]] = {}
        for d in uploaded_docs:
            dt = d.get("actual_type", "")
            uploaded_by_type.setdefault(dt, []).append(d)

        # Check 1: Required document types present
        # Consolidated single check per required type — avoids triplicate duplicate errors
        types_found = set(uploaded_types)
        missing_required = [rt for rt in required_types if rt not in types_found]
        if missing_required:
            for req_type in missing_required:
                # Check if any uploaded doc type is wrong (uploaded wrong type instead)
                uploaded_wrong_type = None
                for doc in uploaded_docs:
                    dt = doc.get("actual_type", "")
                    if dt not in required_types and dt not in (doc.get("file_name", "") for _ in [1]):
                        uploaded_wrong_type = doc
                        break

                if uploaded_wrong_type and req_type == missing_required[0]:
                    errors.append(
                        {
                            "error_type": "MISSING_REQUIRED",
                            "file_name": uploaded_wrong_type.get("file_name", ""),
                            "message": (
                                f"You uploaded a {uploaded_wrong_type.get('actual_type', 'document')} "
                                f"('{uploaded_wrong_type.get('file_name', '')}'), but a {req_type} is required. "
                                f"For {claim_category} claims, please upload: {', '.join(required_types)}."
                            ),
                            "details": {
                                "uploaded_type": uploaded_wrong_type.get("actual_type", ""),
                                "required_type": req_type,
                                "file_name": uploaded_wrong_type.get("file_name", ""),
                                "claim_category": claim_category,
                            },
                        }
                    )
                else:
                    errors.append(
                        {
                            "error_type": "MISSING_REQUIRED",
                            "document_type": req_type,
                            "message": (
                                f"Missing required document: {req_type}. "
                                f"For {claim_category} claims, you must upload a {req_type}."
                            ),
                            "details": {
                                "required_type": req_type,
                                "claim_category": claim_category,
                            },
                        }
                    )

        # Check 2: Wrong types (uploaded doc type doesn't match any required or optional)
        optional_types = policy_doc_reqs.get("optional", [])
        all_allowed = set(required_types + optional_types)
        for doc in uploaded_docs:
            actual_type = doc.get("actual_type", "")
            if actual_type not in all_allowed:
                errors.append(
                    {
                        "error_type": "WRONG_TYPE",
                        "file_name": doc.get("file_name", ""),
                        "message": (
                            f"Wrong document type uploaded: '{doc.get('file_name', '')}' is a {actual_type}. "
                            f"For {claim_category} claims, you need to upload: {', '.join(required_types)}. "
                            f"A {actual_type} is not accepted for this claim type."
                        ),
                        "details": {
                            "uploaded_type": actual_type,
                            "required_types": required_types,
                            "file_name": doc.get("file_name", ""),
                        },
                    }
                )

        # Check 3: Quality / Readability
        for doc in uploaded_docs:
            quality = doc.get("quality", "GOOD")
            if quality == "UNREADABLE":
                errors.append(
                    {
                        "error_type": "UNREADABLE",
                        "document_id": doc.get("file_id", ""),
                        "file_name": doc.get("file_name", ""),
                        "message": (
                            f"The document '{doc.get('file_name', '')}' cannot be read clearly. "
                            f"Please re-upload a clear, legible version of this {doc.get('actual_type', 'document')}."
                        ),
                        "details": {
                            "file_name": doc.get("file_name", ""),
                            "document_type": doc.get("actual_type", ""),
                        },
                    }
                )

        # Check 4: Patient name consistency
        patient_names = set()
        for doc in uploaded_docs:
            name = doc.get("patient_name_on_doc")
            if name:
                patient_names.add(name)
        if len(patient_names) > 1:
            errors.append(
                {
                    "error_type": "PATIENT_MISMATCH",
                    "message": (
                        f"Documents belong to different patients. "
                        f"Patient names found: {', '.join(sorted(patient_names))}. "
                        f"All documents must belong to the same patient."
                    ),
                    "details": {
                        "patient_names": sorted(patient_names),
                    },
                }
            )

        is_valid = len(errors) == 0

        # Build verified document list
        for doc in uploaded_docs:
            verified_docs.append(
                {
                    "file_id": doc.get("file_id", ""),
                    "file_name": doc.get("file_name", ""),
                    "actual_type": doc.get("actual_type", ""),
                    "is_verified": is_valid,
                    "quality": doc.get("quality", "GOOD"),
                    "content": doc.get("content"),
                }
            )

        logger.info(
            "document_verification_done",
            claim_id=claim_id,
            is_valid=is_valid,
            error_count=len(errors),
        )

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "documents": verified_docs,
        }

    async def extract_document_data(
        self,
        claim_id: int,
        documents: list[dict[str, Any]],
        llm_provider=None,
        simulate_failure: bool = False,
    ) -> dict[str, Any]:
        """
        Extract structured data from verified documents.
        Uses the LLM provider to parse document content.
        """
        from backend.providers.llm.interface import LLMRequest

        extracted_docs = []
        overall_confidence = Decimal("0.0")
        unextracted_fields: list[str] = []
        # Track LLM usage/cost across all extraction calls
        llm_usage: dict[str, int] = {}
        llm_cost = 0.0

        if simulate_failure:
            raise RuntimeError("Simulated extraction failure")

        for i, doc in enumerate(documents):
            content = doc.get("content")
            doc_type = doc.get("actual_type", "")

            # Check if this is an image/PDF wrapper from storage (has _image_base64 or _pdf_base64)
            is_image_content = (
                isinstance(content, dict) and ("_image_base64" in content or "_pdf_base64" in content)
            )
            # Check if this is pre-extracted structured data from test cases
            is_structured_content = (
                isinstance(content, dict) and content and not is_image_content
            )

            # ── Route A: Pre-extracted structured data (test cases) ──
            # Use it directly but also run AI validation
            if is_structured_content:
                ai_valid = True
                ai_confidence = Decimal("0.95")
                try:
                    if llm_provider:
                        schema = {
                            "type": "object",
                            "properties": {
                                "is_medical_content": {"type": "boolean"},
                                "risk_score": {"type": "number"},
                                "suspicious_items": {"type": "array", "items": {"type": "string"}},
                                "reasoning": {"type": "string"},
                            },
                            "required": ["is_medical_content", "risk_score"],
                        }
                        ai_req = LLMRequest(
                            messages=[
                                {"role": "system", "content": "You are a medical claims auditor. Analyze this document content for medical legitimacy. Flag non-medical, suspicious, or fraudulent items. Return valid JSON only with: is_medical_content (bool), risk_score (0-1), suspicious_items (list of suspicious entries), reasoning (brief)."},
                                {"role": "user", "content": f"Document type: {doc_type}\nContent: {json.dumps(content)}"},
                            ],
                            response_schema=schema,
                            temperature=0,
                            max_tokens=500,
                        )
                        ai_result = await llm_provider.extract_structured(ai_req)
                        if isinstance(ai_result, dict):
                            _usage = ai_result.pop("_llm_usage", {})
                            _cost = ai_result.pop("_llm_cost", 0.0)
                            for k, v in _usage.items():
                                llm_usage[k] = llm_usage.get(k, 0) + v
                            llm_cost += _cost
                        if ai_result and not ai_result.get("is_medical_content", True):
                            ai_valid = False
                            ai_confidence = Decimal("0.3")
                            logger.warning(
                                "ai_content_validation_failed",
                                document_index=i,
                                doc_type=doc_type,
                                suspicious=ai_result.get("suspicious_items", []),
                                reasoning=ai_result.get("reasoning", ""),
                            )
                except Exception as e:
                    logger.warning("ai_content_validation_error", document_index=i, error=str(e))

                extracted_docs.append(
                    {
                        "document_index": i,
                        "document_type": doc_type,
                        "confidence": float(ai_confidence),
                        "extracted_data": content,
                        "ai_validated": ai_valid,
                    }
                )
                overall_confidence += ai_confidence
                if not ai_valid:
                    unextracted_fields.append(f"document_{i}_failed_ai_validation")
                continue

            # ── Route B: Image/PDF content from uploaded files ──
            # Send to vision-capable LLM for OCR + structured extraction
            if is_image_content:
                try:
                    if llm_provider:
                        import base64 as b64

                        schema = self._get_extraction_schema(doc_type)
                        file_name = content.get("_file_name", doc.get("file_name", "document"))

                        if "_image_base64" in content:
                            image_b64 = content["_image_base64"]
                            image_mime = content.get("_image_mime", "image/png")
                            user_message = [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Extract structured data from this {doc_type} document image "
                                        f"(file: {file_name}). Return ONLY valid JSON matching the schema."
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
                                },
                            ]
                        else:  # _pdf_base64
                            pdf_b64 = content["_pdf_base64"]
                            user_message = [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Extract structured data from this {doc_type} PDF document "
                                        f"(file: {file_name}). Return ONLY valid JSON matching the schema."
                                    ),
                                },
                                {
                                    "type": "file",
                                    "file_data": f"data:application/pdf;base64,{pdf_b64}",
                                    "filename": file_name,
                                },
                            ]

                        request = LLMRequest(
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        f"You are a medical document OCR and data extraction system. "
                                        f"Extract structured data from this {doc_type} document image. "
                                        f"Output valid JSON only, matching the provided schema."
                                    ),
                                },
                                {
                                    "role": "user",
                                    "content": user_message,
                                },
                            ],
                            response_schema=schema,
                            temperature=0,
                            max_tokens=2048,
                        )
                        result = await llm_provider.extract_structured(request)
                        if isinstance(result, dict):
                            _usage = result.pop("_llm_usage", {})
                            _cost = result.pop("_llm_cost", 0.0)
                            for k, v in _usage.items():
                                llm_usage[k] = llm_usage.get(k, 0) + v
                            llm_cost += _cost
                        extracted_docs.append(
                            {
                                "document_index": i,
                                "document_type": doc_type,
                                "confidence": 0.85,
                                "extracted_data": result,
                                "processor_used": "vision_llm",
                            }
                        )
                        overall_confidence += Decimal("0.85")
                        logger.info(
                            "vision_extraction_done",
                            document_index=i,
                            doc_type=doc_type,
                            file_name=file_name,
                        )
                    else:
                        extracted_docs.append(
                            {
                                "document_index": i,
                                "document_type": doc_type,
                                "confidence": 0.0,
                                "extracted_data": {},
                                "error": "No LLM provider available for vision extraction",
                            }
                        )
                        unextracted_fields.append(f"document_{i}")
                except Exception as e:
                    logger.warning("vision_extraction_failed", document_index=i, error=str(e))
                    extracted_docs.append(
                        {
                            "document_index": i,
                            "document_type": doc_type,
                            "confidence": 0.0,
                            "extracted_data": {},
                            "error": str(e),
                        }
                    )
                    unextracted_fields.append(f"document_{i}")
                continue

            # ── Route C: No content ──
            if content is None:
                extracted_docs.append(
                    {
                        "document_index": i,
                        "document_type": doc_type,
                        "confidence": Decimal("0.0"),
                        "extracted_data": {},
                    }
                )
                unextracted_fields.append(f"document_{i}")
                continue

            # ── Route D: Plain text content — use LLM for extraction ──
            try:
                if llm_provider:
                    schema = self._get_extraction_schema(doc_type)
                    request = LLMRequest(
                        messages=[
                            {
                                "role": "system",
                                "content": f"Extract structured data from this {doc_type} document. Output valid JSON.",
                            },
                            {
                                "role": "user",
                                "content": str(content),
                            },
                        ],
                        response_schema=schema,
                    )
                    result = await llm_provider.extract_structured(request)
                    if isinstance(result, dict):
                        _usage = result.pop("_llm_usage", {})
                        _cost = result.pop("_llm_cost", 0.0)
                        for k, v in _usage.items():
                            llm_usage[k] = llm_usage.get(k, 0) + v
                        llm_cost += _cost
                    extracted_docs.append(
                        {
                            "document_index": i,
                            "document_type": doc_type,
                            "confidence": Decimal("0.85"),
                            "extracted_data": result,
                        }
                    )
                    overall_confidence += Decimal("0.85")
                else:
                    extracted_docs.append(
                        {
                            "document_index": i,
                            "document_type": doc_type,
                            "confidence": Decimal("0.0"),
                            "extracted_data": {},
                        }
                    )
            except Exception as e:
                logger.warning("extraction_failed", document_index=i, error=str(e))
                extracted_docs.append(
                    {
                        "document_index": i,
                        "document_type": doc_type,
                        "confidence": Decimal("0.0"),
                        "extracted_data": {},
                        "error": str(e),
                    }
                )
                unextracted_fields.append(f"document_{i}")

        if extracted_docs:
            overall_confidence = overall_confidence / len(extracted_docs)

        return {
            "documents": extracted_docs,
            "overall_confidence": float(overall_confidence),
            "unextracted_fields": unextracted_fields,
            "llm_usage": llm_usage,
            "llm_cost": llm_cost,
        }

    def _get_extraction_schema(self, doc_type: str) -> dict[str, Any]:
        """Get the JSON schema for extracting a document type."""
        schemas = {
            "PRESCRIPTION": {
                "type": "object",
                "properties": {
                    "doctor_name": {"type": "string"},
                    "doctor_registration": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "date": {"type": "string"},
                    "diagnosis": {"type": "string"},
                    "medicines": {"type": "array", "items": {"type": "string"}},
                    "tests_ordered": {"type": "array", "items": {"type": "string"}},
                    "treatment": {"type": "string"},
                },
            },
            "HOSPITAL_BILL": {
                "type": "object",
                "properties": {
                    "hospital_name": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "date": {"type": "string"},
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "amount": {"type": "number"},
                                "quantity": {"type": "integer"},
                            },
                        },
                    },
                    "total": {"type": "number"},
                },
            },
            "LAB_REPORT": {
                "type": "object",
                "properties": {
                    "lab_name": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "test_name": {"type": "string"},
                    "result": {"type": "string"},
                    "date": {"type": "string"},
                },
            },
            "PHARMACY_BILL": {
                "type": "object",
                "properties": {
                    "pharmacy_name": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "date": {"type": "string"},
                    "medicines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "amount": {"type": "number"},
                            },
                        },
                    },
                    "total": {"type": "number"},
                },
            },
            "DENTAL_REPORT": {
                "type": "object",
                "properties": {
                    "dentist_name": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "procedure": {"type": "string"},
                    "date": {"type": "string"},
                },
            },
            "DIAGNOSTIC_REPORT": {
                "type": "object",
                "properties": {
                    "lab_name": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "test_name": {"type": "string"},
                    "date": {"type": "string"},
                },
            },
            "DISCHARGE_SUMMARY": {
                "type": "object",
                "properties": {
                    "hospital_name": {"type": "string"},
                    "patient_name": {"type": "string"},
                    "diagnosis": {"type": "string"},
                    "date": {"type": "string"},
                },
            },
        }
        return schemas.get(
            doc_type,
            {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                },
            },
        )
