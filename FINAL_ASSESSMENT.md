# Plum AI Engineer Assignment — Final Assessment Report

> **Generated:** 2026-06-15
> **Scope:** Full codebase audit against assignment + web research for AI Engineer role competitiveness

---

## Executive Summary

Your system is **well-built and most review items are already addressed**. The multi-agent architecture, 12/12 test cases passing, production observability stack (OpenTelemetry, Jaeger, Prometheus, Grafana), and clean DDD code organization form a solid foundation. 

**Current estimated score: ~8.5/10** (after fixes applied). With the 5 standout improvements below, you can push to **~9.5/10**.

---

## What's Already Fixed ✅ (from review.md)

| # | Fix | Status |
|---|-----|--------|
| 1 | Docker compose: worker + frontend added | ✅ |
| 2 | Architecture doc: has "why", trade-offs, 10x scalability | ✅ |
| 3 | TC005: REJECTED claims show ₹0 approved_amount | ✅ |
| 4 | Document verification: consolidated MISSING_REQUIRED checks | ✅ |
| 5 | Frontend: USER_FRIENDLY_ERROR_MESSAGES for document errors | ✅ |
| 6 | Frontend: auto-polling for in-progress claims | ✅ |
| 7 | Frontend: retry button sends documents + comment | ✅ |
| 8 | Admin: currency is INR (en-IN) | ✅ |
| 9 | AI confidence: dynamic (0.70-0.88 based on reasoning quality) | ✅ |
| 10 | OpenAI adapter: schema validation + retry on failure | ✅ |
| 11 | Redis rate limiter: documented ZREMRANGEBYSCORE approach | ✅ |
| 12 | Component contracts: precise and comprehensive | ✅ |
| 13 | Policy agent: detailed check reasons (WAITING_PERIOD, EXCLUSIONS, etc.) | ✅ |
| 14 | Decision agent: detailed check reasoning | ✅ |
| 15 | Fraud agent: AI-powered fraud analysis | ✅ |
| 16 | checks_performed stored in DB per processing step | ✅ |

---

## 5 Standout Improvements to Differentiate You

Based on web research into what impresses technical reviewers for AI Engineer roles (see `web_research/` folder for full research):

### 🥇 #1: Parallelize Policy + Fraud Agents (1 hour)

**Why it stands out:** Anthropic's "Building Effective Agents" specifically recommends parallelization of independent subtasks. Policy and Fraud agents are completely independent — they both consume extraction output but don't depend on each other. Running them with `asyncio.gather` shows you understand agent dependency graphs and can optimize latency.

**Where:** `backend/orchestrator/engine.py`, lines ~200-280

**Current:** Sequential flow — Policy → Fraud
**Target:** `policy_result, fraud_result = await asyncio.gather(policy_agent.execute(context), fraud_agent.execute(context))`

**Impact:** ~40% latency reduction for pipeline middle steps, signals architectural sophistication.

---

### 🥈 #2: Surface Rich Reasoning in Frontend Traces (2 hours)

**Why it stands out:** The assignment's Observability criterion (20%) says: *"someone on the operations team must be able to look at the system's output and understand exactly what happened — what was checked, what passed, what failed, and why."*

Your agents already produce detailed `checks` with `reason` fields like:
```
WAITING_PERIOD check FAILED: Claim falls within diabetes_90_day. 
Member joined 2024-09-01, treatment on 2024-10-15. 
Eligible from 2024-12-01.
```

But the frontend just shows a flat table with agent name + confidence. **The data is there; it just isn't displayed.**

**What to build:** An expandable accordion/stepper for each processing step. Click "Policy Evaluation" → see all checks with ✅/❌ icons and full reasoning text. This directly addresses the #1 evaluation criterion.

**Where:** `frontend/src/app/claims/[id]/page.tsx` — transform the flat processing trace table into expandable step cards.

---

### 🥉 #3: Add Cost Tracking Per LLM Call (30 min)

**Why it stands out:** At 75,000 claims/year with 5 LLM calls each, cost matters. Showing you track it demonstrates business awareness that separates AI Engineers from prompt engineers.

**Implementation:** In each adapter's `chat()` method, count input/output tokens. Store in `LLMResponse.usage`. Aggregate per claim in the orchestrator. Add a "Cost: ₹X.XX" line to the trace.

**Where:** `backend/providers/llm/` adapters + `backend/orchestrator/engine.py`

**Model costs (approximate):**
| Model | Input/1K tokens | Output/1K tokens |
|-------|-----------------|-------------------|
| GPT-4o | $0.0025 | $0.010 |
| Claude Sonnet | $0.003 | $0.015 |
| DeepSeek V4 | $0.001 | $0.004 |

At 75K claims × ~3K input + ~500 output per call × 5 calls = ~$2,000-$5,000/month.

---

### 4️⃣ #4: Add Eval Report Commentary (1 hour)

**Why it stands out:** The eval report currently just shows pass/fail. Adding per-case analysis shows you think critically about your system's behavior, not just whether it passes tests.

**What to add per test case:**
- What was interesting about this case
- Edge cases encountered
- Note that tests run with mock provider (real LLM may differ)
- Verify `system_must` text requirements (e.g., TC001 requires specific error messages)
- Discussion of TC009 (fraud detection limitations with mock)
- Edge cases NOT covered by the 12 test cases

**Where:** `eval_report.md`

---

### 5️⃣ #5: Record the Demo Video (1-2 hours)

**Why it stands out:** This is a REQUIRED deliverable. Not having it is a guaranteed deduction.

**Required content (per assignment):**
1. A claim stopped early due to document problems (show specific error message) — use TC001
2. A successful end-to-end approval with full trace visible — use TC004
3. One technical decision you're genuinely proud of
4. One thing you'd change given more time

**Tip:** If you implement #2 (rich trace view), the video will be MUCH more impressive.

---

## Priority Matrix

| Priority | Task | Impact | Effort | Est. Score Gain |
|----------|------|--------|--------|-----------------|
| 🔴 P0 | Record demo video | Required deliverable | 1-2 hrs | — |
| 🔴 P0 | Surface rich reasoning in frontend traces | +0.5-1.0 pts | 2 hrs | +1.5 |
| 🟡 P1 | Parallelize Policy + Fraud agents | +0.3-0.5 pts | 1 hr | +0.5 |
| 🟡 P1 | Add cost tracking per LLM call | +0.2-0.3 pts | 30 min | +0.2 |
| 🟡 P1 | Add eval report commentary | +0.3 pts | 1 hr | +0.3 |
| 🟢 P2 | LLM Provider fallback (primary → secondary) | +0.2 pts | 1 hr | +0.2 |
| 🟢 P2 | Few-shot examples in extraction prompts | +0.2 pts | 30 min | +0.2 |
| 🟢 P2 | Frontend tests (at least smoke tests) | +0.2 pts | 2 hrs | +0.2 |
| 🟢 P3 | Add known limitations to README | +0.1 pts | 15 min | +0.1 |
| 🟢 P3 | Per-field extraction confidence | +0.2 pts | 1 hr | +0.2 |

---

## What NOT to Do (Avoid Over-Engineering)

Based on Anthropic's principle "start simple, add complexity only when needed":

| ❌ Don't | ✅ Instead |
|----------|-----------|
| Add LangChain/LangGraph | Your 5-step pipeline is clean enough |
| Build real Docling PDF OCR integration | Document the limitation honestly |
| Add vector database for document search | Not in assignment scope |
| Add real-time websocket updates | Polling every 3s is sufficient |
| Add Kubernetes manifests | Docker compose is fine for this stage |
| Build a model fine-tuning pipeline | Not an ML Engineer role |
| Add multi-language support | English + Hindi recognition is enough |

---

## Score Projection

| Criteria | Weight | Current | After P0/P1 | Max Possible |
|----------|--------|---------|-------------|--------------|
| System Design | 30% | 8.5 | 9.5 | 10 |
| Engineering Quality | 25% | 8.0 | 8.5 | 10 |
| Observability | 20% | 7.5 | 9.5 | 10 |
| AI Integration | 15% | 8.0 | 8.5 | 10 |
| Document Verification | 10% | 8.5 | 9.0 | 10 |
| **Weighted Total** | — | **~8.1** | **~9.1** | 10 |

---

## Web Research Saved

All research findings are saved in `/workspace/web_research/`:
- `01-ai-engineer-market-2025.md` — Job market trends, what impresses recruiters
- `02-production-ai-patterns.md` — Anthropic's agent patterns, production best practices
- `03-healthcare-ai-insights.md` — Healthcare AI trends, Plum-specific insights

These can be reused by other LLM tools for future improvements.

---

## Summary

Your system is already strong. The 16 fixes from `review.md` brought it from ~7.4 to ~8.1/10. To push to 9.0+, focus on:

1. **Demo video** (required deliverable)
2. **Surface rich reasoning in traces** (directly addresses assignment's #1 criterion)
3. **Parallelize Policy + Fraud** (signals architectural sophistication)
4. **Cost tracking** (signals production/business awareness)
5. **Eval report commentary** (signals critical thinking)

Avoid over-engineering. The system already has: multi-agent architecture, 12/12 tests passing, OpenTelemetry observability, schema validation with retry, dynamic confidence, graceful degradation, and comprehensive policy rules. These are exactly what an AI Engineer portfolio should demonstrate.

The key insight from web research: **reviewers want to see that you built the RIGHT system, not the most complex one.** Your clean 5-agent pipeline with proper interfaces is exactly that. Now make the reasoning visible and record the demo.
