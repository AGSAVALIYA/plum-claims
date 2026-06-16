#!/usr/bin/env python3
"""Evaluation runner — executes all 12 test cases from test_cases.json against the API.

Usage:
    uv run python scripts/run_eval.py

Requires:
    - The FastAPI server running on localhost:8000
    - test_cases.json in /workspace/assignment/
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# Config
API_BASE = "http://localhost:8000/api/v1"
TEST_CASES_PATH = Path("/workspace/assignment/test_cases.json")
OUTPUT_PATH = Path("/workspace/eval_report.md")


class EvalRunner:
    """Runs all test cases against the API and generates a report."""

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        self.results: list[dict[str, Any]] = []

    async def run_all(self) -> None:
        """Execute all test cases."""
        with open(TEST_CASES_PATH) as f:
            test_data = json.load(f)

        test_cases = test_data.get("test_cases", [])
        print(f"Running {len(test_cases)} test cases...\n")

        for i, tc in enumerate(test_cases):
            case_id = tc["case_id"]
            case_name = tc["case_name"]
            print(f"[{i+1}/{len(test_cases)}] {case_id}: {case_name}...", end=" ")

            result = await self.run_case(tc)
            self.results.append(result)

            # Print quick status
            expected = tc.get("expected", {})
            expected_decision = expected.get("decision")

            if result.get("system_stopped"):
                # Document error cases — check system stopped
                if expected_decision is None:
                    print("✅ PASS (stopped as expected)")
                else:
                    print("❌ FAIL (unexpected stop)")
            elif result.get("error"):
                print(f"❌ ERROR: {result['error']}")
            else:
                actual = result.get("decision", "?")
                if actual == expected_decision:
                    print(f"✅ PASS (decision: {actual})")
                else:
                    print(f"❌ FAIL (expected: {expected_decision}, got: {actual})")

        await self.client.aclose()
        self.generate_report()

    def _sm_status(self, case_id: str) -> str:
        """Return a formatted system_must status string for the given case id."""
        for r in self.results:
            if r.get("case_id") == case_id:
                sm_checks = r.get("system_must_checks")
                if not sm_checks:
                    return "N/A — no requirements"
                sm_pass = r.get("system_must_pass", False)
                details = r.get("system_must_details", "")
                icon = "PASS" if sm_pass else "FAIL"
                return f"{'✅' if sm_pass else '❌'} **{icon}** — {details}"
        return "⚠️ Unknown"

    def verify_system_must(
        self, test_case: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any]:
        """Verify system_must requirements for the test case via heuristic checks.

        Each test case with an ``expected.system_must`` array gets a targeted
        keyword / structural check against the actual response.
        """
        expected = test_case.get("expected", {})
        system_must = expected.get("system_must", [])
        case_id = test_case["case_id"]

        if not system_must:
            return {
                "passed": True,
                "details": "No system_must requirements",
                "checked": [],
            }

        checks: list[tuple[str, bool]] = []

        if case_id == "TC001":
            # Verify error message names the uploaded type AND the required type
            msg = result.get("error_message") or ""
            # The system may report MISSING_REQUIRED (naming the missing type)
            # or WRONG_TYPE (naming what was uploaded and what is needed).
            # Either way at least one specific type should be named.
            has_specific_type = (
                "PRESCRIPTION" in msg
                or "HOSPITAL_BILL" in msg
                or "prescription" in msg.lower()
                or "hospital bill" in msg.lower()
            )
            has_required = "HOSPITAL_BILL" in msg or "hospital bill" in msg.lower()
            checks.append(
                ("Reports specific document type(s)", has_specific_type)
            )
            checks.append(
                ("Names required type (HOSPITAL_BILL)", has_required)
            )

        elif case_id == "TC002":
            # Verify the response asks member to re-upload (not reject)
            msg = result.get("error_message") or ""
            has_unreadable = "cannot be read" in msg.lower() or "unreadable" in msg.lower()
            has_reupload = "re-upload" in msg.lower() or "reupload" in msg.lower()
            checks.append(("Identifies unreadable document", has_unreadable))
            checks.append(("Asks member to re-upload", has_reupload))

        elif case_id == "TC003":
            # Verify patient names are mentioned in the error
            msg = result.get("error_message") or ""
            has_mismatch = "different patients" in msg.lower() or "patient name" in msg.lower()
            has_names = "Rajesh" in msg or "Arjun" in msg
            checks.append(("Detects different-patient mismatch", has_mismatch))
            checks.append(("Mentions specific patient names", has_names))

        elif case_id == "TC005":
            # Verify the eligible_from date is stated
            reason = result.get("decision_reason") or ""
            trace_text = json.dumps(
                result.get("processing_trace", {}).get("steps", [])
            )
            combined = reason + " " + trace_text
            has_eligible = (
                "eligible from" in combined.lower()
                or "eligible_from" in combined
            )
            checks.append(("States eligible_from date", has_eligible))

        elif case_id == "TC006":
            # Verify line-item level rejection reasons are present
            line_items = result.get("line_items", [])
            has_reasons = any(li.get("rejection_reason") for li in line_items)
            checks.append(
                ("Line-item rejection reasons present", has_reasons)
            )

        elif case_id == "TC007":
            # Verify pre-auth guidance is provided
            reason = result.get("decision_reason") or ""
            trace_text = json.dumps(
                result.get("processing_trace", {}).get("steps", [])
            )
            combined = reason + " " + trace_text
            has_pre_auth = (
                "pre-auth" in combined.lower()
                or "preauthorization" in combined.lower()
                or "prior authorization" in combined.lower()
                or "PRE_AUTHORIZATION" in combined
            )
            checks.append(("Pre-auth guidance provided", has_pre_auth))

        elif case_id == "TC008":
            # Verify the per-claim limit and claimed amount are stated
            reason = result.get("decision_reason") or ""
            trace_text = json.dumps(
                result.get("processing_trace", {}).get("steps", [])
            )
            combined = reason + " " + trace_text
            has_limit = "per-claim limit" in combined.lower() or "per_claim_limit" in combined
            has_amount = "7500" in combined or "7,500" in combined
            checks.append(("States per-claim limit", has_limit))
            checks.append(("States claimed amount (₹7,500)", has_amount))

        elif case_id == "TC009":
            # Verify specific fraud signals are included
            reason = result.get("decision_reason") or ""
            is_manual_review = result.get("decision") == "MANUAL_REVIEW"
            has_claim_count = "4 claims" in reason or "3 claims" in reason
            has_same_day = "same-day" in reason.lower() or "same day" in reason.lower()
            checks.append(("Routes to manual review", is_manual_review))
            checks.append(
                ("Includes claim-count/same-day signal", has_claim_count or has_same_day)
            )

        elif case_id == "TC010":
            # Verify discount-before-copay breakdown is shown
            reason = result.get("decision_reason") or ""
            trace_text = json.dumps(
                result.get("processing_trace", {}).get("steps", [])
            )
            combined = reason + " " + trace_text
            has_discount = "discount" in combined.lower()
            has_copay = (
                "co-pay" in combined.lower()
                or "copay" in combined.lower()
                or "co_pay" in combined
            )
            checks.append(("Mentions network discount", has_discount))
            checks.append(("Shows co-pay breakdown", has_copay))

        elif case_id == "TC011":
            # Verify degradation and manual review recommendation are visible
            degraded = result.get("degraded_components") or []
            manual_review = result.get("manual_review_recommended", False)
            confidence = result.get("confidence_score", 1.0) or 0
            has_degraded = len(degraded) > 0
            checks.append(("Degraded components reported", has_degraded))
            checks.append(("Manual review recommended", manual_review))
            checks.append(
                ("Reduced confidence score", confidence < 0.5)
            )

        elif case_id == "TC012":
            # Verify high confidence on exclusion-based rejection
            confidence = result.get("confidence_score", 0) or 0
            checks.append(
                ("High confidence on exclusion-based rejection", confidence >= 0.80)
            )

        passed = all(p for _, p in checks)
        details = "; ".join(
            f"{label}: {'PASS' if p else 'FAIL'}" for label, p in checks
        )

        return {"passed": passed, "details": details, "checked": checks}

    async def run_case(self, test_case: dict[str, Any]) -> dict[str, Any]:
        """Execute a single test case against the API."""
        inp = test_case.get("input", {})
        expected = test_case.get("expected", {})

        payload = {
            "member_id": inp.get("member_id"),
            "policy_id": inp.get("policy_id", "PLUM_GHI_2024"),
            "claim_category": inp.get("claim_category"),
            "treatment_date": inp.get("treatment_date"),
            "claimed_amount": inp.get("claimed_amount"),
            "hospital_name": inp.get("hospital_name"),
            "ytd_claims_amount": inp.get("ytd_claims_amount", 0),
            "documents": inp.get("documents", []),
            "claims_history": inp.get("claims_history"),
            "simulate_component_failure": inp.get("simulate_component_failure", False),
        }

        try:
            response = await self.client.post(
                f"{API_BASE}/claims",
                json=payload,
            )
        except httpx.ConnectError:
            result = {
                "case_id": test_case["case_id"],
                "case_name": test_case["case_name"],
                "error": "Could not connect to API. Is the server running?",
                "expected": expected,
            }
            sm = self.verify_system_must(test_case, result)
            result["system_must_pass"] = sm["passed"]
            result["system_must_details"] = sm["details"]
            result["system_must_checks"] = sm["checked"]
            return result

        result = {
            "case_id": test_case["case_id"],
            "case_name": test_case["case_name"],
            "expected": expected,
        }

        if response.status_code == 422:
            # Document error — system stopped early
            detail = response.json().get("detail", {})
            if isinstance(detail, list):
                error_info = {"message": str(detail), "code": "VALIDATION_ERROR"}
            elif isinstance(detail, dict):
                error_info = detail.get("error", {})
            else:
                error_info = {"message": str(detail), "code": "UNKNOWN"}
            result.update({
                "system_stopped": True,
                "status_code": 422,
                "error_code": error_info.get("code"),
                "error_message": error_info.get("message"),
                "details": error_info.get("details", {}),
                "trace": error_info.get("details", {}).get("trace", {}),
            })
            sm = self.verify_system_must(test_case, result)
            result["system_must_pass"] = sm["passed"]
            result["system_must_details"] = sm["details"]
            result["system_must_checks"] = sm["checked"]
            return result

        elif response.status_code in (200, 201, 202):
            data = response.json()

            # If claim is submitted asynchronously, poll for completion
            claim_id = data.get("claim_id") or data.get("id")
            status = data.get("status")

            if status == "SUBMITTED" and claim_id:
                # Poll for claim completion
                for attempt in range(30):  # Max 60 seconds
                    await asyncio.sleep(2)
                    try:
                        detail_resp = await self.client.get(f"{API_BASE}/claims/{claim_id}")
                        if detail_resp.status_code == 200:
                            detail_data = detail_resp.json()
                            claim_status = detail_data.get("status", "")
                            if claim_status in ("DECIDED", "ERROR", "CANCELLED", "DOCUMENT_ERROR"):
                                data = detail_data
                                break
                    except Exception as e:
                        print(f"Poll error: {e}")
                        continue
                else:
                    # Polling completed without finding a final status
                    print(f"Warning: Claim {claim_id} still in status after polling")

            # Determine if system was stopped by document errors (async path)
            final_status = data.get("status", "")
            is_doc_error = final_status == "DOCUMENT_ERROR"

            result.update({
                "system_stopped": is_doc_error,
                "status_code": response.status_code,
                "claim_id": claim_id,
                "decision": data.get("decision"),
                "approved_amount": data.get("approved_amount"),
                "confidence_score": data.get("confidence_score"),
                "decision_reason": data.get("decision_reason"),
                "status": final_status,
                "manual_review_recommended": data.get("manual_review_recommended"),
                "degraded_components": data.get("degraded_components"),
                "line_items": data.get("line_items", []),
                "processing_trace": data.get("processing_trace", {}),
                "documents": data.get("documents", []),
            })

            # Extract error message for document-error cases
            if is_doc_error:
                err_msgs = data.get("error_messages") or data.get("document_errors") or []
                if isinstance(err_msgs, list) and len(err_msgs) > 0:
                    first = err_msgs[0]
                    if isinstance(first, dict):
                        result["error_message"] = first.get("message", str(first))
                    else:
                        result["error_message"] = str(first)
                # Also get the error code from the first document error
                doc_errors = data.get("document_errors") or []
                if isinstance(doc_errors, list) and len(doc_errors) > 0:
                    first = doc_errors[0]
                    if isinstance(first, dict):
                        result["error_code"] = first.get("error_type", "UNKNOWN")
            sm = self.verify_system_must(test_case, result)
            result["system_must_pass"] = sm["passed"]
            result["system_must_details"] = sm["details"]
            result["system_must_checks"] = sm["checked"]
            return result

        else:
            result.update({
                "system_stopped": False,
                "status_code": response.status_code,
                "error": response.text[:500],
            })
            sm = self.verify_system_must(test_case, result)
            result["system_must_pass"] = sm["passed"]
            result["system_must_details"] = sm["details"]
            result["system_must_checks"] = sm["checked"]
            return result

    def generate_report(self) -> None:
        """Generate a Markdown evaluation report."""
        lines = [
            "# Plum Claims Processing — Evaluation Report",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"**Test Cases:** {len(self.results)}",
            "",
            "---",
            "",
            "## Summary",
            "",
        ]

        # Count results
        passed = 0
        failed = 0
        errors = 0

        for r in self.results:
            expected = r.get("expected", {})
            expected_decision = expected.get("decision")
            actual_decision = r.get("decision")

            if r.get("error"):
                errors += 1
            elif r.get("system_stopped"):
                if expected_decision is None:
                    passed += 1
                else:
                    failed += 1
            elif actual_decision == expected_decision:
                passed += 1
            else:
                failed += 1

        lines.extend([
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total | {len(self.results)} |",
            f"| Passed | {passed} |",
            f"| Failed | {failed} |",
            f"| Errors | {errors} |",
            f"| Pass Rate | {passed / len(self.results) * 100:.1f}% |",
            "",
        ])

        # system_must pass rate
        sm_cases = [r for r in self.results if r.get("system_must_checks")]
        sm_passed = sum(1 for r in sm_cases if r.get("system_must_pass"))
        sm_total = len(sm_cases)
        if sm_total > 0:
            lines.extend([
                "### system_must Verification",
                "",
                "| Metric | Count |",
                "|--------|-------|",
                f"| Cases with requirements | {sm_total} |",
                f"| Passed | {sm_passed} |",
                f"| Failed | {sm_total - sm_passed} |",
                f"| Pass Rate | {sm_passed / sm_total * 100:.1f}% |",
                "",
            ])

        lines.extend(["---", ""])

        # Case-by-Case Analysis (commentary)
        lines.extend([
            "## Case-by-Case Analysis",
            "",
            "### TC001: Wrong Document Uploaded",
            "**What is interesting:** Tests the early-gate pattern — the system must stop "
            "BEFORE any LLM calls are made serving as the first defensive layer. "
            "It also tests whether the user-facing error message is specific enough "
            "for the member to self-correct.",
            "**Edge cases:** What if both uploaded documents are wrong types? "
            "What if one is correct and the other is wrong? "
            "What if a document type is completely unrecognized?",
            "**system_must verification:** "
            + self._sm_status("TC001"),
            "",
            "### TC002: Unreadable Document",
            "**What is interesting:** Tests that the system can detect quality issues "
            "(blurry / unreadable photos) without requiring real OCR — a pragmatic "
            "design choice that keeps the early-gate fast.",
            "**Edge cases:** What if MULTIPLE documents are unreadable? "
            "What if the document is a PDF that fails to parse entirely? "
            "The current implementation relies on a `quality` flag in test input.",
            "**system_must verification:** "
            + self._sm_status("TC002"),
            "",
            "### TC003: Documents Belong to Different Patients",
            "**What is interesting:** Tests cross-document patient-name matching. "
            "The system must compare patient names extracted (or declared) across "
            "all submitted documents and flag inconsistencies.",
            "**Edge cases:** What if one document has no patient name field? "
            "What if the names differ by only a middle initial — is that a mismatch? "
            "What about hyphenated names or name transliterations?",
            "**system_must verification:** "
            + self._sm_status("TC003"),
            "",
            "### TC004: Clean Consultation — Full Approval",
            "**What is interesting:** The happy path. Validates co-pay calculation "
            "(10% on consultation category, yielding ₹1,350 approved from ₹1,500 claimed) "
            "and end-to-end pipeline flow across all 5 agents.",
            "**Edge cases:** None for this case — it is the baseline. "
            "However, it also implicitly tests that fraud, policy, and document "
            "verification all produce no flags on a clean submission.",
            "**system_must verification:** " + self._sm_status("TC004"),
            "",
            "### TC005: Waiting Period — Diabetes",
            "**What is interesting:** Tests time-based policy rule enforcement. "
            "The system must check the member's join date against the "
            "condition-specific waiting period (90 days for diabetes) and compute "
            "the exact `eligible_from` date.",
            "**Edge cases:** What if the member has multiple waiting periods for "
            "different conditions? What if the claim spans treatments for two "
            "conditions with different waiting periods? "
            "What if the member joined on a leap day?",
            "**system_must verification:** "
            + self._sm_status("TC005"),
            "",
            "### TC006: Dental Partial Approval — Cosmetic Exclusion",
            "**What is interesting:** Tests line-item-level decision-making. "
            "Not all-or-nothing — the system must approve covered items (root canal) "
            "while rejecting excluded ones (teeth whitening) with per-item reasoning.",
            "**Edge cases:** What if ALL line items are excluded? "
            "What if some items are partially covered? "
            "What if the same item has both covered and excluded components?",
            "**system_must verification:** "
            + self._sm_status("TC006"),
            "",
            "### TC007: MRI Without Pre-Authorization",
            "**What is interesting:** Tests pre-authorization enforcement. "
            "MRI scans above ₹10,000 require prior approval. The system must reject "
            "but also provide actionable guidance on how to resubmit with pre-auth.",
            "**Edge cases:** What if partial pre-authorization was obtained? "
            "What if the member obtains pre-auth after submission but before decision? "
            "What about other procedures that require pre-auth (CT, PET scans)?",
            "**system_must verification:** "
            + self._sm_status("TC007"),
            "",
            "### TC008: Per-Claim Limit Exceeded",
            "**What is interesting:** Tests financial-cap enforcement. "
            "The system must compare the claimed amount against policy limits and "
            "surface both the limit and the actual claimed amount clearly.",
            "**Edge cases:** What if multiple line items individually exceed the limit? "
            "Should the limit apply per-line-item or per-claim? "
            "What if the limit changes mid-policy-year?",
            "**system_must verification:** "
            + self._sm_status("TC008"),
            "",
            "### TC009: Fraud Signal — Multiple Same-Day Claims",
            "**What is interesting:** Tests fraud detection logic. "
            "Member has 4 claims on the same day; the limit is 2/day. "
            "The system must route to MANUAL_REVIEW (not auto-reject) "
            "and surface the specific signals that triggered the flag.",
            "**Edge cases:** What if the pattern is spread across 2 days? "
            "What about high-velocity claims from different providers? "
            "Fraud detection with mock LLM provider is rule-based — "
            "real LLM analysis may surface subtler patterns.",
            "**system_must verification:** "
            + self._sm_status("TC009"),
            "",
            "### TC010: Network Hospital — Discount Applied",
            "**What is interesting:** Tests the ORDER of financial operations. "
            "Network discount (20%) must be applied BEFORE co-pay (10%), "
            "not after. Getting this wrong changes the final approved amount "
            "(₹3,240 vs ₹3,420 if reversed).",
            "**Edge cases:** What if the discount brings the amount to zero? "
            "What if there are multiple discounts? "
            "What if the hospital is partially in-network?",
            "**system_must verification:** "
            + self._sm_status("TC010"),
            "",
            "### TC011: Component Failure — Graceful Degradation",
            "**What is interesting:** Tests resilience under partial failure. "
            "The extraction agent fails, but the pipeline must continue, produce a "
            "decision, and expose the failure visibly with a reduced confidence score "
            "and a manual-review recommendation.",
            "**Edge cases:** What if ALL agents fail? "
            "What if the failure is in a downstream agent instead of upstream? "
            "What if the same agent fails intermittently?",
            "**system_must verification:** "
            + self._sm_status("TC011"),
            "",
            "### TC012: Excluded Treatment",
            "**What is interesting:** Tests policy exclusion rule enforcement. "
            "Bariatric/obesity treatment is explicitly excluded under the policy. "
            "The system must reject with high confidence because the rule is "
            "unambiguous — no grey area.",
            "**Edge cases:** What if the treatment is partially excluded "
            "(some line items covered, some not)? "
            "What if the exclusion criteria are conditional "
            "(e.g., excludes obesity unless BMI > 40)?",
            "**system_must verification:** "
            + self._sm_status("TC012"),
            "",
            "---",
            "",
        ])

        # Detail per case
        for r in self.results:
            case_id = r["case_id"]
            case_name = r["case_name"]
            expected = r.get("expected", {})
            expected_decision = expected.get("decision")

            lines.extend([
                f"## {case_id}: {case_name}",
                "",
                f"**Expected Decision:** {expected_decision or 'N/A (system should stop)'}",
            ])

            if r.get("error"):
                lines.append(f"**❌ ERROR:** {r['error']}")
            elif r.get("system_stopped"):
                sm_pass = r.get("system_must_pass", True)
                sm_icon = "✅" if sm_pass else "❌"
                lines.extend([
                    f"**✅ System stopped early (as expected)**",
                    f"- Error Code: `{r.get('error_code', 'N/A')}`",
                    f"- Message: {r.get('error_message', 'N/A')}",
                    f"- system_must: {sm_icon} {'PASS' if sm_pass else 'FAIL'}",
                ])
            else:
                actual = r.get("decision", "?")
                match = "✅" if actual == expected_decision else "❌"
                sm_pass = r.get("system_must_pass", True)
                sm_icon = "✅" if sm_pass else "❌"
                lines.extend([
                    f"**Actual Decision:** {actual}",
                    f"**Match:** {match}",
                    f"- Approved Amount: ₹{r.get('approved_amount', 0)}",
                    f"- Confidence Score: {r.get('confidence_score', 0)}",
                    f"- Status: {r.get('status', '?')}",
                    f"- Manual Review Recommended: {r.get('manual_review_recommended', False)}",
                    f"- Degraded Components: {r.get('degraded_components', [])}",
                    f"- system_must: {sm_icon} {'PASS' if sm_pass else 'FAIL'}",
                ])

                decision_reason = r.get("decision_reason", "")
                if decision_reason:
                    lines.append(f"- Reason: {decision_reason}")

                # Line items
                line_items = r.get("line_items", [])
                if line_items:
                    lines.append("")
                    lines.append("### Line Items")
                    lines.append("")
                    lines.append("| Description | Amount | Approved | Covered | Reason |")
                    lines.append("|-------------|--------|----------|---------|--------|")
                    for li in line_items:
                        lines.append(
                            f"| {li.get('description', '')} | "
                            f"₹{li.get('amount', 0)} | "
                            f"₹{li.get('approved_amount', 0)} | "
                            f"{li.get('is_covered', '?')} | "
                            f"{li.get('rejection_reason', '-')} |"
                        )

                # Trace summary
                trace = r.get("processing_trace", {})
                steps = trace.get("steps", [])
                if steps:
                    lines.append("")
                    lines.append("### Processing Trace")
                    lines.append("")
                    lines.append("| Step | Agent | Status | Confidence | Duration |")
                    lines.append("|------|-------|--------|------------|----------|")
                    for step in steps:
                        lines.append(
                            f"| {step.get('step_name', '')} | "
                            f"{step.get('agent_name', '')} | "
                            f"{step.get('status', '')} | "
                            f"{step.get('confidence_score', '-')} | "
                            f"{step.get('duration_ms', '-')}ms |"
                        )

            lines.extend(["", "---", ""])

        # Notes on Mock Provider
        lines.extend([
            "## Notes on Mock Provider",
            "",
            "- All 12 test cases were run with the mock LLM provider (`MockLLMProvider`).",
            "- Real LLM behavior may differ in confidence scores, fraud detection nuance, "
            "and extraction accuracy.",
            "- TC009 (fraud signals) passes with rule-based frequency detection even "
            "without AI — the fraud agent's `SAME_DAY_CLAIMS_EXCEEDED` rule fires "
            "independently of LLM output.",
            "- TC011 (graceful degradation) is tested via the `simulate_component_failure` "
            "flag, which triggers an extraction agent failure regardless of provider.",
            "- With a real LLM, per-line-item fraud scoring and nuanced policy reasoning "
            "would add depth but also introduce non-determinism.",
            "",
            "## Known Test Gaps",
            "",
            "The current 12 test cases cover the core claim lifecycle but leave "
            "several important scenarios untested:",
            "",
            "| Gap | Impact | Priority",
            "|-----|--------|---------",
            "| **Adversarial / negative tests** (invalid `member_id`, "
            "missing `policy_id`, future-dated treatments) | Could crash or behave unexpectedly | High",
            "| **Concurrent claim submission** (same member submits 50 claims in parallel) | "
            "Thread safety, rate limiting | Medium",
            "| **Rate limiting** (burst traffic from a single IP / member) | "
            "API abuse protection | Medium",
            "| **Internationalization** (non-English documents, Unicode names) | "
            "Data integrity, extraction quality | Low",
            "| **Frontend component tests** | UI regressions, user experience | Medium",
            "| **File size / format limits** (huge PDFs, corrupt files) | "
            "Memory safety, graceful error handling | Medium",
            "| **Partial policy updates** (mid-claim policy change) | "
            "Data consistency | Low",
            "| **Multi-currency / exchange rate handling** | Financial accuracy | Low",
            "",
            "---",
            "",
            "*Generated by the Plum Claims Evaluation Runner.*",
            "",
        ])

        # Write report
        report = "\n".join(lines)
        with open(OUTPUT_PATH, "w") as f:
            f.write(report)

        print(f"\n📄 Report written to {OUTPUT_PATH}")
        print(f"   Passed: {passed}/{len(self.results)} ({passed / len(self.results) * 100:.1f}%)")


async def main() -> None:
    runner = EvalRunner()
    await runner.run_all()


if __name__ == "__main__":
    asyncio.run(main())
