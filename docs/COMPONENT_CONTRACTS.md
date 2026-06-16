# Component Contracts — Plum Claims Processing System

> **Canonical version:** This document is maintained in MDX format at `docs/architecture/component-contracts.mdx`. This Markdown version is a snapshot — refer to the MDX version for the most up-to-date contracts.

## API Endpoints

### POST `/api/v1/auth/login`
**Input:** `{ member_id: string, password: string }`
**Output:** `{ access_token: string, token_type: "bearer", member_id: string, member_name: string }`
**Errors:** 401 `INVALID_CREDENTIALS`

### POST `/api/v1/auth/register`
**Input:** `{ member_id: string, password: string }`
**Output:** Same as login
**Errors:** 404 `MEMBER_NOT_FOUND`, 422 `WEAK_PASSWORD`

### POST `/api/v1/claims`
**Input:** JSON body with `member_id`, `policy_id`, `claim_category`, `treatment_date`, `claimed_amount`, `documents[]`
**Output:** `ClaimResponse` (201) or `DocumentValidationErrorResponse` (422)
**Errors:** 422 `DOCUMENT_VALIDATION_FAILED`, 500 `INTERNAL_ERROR`

### POST `/api/v1/claims/upload`
**Input:** `multipart/form-data` with `member_id`, `claim_category`, `treatment_date`, `claimed_amount`, `files[]`, `document_types[]`
**Output:** `ClaimResponse` (201) or `DocumentValidationErrorResponse` (422)
**Errors:** 422 `DOCUMENT_VALIDATION_FAILED`, `FILE_TOO_LARGE`, `INVALID_FILE_TYPE`

### GET `/api/v1/claims/{claim_id}`
**Output:** `ClaimResponse`
**Errors:** 404 `RESOURCE_NOT_FOUND`

### GET `/api/v1/claims/{claim_id}/trace`
**Output:** `ProcessingTraceResponse`
**Errors:** 404 `RESOURCE_NOT_FOUND`

### GET `/api/v1/claims`
**Query:** `member_id?`, `status?`, `limit?`, `offset?`
**Output:** `ClaimListResponse`

### POST `/api/v1/documents/upload`
**Input:** `multipart/form-data` with `file`, `document_type`
**Output:** `{ file_id, file_name, file_path, content_type, size_bytes, document_type }`
**Errors:** 422 `INVALID_FILE_TYPE`, `FILE_TOO_LARGE`

### GET `/api/v1/documents/{file_id}/download`
**Output:** Binary file content
**Errors:** 404

---

## Agent Contracts

### VerificationAgent
**Input:** `{ claim_id, claim_category, documents[], ... }`
**Output:** `{ agent, is_valid: bool, errors[], warnings[], documents[], checks[], confidence }`
**Behavior:** Checks required types, wrong types, unreadable docs, patient name mismatch. Stops pipeline if invalid.

### ExtractionAgent
**Input:** `{ claim_id, documents[], simulate_component_failure? }`
**Output:** `{ agent, documents[], overall_confidence, unextracted_fields[], checks[], confidence }`
**Behavior:** Extracts structured data via LLM. Validates content for non-medical items. Raises on simulated failure.

### PolicyAgent
**Input:** `{ member_id, claim_category, treatment_date, claimed_amount, hospital_name, extraction_result, ytd_claims_amount }`
**Output:** `{ agent, decision, approved_amount, checks[], rejection_reasons[], line_items[], confidence, sessions_count }`
**Behavior:** Evaluates 12+ policy rules. Applies network discount then co-pay. Caps at per-claim, annual, sum insured, and family floater limits.

### FraudAgent
**Input:** `{ member_id, treatment_date, claimed_amount, claims_history? }`
**Output:** `{ agent, fraud_score, signals[], recommendation, priority, checks[], confidence }`
**Behavior:** Computes weighted fraud score from 5 signals. Thresholds: less than 0.30 PROCEED, 0.30–0.80 MANUAL_REVIEW, greater than 0.80 HIGH priority.

### DecisionAgent
**Input:** `{ verification_result, extraction_result, policy_result, fraud_result, degradation_info? }`
**Output:** `{ agent, decision, approved_amount, confidence_score, decision_reason, line_items[], rejection_reasons[], manual_review_recommended, degraded_components[] }`
**Behavior:** Aggregates all agent results. Priority: MANUAL_REVIEW > REJECTED > PARTIAL > APPROVED. All-failed → MANUAL_REVIEW with confidence 0.0.

---

## Provider Interfaces

### ILLMProvider
```python
async def chat(request: LLMRequest) -> LLMResponse
async def extract_structured(request: LLMRequest) -> dict
async def health_check() -> bool
```
**Implementations:** OpenAIAdapter, AnthropicAdapter, GoogleGeminiAdapter, MockLLMAdapter, CachedLLMProvider

### IStorageProvider
```python
async def upload(file: StoredFile) -> str  # Returns file_id
async def download(file_id: str) -> StoredFile
async def delete(file_id: str) -> None
async def exists(file_id: str) -> bool
```
**Implementations:** LocalStorageAdapter, MinIOAdapter, S3Adapter

### ICacheProvider
```python
async def get(key) -> bytes | None
async def set(key, value, ttl_seconds?) -> None
async def delete(key) -> bool
async def exists(key) -> bool
```
**Implementations:** RedisCacheAdapter, InMemoryCacheAdapter

### IDocumentProcessor
```python
async def classify_document(file, filename) -> DocumentType
async def assess_quality(file) -> QualityAssessment
async def extract_text(file, filename) -> ExtractionResult
async def extract_structured(file, filename, schema) -> BaseModel
```
**Implementations:** HybridDocumentProcessor (routes to Docling or Vision LLM)

---

## Domain Models

### Claim
`claim_id`, `member_id`, `policy_id`, `claim_category`, `treatment_date`, `claimed_amount`, `approved_amount?`, `decision?`, `decision_reason?`, `confidence_score?`, `status`, `hospital_name?`, `manual_review_recommended`, `degraded_components[]`, `processing_trace{}`

### ClaimDocument
`document_id`, `claim_id`, `file_name`, `file_path`, `content_type`, `document_type?`, `detected_type?`, `extraction_data{}`, `quality_score?`, `verification_status`, `patient_name_on_doc?`, `error_message?`

### ClaimLineItem
`line_item_id`, `claim_id`, `description`, `quantity`, `unit_rate?`, `amount`, `approved_amount?`, `is_covered?`, `rejection_reason?`

### ClaimProcessingStep
`step_id`, `claim_id`, `step_index`, `step_name`, `agent_name`, `status`, `input_data{}`, `output_data{}`, `error_message?`, `confidence_score?`, `checks_performed[]`, `started_at`, `completed_at?`, `duration_ms?`

### Member
`member_id`, `name`, `date_of_birth`, `gender`, `relationship`, `join_date`, `primary_member_id?`, `password_hash?`

### MemberClaimsSummary
`member_id`, `year`, `total_claims_count`, `total_claims_amount`, `approved_claims_count`, `approved_claims_amount`, `sessions_used_this_year`, `same_day_claim_count`, `family_approved_amount`

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `DOCUMENT_VALIDATION_FAILED` | 422 | Documents failed verification |
| `CLAIM_VALIDATION_FAILED` | 422 | Invalid claim data |
| `RESOURCE_NOT_FOUND` | 404 | Claim or document not found |
| `INVALID_CREDENTIALS` | 401 | Wrong member_id or password |
| `TOKEN_EXPIRED` | 401 | JWT expired |
| `INVALID_TOKEN` | 401 | Malformed JWT |
| `MISSING_TOKEN` | 401 | No Authorization header |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `FILE_TOO_LARGE` | 422 | File exceeds 10MB |
| `INVALID_FILE_TYPE` | 422 | Unsupported file type |
| `LLM_PROVIDER_ERROR` | 500 | LLM call failed |
| `STORAGE_ERROR` | 500 | File storage failed |
| `EXTRACTION_FAILED` | 500 | Document extraction failed |
| `POLICY_LOAD_FAILED` | 500 | Can't load policy file |
| `INTERNAL_ERROR` | 500 | Unexpected error |
