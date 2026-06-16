# Production AI Patterns — What Impresses Technical Reviewers

> **Source:** Anthropic "Building Effective Agents" (Dec 2024), Lilian Weng "LLM Powered Autonomous Agents", Arize AI
> **Date:** June 2026

---

## Anthropic's Core Workflow Patterns

### 1. Prompt Chaining (✅ Your system does this)
Decompose task into sequential steps where each LLM call processes the output of the previous one. Add programmatic checks (gates) between steps.

**Your system:** Verification → Extraction → Policy → Fraud → Decision

### 2. Routing
Classify input and direct to specialized followup. Use cheaper models for simple cases.

**Not yet implemented.** Could route simple claims to cheaper LLM, complex to expensive.

### 3. Parallelization (⚠️ Should add)
Run independent subtasks simultaneously.
- **Sectioning:** Policy and Fraud agents are independent — run them in parallel
- **Voting:** Run multiple fraud checks and aggregate

### 4. Orchestrator-Workers
Central LLM breaks down tasks, delegates to workers, synthesizes results.

**Not needed for your use case** — your 5-step pipeline has fixed subtasks.

### 5. Evaluator-Optimizer (💡 Could add)
One LLM generates, another evaluates and provides feedback in a loop.

**Potential use:** Policy agent generates decision, evaluator LLM reviews it for correctness before finalizing.

---

## Three Core Principles (Anthropic)

1. **Maintain simplicity in agent's design** — ✅ Your pipeline is clean
2. **Prioritize transparency** — ⚠️ Your traces need richer reasoning
3. **Carefully craft agent-computer interface (ACI)** — ✅ Clean provider interfaces

---

## What Technical Reviewers Look For

| Pattern | Implemented? | Priority |
|---------|-------------|----------|
| Structured output with schema validation | ✅ (with retry) | Critical |
| Graceful degradation on component failure | ✅ | Critical |
| Confidence scores that degrade realistically | ⚠️ (improved but could be better) | High |
| Cost tracking per LLM call | ❌ | Medium |
| A/B testing framework for LLM providers | ❌ | Low |
| Few-shot examples in prompts | ⚠️ | Medium |
| Human-in-the-loop for edge cases | ⚠️ (MANUAL_REVIEW exists) | Medium |
| Evaluation framework (not just pass/fail) | ❌ | High |
| Traces with detailed reasoning per step | ⚠️ (checks exist, not surfaced) | Critical |
| Audit trail for every decision | ✅ (ProcessingTrace) | Critical |

---

## Actionable Recommendations

1. **Parallelize Policy + Fraud agents** — 40% latency improvement, shows architectural thinking
2. **Add evaluation metrics per agent** — precision, recall, latency, cost
3. **Track LLM token costs** — simple: count tokens × price per model
4. **Add AI confidence per check, not just overall** — granularity impresses
5. **Surface rich reasoning in traces** — make every check human-readable
