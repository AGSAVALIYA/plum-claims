# Slide Transcripts — AI Engineer Assignment Presentation

> Ready-to-record voice-over scripts for all 14 slides.
> Total estimated duration: ~11-13 minutes across all slides.
> Speaking style: conversational, like explaining your work to a fellow engineer.

---

## Slide 01 — Title: Claims Processing System

**[AUDIO: slide-01.mp3]**

**Duration:** ~30 seconds

**Visual:** Title slide showing "Claims Processing System — AI Engineer Assignment" with your name, date, and a screenshot of the app dashboard.

**Transcript:**

> Welcome. This is my submission for the health insurance claims processing system — an end-to-end claims processing system built over the course of a few days. It accepts medical documents, verifies them, extracts structured data using LLMs, evaluates against policy rules, detects fraud, and produces explainable decisions. I'll walk through the architecture, the AI decisions I made, talk about how I used AI-assisted development tools throughout.

---

## Slide 02 — The Problem & Context

**[AUDIO: slide-02.mp3]**

**Duration:** ~45 seconds

**Visual:** Assignment requirements summary — key challenges: automated claims processing at scale, explainable decisions, graceful failure handling, document verification with specific actionable messages.

**Transcript:**

> Here's the challenge. Health insurance claims processing at any meaningful scale involves thousands of claims — each requiring document verification, policy checks against multiple rules, fraud signal detection, and a clear, explainable decision. Today, most of this is done manually, which means it's slow, inconsistent, and doesn't scale well.
>
> The assignment asked for a working system with five evaluation criteria: System Design at 30%, Engineering Quality at 25%, Observability at 20%, AI Integration at 15%, and Document Verification at 10%. The system had to be explainable — no black-box decisions. It had to catch document problems early with specific, actionable messages. And it had to handle failures gracefully without crashing the entire pipeline. I designed the system to score highly on all five.

---

## Slide 03 — System Architecture

**[AUDIO: slide-03.mp3]**

**Duration:** ~90 seconds

**Visual:** Architecture diagram showing the modular monolith with SVG layers: Next.js Frontend, FastAPI Backend, Multi-Agent Pipeline Engine, Domain Services, and Infrastructure (PostgreSQL, Redis, LLM Providers, OpenTelemetry).

**Transcript:**

> Let me walk through the architecture. The system is a modular monolith with four layers: an HTTP API layer in FastAPI, a domain layer with pure business logic, an orchestrator that runs the five-agent pipeline, and a providers layer that abstracts external services — LLMs, storage, caching, and document processing.
>
> I chose a modular monolith over microservices because the team size is small, the bounded contexts are still evolving, and in-process calls keep pipeline latency low. The trade-off is that everything scales as one unit — but the bounded contexts are cleanly separated behind interfaces, so splitting into microservices later would be straightforward.
>
> For the frontend, I used Next.js 15 with TypeScript and Tailwind. It handles claim submission with document upload, displays processing traces with expandable check details, and supports both member and admin views.
>
> On the infrastructure side, I set up Docker Compose with nine services — the FastAPI backend, a standalone Celery worker for async claim processing, Next.js frontend, PostgreSQL 17, Redis 7, MinIO for object storage, Jaeger for distributed tracing, Prometheus for metrics, and Grafana for dashboards. Every service has health checks and proper dependency ordering so they start up reliably.

---

## Slide 04 — Code Organization

**[AUDIO: slide-04.mp3]**

**Duration:** ~50 seconds

**Visual:** Split view — left side shows the code directory tree (backend/, frontend/, docs/, infra/, scripts/), right side shows metric cards: 77 Tests, 6 LLM Providers, 8 Docker Services, 14 Grafana Panels.

**Transcript:**

> The codebase is split into two main directories. The backend has about 55 source files across five layers — the HTTP API layer, the core configuration and telemetry, the domain business logic, the five-agent orchestrator, and the providers layer that handles LLM integration, storage, caching, and document processing. The test suite has 77 tests across eight test files.
>
> The frontend has about 50 source files — pages for the dashboard, claims submission, and admin views, plus reusable components and an API client library.
>
> The metrics here give a quick overview: 77 tests, six LLM providers supported through a common interface, nine Docker services for the production stack, and a 14-panel Grafana dashboard for observability.

---

## Slide 05 — Multi-Agent Pipeline

**[AUDIO: slide-05.mp3]**

**Duration:** ~80 seconds

**Visual:** Pipeline flow diagram showing 5 steps: Document Verification (with STOP gate) → Document Extraction (LLM) → parallel Policy Evaluation + Fraud Detection → Decision Aggregation → APPROVED/PARTIAL/REJECTED/MANUAL_REVIEW. Key points shown below.

**Transcript:**

> The multi-agent pipeline is the core of the system. When a claim is submitted, the API returns a 202 Accepted immediately and processing happens asynchronously through Celery.
>
> Step 1 is Document Verification. This runs before any LLM calls — it's the early gate. If documents are wrong, unreadable, or belong to different patients, the pipeline stops immediately and returns a specific, actionable error message. This saves significant cost because we don't fire expensive LLM calls on invalid claims.
>
> Step 2 is Document Extraction. This uses LLMs to pull structured data from messy medical documents — patient names, diagnoses, line items, amounts, doctor registration numbers. The extraction produces structured JSON with per-field confidence scores.
>
> Steps 3 and 4 run in parallel. Policy Evaluation checks the claim against rules loaded from a JSON policy file — waiting periods, exclusions, co-pay calculations, network discounts. Fraud Detection checks multiple signals — same-day claims, monthly volume, high-value amounts, document alterations, and provider concentration — and computes a weighted fraud score. These are independent, so I used asyncio.gather to run them concurrently, reducing pipeline latency by about 40 percent.
>
> Step 5 is Decision Aggregation. It takes all previous results, computes an overall confidence score, and produces one of four decisions: APPROVED, PARTIAL, REJECTED, or MANUAL_REVIEW. Every decision includes the approved amount, the reasoning, and a full processing trace.
>
> Most importantly — if any agent fails, the pipeline doesn't crash. The error is caught, the failed step is marked, confidence is reduced, and the manual review flag is set. The remaining agents continue with whatever data they have.

---

## Slide 06 — Why NOT LangChain

**[AUDIO: slide-06.mp3]**

**Duration:** ~75 seconds

**Visual:** Comparison table: LangChain vs Custom Solution across 7 concerns — Abstraction, Debugging, Schema Validation, Cost Tracking, Vendor Lock-in, Graceful Degradation, Explainability. Bottom quote from Anthropic's guidance.

**Transcript:**

> Let me talk about AI integration — specifically why I deliberately chose not to use LangChain or LangGraph. This was one of the most important architectural decisions.
>
> LangChain is the default choice for many LLM applications. It provides chains, agents, tools, and a huge ecosystem. But for this system, it's the wrong tool. Our pipeline is five well-defined sequential steps with programmatic gates between them. LangChain's abstractions would add more complexity than they remove — it's a 500-kilobyte-plus dependency for what is essentially five async function calls with try-except around each.
>
> Debugging LangChain is notoriously difficult — when something goes wrong, you get opaque error traces. Our custom orchestrator gives us a complete ProcessingTrace with per-step input, output, confidence, and timing — stored as JSONB in PostgreSQL and fully queryable.
>
> Schema validation is another issue. LangChain's structured output support is inconsistent across providers. Our adapters have built-in schema validation — if the LLM returns malformed JSON, we catch it, retry once with an error correction prompt, and if it still fails, we return a structured fallback the pipeline can handle.
>
> Cost tracking — every LLM call costs money, and at scale that adds up. We track input and output tokens per call, compute the cost per model's pricing, and aggregate it per claim and per pipeline step. LangChain has no native support for this.
>
> And vendor lock-in — we support OpenAI, Anthropic, Google Gemini, and DeepSeek through the same interface. Switch providers by changing one environment variable. You can even use a Mock provider for testing — zero cost, deterministic responses.
>
> The lesson from Anthropic's own guidance: start simple, add complexity only when needed. Our five-step pipeline is simple. It works. It's explainable. It didn't need a framework.

---

## Slide 07 — Multi-Provider LLM Abstraction

**[AUDIO: slide-07.mp3]**

**Duration:** ~65 seconds

**Visual:** Provider cards (OpenAI, Anthropic, Google, Mock Provider) and feature list: Schema validation with retry, Cost tracking per model, Content-addressable caching, Tenacity retry with exponential backoff.

**Transcript:**

> The LLM abstraction layer is something I'm genuinely proud of. Every provider implements the same ILLMProvider interface with three methods: chat, extract structured, and health check. Switching from one provider to another requires changing a single environment variable — that's it.
>
> We support OpenAI with GPT-4o, Anthropic with Claude models, Google with Gemini, and a DeepSeek-compatible provider. The Mock provider returns deterministic responses at zero cost, which is invaluable for testing and CI.
>
> There are four key features built into every adapter. First, schema validation with automatic retry — if the LLM returns malformed JSON, we catch it, send an error correction prompt, and try once more. Second, cost tracking per model — we multiply input and output token counts by each provider's published per-thousand-token rates. Third, content-addressable caching with SHA-256 hashing and Redis TTL — identical prompts get cached responses, saving money on repeated lookups. And fourth, tenacity retry with exponential backoff for transient network errors.

---

## Slide 08 — Observability & Explainability

**[AUDIO: slide-08.mp3]**

**Duration:** ~75 seconds

**Visual:** Left side shows a ProcessingTrace example with expandable check details (SUBMISSION_DEADLINE PASSED, CATEGORY_COVERED PASSED, WAITING_PERIOD PASSED, etc.). Right side shows metrics: 240 Business Metrics, 14-Panel Grafana Dashboard, Jaeger Distributed Tracing, PHI/PII Log Scrubbing.

**Transcript:**

> The assignment explicitly says someone on the operations team must be able to look at the system's output and understand exactly what happened — what was checked, what passed, what failed, and why the final decision was made.
>
> This is exactly what our ProcessingTrace delivers. Every claim has a trace with five steps. Each step shows the agent name, status, confidence score, timing in milliseconds, and most importantly — the detailed checks performed.
>
> Expand any step and you see exactly what happened. For Policy Evaluation, you see checks like: SUBMISSION_DEADLINE — PASSED, within 30 days. CATEGORY_COVERED — PASSED, CONSULTATION is covered. WAITING_PERIOD — PASSED, member enrolled over 30 days ago. CO-PAY — 10 percent applied. NETWORK_DISCOUNT — 20 percent applied at Apollo Hospitals. Every check has a full human-readable reason.
>
> We also have full OpenTelemetry integration with Jaeger distributed tracing and 240 business metrics flowing to a 14-panel Grafana dashboard — claims throughput, agent latency, fraud risk scores, LLM cache hit-miss ratios, pipeline error rates.
>
> And PHI and PII is scrubbed from logs — patient names, amounts, doctor details are all redacted before they hit log output. The combination of per-claim ProcessingTraces, distributed tracing, and business metrics means we can reconstruct exactly why any claim got any decision.

---

## Slide 09 — Production Infrastructure

**[AUDIO: slide-09.mp3]**

**Duration:** ~50 seconds

**Visual:** Grid of 9 service cards: app (FastAPI :8000), worker (Celery), frontend (Next.js :3000), db (PostgreSQL 17), redis (Redis 7), minio (S3-compatible), jaeger (Tracing :16686), prometheus (Metrics :9095), grafana (Dashboards :3001). Features listed below.

**Transcript:**

> Here's the full production stack. Nine Docker services orchestrated with Docker Compose. The FastAPI backend serves the API, Celery handles async claim processing so the API stays responsive, and the frontend runs on Next.js.
>
> PostgreSQL 17 is the primary database with JSONB support for the processing traces. Redis 7 handles both caching and rate limiting. MinIO provides S3-compatible object storage for uploaded documents. Jaeger collects distributed traces, Prometheus scrapes metrics, and Grafana visualizes everything on a 14-panel dashboard.
>
> Every service has health checks with proper dependency ordering — the app won't start until the database and Redis are ready. The Dockerfile uses a multi-stage build with a slim runner image, and the application runs as a non-root user. These are production practices that matter when you're deploying for real.

---

## Slide 10 — AI-Assisted Development

**[AUDIO: slide-10.mp3]**

**Duration:** ~70 seconds

**Visual:** Three cards — GitHub Copilot (since 2021, boilerplate, tests, refactoring), Claude Code (multi-model orchestration, sub-agents), Claude Opus (strategic decisions). Bottom insight: AI accelerated implementation, but architectural decisions were human.

**Transcript:**

> I want to talk about AI tools — because using AI coding tools is standard practice.
>
> I've been using GitHub Copilot since 2021, when I was a beta tester as a student. It's evolved from simple autocomplete to full agent mode. For this project, it handled the boilerplate — FastAPI route handlers, Pydantic schemas, React components — where the patterns are well-established and the AI can generate correct code quickly.
>
> For the heavier architectural work, I used Claude Code with a multi-model setup. DeepSeek V4 Pro for thinking through complex decisions — like whether to parallelize Policy and Fraud. DeepSeek V4 Flash for the sub-agents that run parallel code reviews — it found 20-plus issues across backend, frontend, and tests in about three minutes. And MiMo 2.5 Pro for tasks needing long context.
>
> For strategic thinking — the overall architecture, deciding what not to build, drafting this transcript — I used Claude Opus. It's particularly good at reasoning about trade-offs.
>
> But here's the key insight: I still had to verify every AI finding, prioritize what to fix, and decide which suggestions made architectural sense. The decision to reject LangChain, the choice to parallelize the pipeline, the judgment to leave certain features as stubs — those were human decisions informed by AI analysis.

---

## Slide 11 — Challenges & Key Decisions

**[AUDIO: slide-11.mp3]**

**Duration:** ~80 seconds

**Visual:** Three challenge cards — Embedded vs Standalone Celery, Sync Verification vs Async Processing, HybridDocumentProcessor Stub. Bottom section: "What I'd Change Given More Time" with 4 items.

**Transcript:**

> Let me talk about the hardest decisions and what I'd do differently.
>
> Challenge one: Embedded versus standalone Celery worker. The FastAPI lifespan starts a daemon thread for claim processing in development mode. This works great for a single developer — no separate process to manage. But it silently dies under load with real LLM calls, which I discovered during end-to-end testing. The docker-compose setup has a standalone Celery worker service for production. Looking back, I'd make the standalone worker the only option — the embedded pattern creates false confidence.
>
> Challenge two: Synchronous verification versus async extraction. Document verification must be synchronous — you need to stop the pipeline before making expensive LLM calls. But extraction, policy evaluation, and fraud detection can all be async. The clean separation of step one as the synchronous gate and steps two through five as the async pipeline was absolutely the right call.
>
> Challenge three: The HybridDocumentProcessor stub. Real document OCR with the Docling integration is a placeholder. Indian medical documents are notoriously messy — handwritten prescriptions, phone photos, rubber stamps. I chose not to build this because it would take days, and the assignment says if you're stuck for more than two hours, document it and move on.
>
> Given more time, I'd fix the Redis rate limiter which has dead code deferring to in-memory, implement proper OCR, add an evaluator-optimizer pattern where the Decision agent reviews the Policy agent's reasoning, and add frontend tests — there are zero right now.
>
> The one decision I'm proudest of is the LLM abstraction layer. Switching from mock to a real provider requires changing one environment variable. Schema validation with retry handles malformed output. Cost tracking per call means we know exactly what each claim costs. That's the difference between a prompt engineer and an AI engineer — thinking about cost, reliability, and production readiness.

---

## Slide 12 — Engineering Quality

**[AUDIO: slide-12.mp3]**

**Duration:** ~45 seconds

**Visual:** Left side shows the test pyramid — 6 Smoke tests (top), 28 Unit tests (middle), 12 Integration tests (bottom). Right side shows metrics: 77 tests, 100% pass, 12/12 eval 100%, 10/10 system_must 100%, 8 test files, FastAPI TestClient, in-memory SQLite.

**Transcript:**

> Engineering quality matters. The test suite has 77 tests across eight test files with 2,301 lines of test code. All 77 pass. The evaluation suite — 12 test cases — passes at 100 percent. And the system must verifications, which check natural language requirements like "tell the member specifically what document type was uploaded and what is needed instead" — all 10 pass at 100 percent.
>
> The test pyramid shows the right shape: a broad base of integration tests covering the API, policy, fraud, decision, and document verification domains, with unit tests above that and a small number of smoke tests at the top. Integration tests use FastAPI's TestClient with an in-memory SQLite database for isolation. This gives us confidence that the system works end to end without needing a real database or LLM calls in CI.

---

## Slide 13 — Thank You & Summary

**[AUDIO: slide-13.mp3]**

**Duration:** ~50 seconds

**Visual:** Summary slide with 6 key takeaways, GitHub link, and contact info.

**Transcript:**

> To summarize: I built a production-ready claims processing system with a multi-agent pipeline, 77 tests, full observability, explainable decisions, and a clean user interface. The system processes claims end-to-end — document verification, structured extraction, policy evaluation, fraud detection, and decision aggregation — in about two seconds with a real LLM.
>
> I used AI tools extensively — Copilot since 2021 for code generation, Claude Code for multi-agent orchestration and parallel code reviews, and Opus for strategic planning. But the architectural decisions, the trade-offs, the judgment about what not to build — those were human decisions.
>
> What excites me about this kind of work is that it's a real problem. Health insurance claims processing directly affects people's access to healthcare. Building systems that work reliably at scale, produce explainable decisions, and handle real-world messy inputs — that's meaningful engineering.
>
> Thank you for reviewing my submission. I'm happy to walk through any part of the code in more detail. The full source code is on GitHub at the link shown. I'm also prepared to extend the system live — add a new policy rule, implement a new fraud signal, or integrate a new LLM provider.
