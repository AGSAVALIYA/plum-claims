# 🔍 Plum Assignment — Comprehensive Review & Improvement Plan

**Generated:** 2026-06-15
**Review scope:** Full codebase — backend, frontend, infrastructure, tests, docs, eval

---

## Executive Summary

Your assignment is **solid and well-built** — a working multi-agent pipeline, all 12 test cases passing, proper observability infrastructure (OpenTelemetry, Jaeger, Prometheus, Grafana), and a clean modular code architecture. However, there are **critical gaps** across deployment, frontend UX, trace quality, and testing that will cost significant points in evaluation.

### Current Estimated Score: **~7.4/10**
### Achievable Score with Improvements: **~9.0+/10**

---

## Score Breakdown by Evaluation Criteria

| Criteria | Weight | Current | Achievable | Key Gap |
|----------|--------|---------|------------|---------|
| **System Design** | 30% | 7.5/10 | 9.0/10 | Architecture doc missing "why"/trade-offs; docker-compose missing services; dead rate limiter |
| **Engineering Quality** | 25% | 7.0/10 | 9.0/10 | No API or frontend tests; dead code paths; triplicate verification logic |
| **Observability** | 20% | 6.5/10 | 9.0/10 | Traces lack detailed reasoning chains; metrics unverified; pipeline spans sparse |
| **AI Integration** | 15% | 7.0/10 | 8.5/10 | Hybrid processor sends filename only; no few-shot examples; hardcoded confidence |
| **Document Verification** | 10% | 7.0/10 | 9.0/10 | Error messages too technical; triple MISSING_REQUIRED errors; processor stub |
| **Bonus: Multi-Agent** | — | ✅ | ✅ | Already implemented — 5-agent pipeline with clean interfaces |

---

## 🔴 CRITICAL — Must Fix (Will Lose Major Points)

### 1. Docker Compose Missing Celery Worker & Frontend
> **Severity:** 🔴 CRITICAL | **Effort:** Low (30 min)

**File:** `docker-compose.yml`

The README says `docker compose up -d` starts "all services (backend, frontend, db, redis, jaeger, prometheus, grafana)" but the compose file has **no Celery worker service** and **no frontend service**. Any claim submitted via the API will sit in `SUBMITTED` forever because no worker consumes the queue. The frontend simply can't be accessed via docker-compose.

**Additionally:** MinIO container runs but is unused — no service references the `minio` hostname since `STORAGE_PROVIDER=local` is hardcoded.

**Fix:**
```yaml
# Add to docker-compose.yml:
worker:
  build: .
  command: celery -A backend.core.celery_app worker -Q claims -l info
  depends_on: [db, redis]
  networks: [plum_net]

frontend:
  build: ./frontend
  ports: ["3000:3000"]
  depends_on: [app]
  networks: [plum_net]
```

---

### 2. Demo Video is MISSING
> **Severity:** 🔴 CRITICAL | **Effort:** Medium (1-2 hrs)

The assignment **requires** an 8–12 minute demo video. This is a **listed deliverable**. Not having it is a guaranteed point deduction. No video or deployed URL was found anywhere in the workspace.

**Required content per assignment:**
- A claim stopped early due to document problems (show the specific error message) — use TC001
- A successful end-to-end approval with the full trace visible — use TC004
- One technical decision you're genuinely proud of
- One thing you'd change given more time

---

### 3. HybridDocumentProcessor Sends Filename Only — No Document Content
> **Severity:** 🔴 CRITICAL | **Effort:** Medium (2-3 hrs)

**File:** `backend/providers/doc_processing/hybrid_processor.py:196-197`

```python
"content": f"Filename: {filename}. Document type: {await self.classify_document(file_bytes, filename)}",
```

For any real PDF/image upload (not pre-extracted test data with `content` stubs), the LLM receives **only the filename string**, not the actual document bytes. Document extraction is effectively broken for real uploads. The Docling integration is a stub (`pass  # Placeholder for real Docling integration` at line 69).

**Fix:** Pass base64-encoded file content as the user message, or complete the Docling integration for OCR-based extraction.

---

### 4. Architecture Document Lacks "Why", Trade-offs, and Scalability Plan
> **Severity:** 🔴 CRITICAL | **Effort:** Low (1 hr)

**File:** `docs/ARCHITECTURE.md`, `docs/architecture/overview.mdx`

The assignment explicitly asks: *"What did you consider and reject? What are the limitations of your current design and how would you address them at 10x the current load?"*

**What's missing:**

| Section | Status | What to Add |
|---------|--------|-------------|
| Why each design decision was made | ❌ | "We chose sequential agents over parallel because..." |
| Alternatives considered and rejected | ❌ | "We considered LangChain but rejected it because..."; "We considered NoSQL but chose PostgreSQL because..." |
| Current limitations | ❌ | "Document extraction accuracy depends on quality; fraud detection is rule-based; no multi-page support" |
| 10x scalability plan | ❌ | "Horizontal scaling of Celery workers; LLM request batching; read replicas; Redis cluster; Kafka for event sourcing" |
| Cost modeling | ❌ | 5 LLM calls per claim at 75K claims/year = ~$X monthly at current token prices |
| Why Next.js over SPA, PostgreSQL over NoSQL | ❌ | These decisions are stated but not justified |

**Also:** The `.md` and `.mdx` versions of architecture docs diverge — `COMPONENT_CONTRACTS.md` vs `component-contracts.mdx` have incompatible `IStorageProvider` signatures. The `ARCHITECTURE.md` says the system uses async Celery, but `overview.mdx` describes a different model. Consolidate into one set of docs.

---

### 5. Pipeline Traces Lack Detailed Reasoning (20% of grade!)
> **Severity:** 🔴 CRITICAL | **Effort:** Medium (2-3 hrs)

**File:** `backend/orchestrator/agents/` (all agents)

The assignment says: *"someone on the operations team must be able to look at the system's output and understand exactly what happened — what was checked, what passed, what failed, and why"*

**Current trace output in eval report:**
```
| Policy Evaluation | policy_agent | COMPLETED | 0.95 | 3ms |
```

**What it SHOULD show:**
```
Policy Evaluation — COMPLETED (0.95 confidence, 3ms)
├── ✅ Coverage Check: CONSULTATION covered under Plan PLUM_GHI_2024
├── ✅ Network Hospital: "Apollo Hospitals" is in-network → 20% discount applied
├── ✅ Waiting Period: member enrolled 2024-04-01 (>30 days ago), no condition-specific waits apply
├── ✅ Exclusion Check: "Viral Fever" not in exclusion list → PASSED
├── ✅ Pre-Auth Check: Consultation does not require pre-authorization → PASSED
├── ✅ Sub-limit Check: ₹1500 within per-claim limit of ₹5000 → PASSED
├── ℹ️ Co-pay Applied: 10% co-pay on ₹1500 = ₹150 deducted
├── ℹ️ Network Discount: 20% on ₹1500 = ₹300 deducted (applied before co-pay in TC010)
└── ℹ️ Final Amount: ₹1500 - ₹300 (discount) = ₹1200 - ₹120 (10% co-pay) = ₹1080
```

**Where to fix:** Each agent's `execute()` method should populate `output_summary` with detailed, human-readable entries for every check performed. The `checks` list already exists in most agents — enrich each check with clear `reason` text.

---

### 6. Eval Report Has Contradictory Data
> **Severity:** 🔴 CRITICAL | **Effort:** Low (30 min)

**File:** `eval_report.md`

An evaluator will audit these numbers:

- **TC005** (line 114): `approved_amount: ₹2700.0` despite decision being `REJECTED`. A rejected claim should show `₹0.00`.
- **TC006** (line 137): `approved_amount: ₹0.0` but line items show Root Canal Treatment approved at ₹8000. These contradict — total should be ₹8000 (or ₹5000 if per-claim capped).
- **TC005** (line 120): `approved_amount: ₹2700.0` even though the claim was rejected for WAITING_PERIOD — the system is calculating a hypothetical approved amount on a rejected claim.

**Fix:** Fix the `approved_amount` calculation in the decision agent (`backend/domain/decision/service.py`) to correctly handle REJECTED claims (always 0) and sum line-item approved amounts for PARTIAL claims.

---

### 7. No Frontend Tests & Weak API Tests
> **Severity:** 🔴 CRITICAL | **Effort:** Medium-High (3-4 hrs)

The assignment says: *"Every significant component must have tests. A system with no tests is incomplete."*

**Missing entirely:**
- ❌ **Zero frontend tests** (no Jest, Vitest, Playwright, or Cypress)
- ❌ **No API endpoint tests** (no FastAPI `TestClient` usage — tests go through Python layer, bypassing HTTP validation, middleware, auth, serialization)
- ❌ No auth flow tests (login, register, token refresh)
- ❌ No admin endpoint tests (dashboard, override, rerun)
- ❌ No Celery task tests

**What's missing in backend tests:**
- ❌ No unit tests for individual orchestrator agents (verification, extraction, policy, fraud, decision — only tested through heavy integration tests)
- ❌ No tests for `FraudService.assess_fraud()` in isolation (same-day, monthly, high-value, alteration signals)
- ❌ No tests for `DecisionService.compute_decision()` or confidence computation
- ❌ No tests for Redis adapter, S3 adapter, MinIO adapter (only LocalStorage tested)
- ❌ No tests for LLM adapters (mock provider is used but its behavior is unverified)
- ❌ No negative/error-path tests (invalid member_id, missing policy_id, future dates, negative amounts, empty documents)
- ❌ Estimated line coverage: **under 20%** of ~55 source files

**What exists (good):**
- ✅ All 12 assignment test cases covered in `test_claim_pipeline.py`
- ✅ 18 policy service unit tests
- ✅ 5 document verification tests
- ✅ Integration tests with in-memory SQLite

---

## 🟡 HIGH IMPACT — Should Fix (Noticeable Improvement)

### 8. Frontend: Document Errors Show Raw Technical Codes
> **Severity:** 🟡 HIGH | **Effort:** Low (30 min)

**File:** `frontend/src/app/claims/[id]/page.tsx:560-563`

Users see raw error badges like `PATIENT_MISMATCH`, `WRONG_DOC_TYPE`, `UNREADABLE` — not actionable error messages. **This directly hurts evaluation of TC001-TC003** where the assignment requires messages to be "specific enough that the member knows precisely what to do next."

The old frontend (`frontend-old/src/components/claims/FailureReasonCard.tsx`) had an `ERROR_TYPE_MESSAGES` mapping that translated every error type into clear, non-technical language with helpful icons. This was removed from the new frontend.

**Fix:** Add a user-friendly error mapping. Example:
```typescript
const USER_FRIENDLY_ERRORS: Record<string, string> = {
  PATIENT_MISMATCH: "The name on this document doesn't match your records. Please upload documents that belong to you.",
  WRONG_DOC_TYPE: "This document type isn't accepted for this claim. Please check what documents are required and re-upload.",
  UNREADABLE: "We couldn't read this document because it's too blurry. Please upload a clearer version.",
  MISSING_REQUIRED: "A required document is missing. Please upload the document listed below.",
};
```

---

### 9. Frontend: No Auto-Polling for In-Progress Claims (UX Regression)
> **Severity:** 🟡 HIGH | **Effort:** Low (15 min)

**File:** `frontend/src/app/claims/[id]/page.tsx`

After submitting a claim, the user sees a static page. If the claim is still PROCESSING/VALIDATING, the user must manually refresh. The old frontend (`frontend-old`) had `setInterval(fetchClaim, 3000)` — this was removed in the new frontend.

**Fix:** Add a `useEffect` that polls every 3 seconds while status is `SUBMITTED`/`VALIDATING`/`PROCESSING`, with cleanup on unmount and a max retry count.

---

### 10. Frontend: Retry Button Sends Empty Body (Broken Recovery Flow)
> **Severity:** 🟡 HIGH | **Effort:** Medium (1 hr)

**File:** `frontend/src/app/claims/[id]/page.tsx:321`

```typescript
await retryClaim(claim.claim_id, {});
```

The retry sends an empty object — there is no UI to re-upload corrected documents or add a comment. When a claim fails with `DOCUMENT_ERROR`, the retry button is useless. The old frontend had a full retry flow with file re-upload (`CustomFileUploader`), a comment textarea, and separate error/success states.

**Fix:** Add a retry UI section with file re-upload, at minimum. Or auto-redirect to the new claim form pre-populated with the failed claim's data.

---

### 11. Frontend: Admin Dashboard Shows USD Instead of INR
> **Severity:** 🟡 HIGH | **Effort:** Trivial (2 min — 1 line change)

**Files:**
- `frontend/src/app/admin/page.tsx:59-61` — `en-US` / `USD`
- `frontend/src/app/admin/claims/page.tsx:131` — `en-US` / `USD`

The admin panel shows dollar amounts on an Indian health insurance platform. The member-facing pages use `en-IN` / `INR` (e.g., `claims/[id]/page.tsx:82-86`). This is inconsistent and factually wrong. **An evaluator reviewing the admin dashboard will immediately notice.**

**Fix:** Change both files to:
```typescript
new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })
```

---

### 12. AI Confidence Hard-Coded to 0.88
> **Severity:** 🟡 HIGH | **Effort:** Low (30 min)

**File:** `backend/orchestrator/agents/policy_agent.py:713`

```python
ai_result = await llm.extract_structured(ai_request)
ai_confidence = 0.88  # UNCONDITIONAL — same value regardless of AI output
```

`ai_confidence` is set to `0.88` regardless of whether the AI analysis succeeded, failed, or returned useful insights. Combined with `min(ai_confidence, 0.95)` at line 734, clean claims always get 0.88 confidence. This looks arbitrary and would be questioned in evaluation.

**Fix:** Set `ai_confidence` based on whether the AI call succeeded (e.g., `0.88` if success, `1.0` if skipped/error), and use the AI's own confidence if available. Or set it based on how well the AI reasoning aligns with the rule-based result.

---

### 13. Document Verification: Triple MISSING_REQUIRED Errors
> **Severity:** 🟡 HIGH | **Effort:** Low (30 min)

**File:** `backend/domain/documents/service.py:49-145`

Three separate code blocks check for the same missing document condition:
- **Check 1** (lines 49-64): `if req_type not in uploaded_types`
- **Check 2** (lines 99-121): Duplicate check guarded by `if not errors`
- **Check 3** (lines 123-145): Triplicate check guarded by `if len(errors) == 0`

A single missing required document can generate up to 3 `MISSING_REQUIRED` errors. The guards partially mitigate this but the logic is fragmented and confusing. The test at `test_document_verification.py:78` only checks `len(result["errors"]) >= 1`, so the duplication is untested.

**Fix:** Consolidate into a single check per required type, with the best error message format from Check 1 (which includes the claim category context).

---

### 14. Malformed LLM Structured Output — No Validation or Retry
> **Severity:** 🟡 HIGH | **Effort:** Medium (1-2 hrs)

**Files:**
- `backend/providers/llm/openai_adapter.py:83-93` — DeepSeek mode uses `json_object` which only guarantees valid JSON, not schema conformance
- `backend/providers/llm/mock_adapter.py:155-156` — Returns `{"_raw": response.content}` sentinel on parse failure
- **All callers** (extraction agent, policy agent, fraud agent, decision agent) — **Never check for the `_raw` sentinel**

If the LLM returns malformed JSON (wrong field names, wrong types), the sentinel `{"_raw": "..."}` propagates through the pipeline as if it were valid data, causing downstream errors or silent data corruption.

**Fix:** Add schema validation and retry logic in each adapter's `extract_structured()`. If the response doesn't match the schema, retry once with an error message in the prompt.

---

### 15. Rate Limiter Redis Path is Dead Code
> **Severity:** 🟡 HIGH | **Effort:** Low (1 hr)

**File:** `backend/api/middleware.py:131-156`

The `_check_redis_rate_limit` method calls `cache.get_sync()` which **does not exist** on `RedisCacheAdapter` (it only has async methods — `get`, `set`, `delete`, `exists`). The code always falls through to `return True` at line 156, deferring to the in-memory path. This means multi-process rate limiting is non-functional — each uvicorn worker has its own in-memory window, so the actual rate limit is `N * limit` where N is the number of workers.

**Fix:** Either implement a proper Redis sorted-set sliding window (using `ZREMRANGEBYSCORE`/`ZCARD`/`ZADD` through the cache adapter), or remove the dead code and document that rate limiting is in-memory only.

---

## 🟢 NICE TO HAVE — Polish (Would Impress Reviewers)

### 16. Parallelize Independent Agents
Policy and Fraud agents are independent — they both read from extraction output but don't depend on each other. Running them in parallel (`asyncio.gather`) shows architectural sophistication and reduces end-to-end latency.

**Current flow:** Verification → Extraction → Policy → Fraud → Decision (sequential)
**Better flow:** Verification → Extraction → `[Policy ‖ Fraud]` → Decision

**File:** `backend/orchestrator/engine.py`, around lines 230-280

---

### 17. Component Contracts Not Precise Enough
**File:** `docs/COMPONENT_CONTRACTS.md` and `docs/architecture/component-contracts.mdx`

Contracts exist but lack:
- Exact JSON schemas with real examples
- Error type enumerations with trigger conditions
- Pre/post conditions per method
- Pagination contract (GET /claims accepts limit/offset but response doesn't specify total/next)
- Idempotency key contract (important for production)
- Rate limit response format (429 error body not defined)

**The two doc versions have incompatible `IStorageProvider.upload` signatures** — the `.md` shows `(file_name, content, content_type)` while `.mdx` shows `(file: StoredFile)`. Consolidate into one canonical doc.

---

### 18. Eval Report Needs Commentary & system_must Verification
**File:** `eval_report.md`, `scripts/run_eval.py`

**Current:** Just pass/fail results for all 12 cases.
**Should add:**
- Analysis per test case (what was interesting, what edge cases were hit)
- Note that tests ran with mock provider (real LLM behavior may differ)
- The eval script does NOT verify `expected.system_must` text requirements (e.g., TC001 requires "Tell the member specifically what document type was uploaded and what is needed instead" — only the decision field is checked)
- Discussion of TC009 (fraud detection with mock provider limitations)
- Edge cases not covered by the 12 test cases

---

### 19. Enhance Frontend Trace Visualization
**File:** `frontend/src/app/claims/[id]/page.tsx`, `frontend/src/app/admin/claims/[id]/page.tsx`

The claim detail page shows traces as a flat table. For the Observability criterion (20%), a **visual pipeline stepper/flowchart** with expandable reasoning per step would be much more impressive:

```
[✅ Verification] → [✅ Extraction] → [✅ Policy] → [✅ Fraud] → [✅ Decision]
     1.0              0.95             0.95           1.0           0.92
```

Each step expandable via click/accordion to show granular check results. The old frontend had a `ProcessingTraceViewer` component that was partially removed.

---

### 20. Per-Field Extraction Confidence
Instead of one overall confidence (0.95), report confidence per extracted field:
```json
{
  "patient_name": {"value": "Rajesh Kumar", "confidence": 0.98},
  "amount": {"value": 1500, "confidence": 0.85},
  "diagnosis": {"value": "Viral Fever", "confidence": 0.92},
  "doctor_registration": {"value": "KA/45678/2015", "confidence": 0.94}
}
```

**File:** `backend/domain/documents/service.py` — extraction schema and result structure

---

### 21. LLM Provider Fallback
If the primary LLM fails after retries, automatically fall back to a secondary provider. Shows production-readiness thinking and directly addresses the TC011 resilience requirement.

**File:** `backend/providers/llm/` — add a composite provider that wraps multiple adapters

---

### 22. Prompt Engineering Improvements
- Add few-shot examples of Indian medical document formats (from `sample_documents_guide.md`)
- Add chain-of-thought prompting for complex policy decisions
- Add medical abbreviation expansion (HTN→Hypertension, T2DM→Type 2 Diabetes)
- Add Indian doctor registration number format validation in prompts

---

### 23. Add Known Limitations to README
Shows maturity and honest self-assessment:
```markdown
## Known Limitations
- Document extraction accuracy depends on document quality; no Docling integration yet
- Fraud detection is primarily rule-based (AI signal is supplemental)
- No support for multi-page scanned PDFs
- Mock provider used for eval testing; real LLM results may vary
- SHA-256 password hashing (not bcrypt/argon2)
- Rate limiting is in-memory only (not Redis-backed in production)
- Embedded Celery worker pattern is dev-only; needs separate worker for production
```

---

### 24. Custom OpenTelemetry Span Attributes
Add `claim_id`, `member_id`, `category`, `agent_name` as span attributes for easier Jaeger filtering and correlation.

**File:** `backend/orchestrator/engine.py` — span creation in `_process_claim`

---

### 25. Correlate Logs with Traces
Add `trace_id` and `span_id` to structured log records so logs can be linked to Jaeger traces for end-to-end debugging.

**File:** `backend/core/logging.py`

---

### 26. Frontend Accessibility Improvements
- Add skip-to-content link at top of every page
- Fix dead "Forgot password?" button (`login/page.tsx:146` — has `tabIndex={-1}`, no `onClick`)
- Fix non-functional notification bell (`Header.tsx:60` — `aria-label="Notifications"` but does nothing)
- Fix image alt text using filenames instead of descriptions (`claims/[id]/page.tsx:655`)
- Add `loading="lazy"` to document preview images

---

### 27. Backend Code Cleanup (Quick Wins)

| Issue | File | Line |
|-------|------|------|
| Unreachable `return` after `return "mock"` | `providers/llm/mock_adapter.py` | 147 |
| `degraded_components` column type `Mapped[dict]` but default `list` | `domain/claims/models.py` | 49 |
| Module-level `import Member` at bottom of file | `tests/test_claim_pipeline.py` | 822 |
| Test deps (`pytest-asyncio`, `aiosqlite`, `pluggy`) in production deps | `pyproject.toml` | — |
| `all_agents_failed` property never True if step 1 succeeds | `orchestrator/state.py` | 94-98 |
| TC009 test uses permissive `in ("APPROVED", "MANUAL_REVIEW")` assertion | `tests/test_claim_pipeline.py` | 549 |
| Dead packages in frontend: `@radix-ui/react-toast`, `react-hot-toast`, `shadcn` | `frontend/package.json` | — |
| README lists 10 claim categories, code handles only 6 | `README.md` | — |
| Three different `LLM_PROVIDER` defaults across docs (.env, README, configuration.mdx) | Multiple | — |

---

## 🔧 Prioritized Action Plan

| Priority | Task | Impact | Effort | Criteria Affected |
|----------|------|--------|--------|-------------------|
| 🔴 P0 | Enrich pipeline traces with detailed reasoning per check | +1.5 pts | 2-3 hrs | Observability (20%), System Design (30%) |
| 🔴 P0 | Record demo video (8-12 min) | Required | 1-2 hrs | Deliverable |
| 🔴 P0 | Enhance architecture doc (why, trade-offs, 10x scalability) | +1.0 pts | 1 hr | System Design (30%) |
| 🔴 P0 | Add Celery worker + frontend to docker-compose.yml | Required | 30 min | System Design (30%) |
| 🔴 P0 | Fix TC005/TC006 eval report data inconsistencies | +0.5 pts | 30 min | Deliverable |
| 🔴 P1 | Add API endpoint tests (FastAPI TestClient) | +0.5 pts | 2 hrs | Engineering Quality (25%) |
| 🔴 P1 | Make document error messages user-friendly (frontend mapping) | +0.5 pts | 30 min | Document Verification (10%) |
| 🔴 P1 | Add auto-polling to claim detail page | +0.3 pts | 15 min | Engineering Quality (25%) |
| 🟡 P2 | Fix HybridDocumentProcessor to pass actual file content | +0.5 pts | 2-3 hrs | AI Integration (15%) |
| 🟡 P2 | Fix AI confidence hard-coded to 0.88 | +0.3 pts | 30 min | AI Integration (15%) |
| 🟡 P2 | Remove triplicate MISSING_REQUIRED checks | +0.2 pts | 30 min | Document Verification (10%) |
| 🟡 P2 | Fix Redis rate limiter dead code | +0.3 pts | 1 hr | System Design (30%) |
| 🟡 P2 | Parallelize Policy + Fraud agents | +0.3 pts | 1 hr | System Design (30%) |
| 🟡 P2 | Fix frontend retry flow (allow document re-upload) | +0.3 pts | 1 hr | Engineering Quality (25%) |
| 🟡 P2 | Add eval report commentary | +0.3 pts | 30 min | Deliverable |
| 🟡 P2 | Improve component contracts precision | +0.3 pts | 1 hr | System Design (30%) |
| 🟢 P3 | Fix admin currency from USD to INR | +0.2 pts | 2 min | Engineering Quality |
| 🟢 P3 | Add LLM structured output validation + retry | +0.2 pts | 1-2 hrs | AI Integration (15%) |
| 🟢 P3 | Add frontend trace visualization (stepper) | +0.3 pts | 2 hrs | Observability (20%) |
| 🟢 P3 | Add admin dashboard charts | +0.2 pts | 1-2 hrs | Engineering Quality |
| 🟢 P4 | LLM provider fallback (primary → secondary) | +0.1 pts | 1 hr | AI Integration (15%) |
| 🟢 P4 | Few-shot prompt examples | +0.1 pts | 30 min | AI Integration (15%) |
| 🟢 P4 | Custom span attributes (claim_id, member_id) | +0.1 pts | 15 min | Observability (20%) |
| 🟢 P4 | Correlate logs with traces (trace_id in logs) | +0.1 pts | 30 min | Observability (20%) |
| 🟢 P4 | Add frontend tests (at least smoke tests) | +0.2 pts | 2 hrs | Engineering Quality (25%) |
| 🟢 P4 | Add known limitations to README | +0.1 pts | 15 min | Deliverable |

---

## What's Done WELL ✅

| Area | Strengths |
|------|-----------|
| **Multi-agent Architecture** | 5-agent pipeline with clean interfaces — directly addresses the bonus points requirement |
| **Graceful Degradation** | Failed agents don't crash the pipeline; confidence is adjusted and manual review is recommended (TC011 passes) |
| **Policy Rules** | 30+ rules covering all categories — waiting periods, exclusions, co-pay, network discounts, sub-limits, family floater, sessions, branded drugs, pre-auth |
| **All 12 Test Cases Pass** | 100% pass rate in eval (though data issues exist in the report — see P0) |
| **Infrastructure** | Docker Compose, Jaeger, Prometheus, Grafana with 14-panel dashboard — production-grade observability stack |
| **LLM Provider Abstraction** | Clean interface supporting Gemini/OpenAI/Anthropic/Mock with config-based switching |
| **Code Architecture** | Clean DDD with `api/` / `domain/` / `orchestrator/` / `providers/` / `core/` separation |
| **Mock Provider** | Enables testing without API keys or cost |
| **Frontend UI** | Professional design with shadcn/ui, TailwindCSS, Framer Motion animations |
| **Auth System** | JWT with role-based access (member/admin), protected routes |
| **Early Document Validation** | Pipeline stops on verification failure before wasting LLM calls |
| **Log Scrubbing** | PHI/PII redaction in structured logging — important for production |
| **Dependency Injection** | Clean container-based DI with proper lifecycle management in tests |
| **Async Patterns** | Consistent async/await throughout, FastAPI lifespan for startup/shutdown |

---

> [!TIP]
> **The single biggest score multiplier** is enriching the pipeline traces with detailed, human-readable reasoning per check. This directly impacts Observability (20%) AND System Design (30%) AND makes the demo video much more impressive. Every check in the policy agent already has a `reason` field — they just need to be surfaced and formatted for human consumption. Focus here first.

> [!TIP]
> **If you only have 4 hours:** (1) Add Celery worker + frontend to docker-compose (30 min), (2) Fix admin USD→INR (2 min), (3) Add user-friendly error messages in frontend (30 min), (4) Fix eval report TC005/TC006 data (30 min), (5) Enrich a few key traces with detailed reasoning (1.5 hrs), (6) Record the demo video showing the enriched traces (1 hr).
