# Complete GitHub issue roadmap

Plan IDs P01–P28 are stable. Dependencies refer to these IDs; links below point to the created GitHub issues. Every issue includes the shared [Definition of Done](development.md).

## Ownership and sequence

| Plan ID | Issue | Owner | Dependencies |
|---|---|---|---|
| [P01 / #1](https://github.com/voltrox007/placement-preparation-agent/issues/1) | Review the documented baseline and establish repository workflow | @voltrox007 | None |
| [P02 / #2](https://github.com/voltrox007/placement-preparation-agent/issues/2) | Establish Python tooling, configuration, and CI | @SakshamSekhri | [P01 / #1](https://github.com/voltrox007/placement-preparation-agent/issues/1) |
| [P03 / #3](https://github.com/voltrox007/placement-preparation-agent/issues/3) | Define typed domain contracts and credit policies | @vidhimahajan06 | [P02 / #2](https://github.com/voltrox007/placement-preparation-agent/issues/2) |
| [P04 / #4](https://github.com/voltrox007/placement-preparation-agent/issues/4) | Implement SQLite schema, migrations, and repositories | @voltrox007 | [P03 / #3](https://github.com/voltrox007/placement-preparation-agent/issues/3) |
| [P05 / #5](https://github.com/voltrox007/placement-preparation-agent/issues/5) | Verify Azure compatibility and register a persistent Foundry agent | @vidhimahajan06 | P02, P03 |
| [P06 / #6](https://github.com/voltrox007/placement-preparation-agent/issues/6) | Build single-request agent execution and budget enforcement | @vidhimahajan06 | P03, P04, P05 |
| [P07 / #7](https://github.com/voltrox007/placement-preparation-agent/issues/7) | Build Streamlit navigation and student identity boundary | @SakshamSekhri | [P04 / #4](https://github.com/voltrox007/placement-preparation-agent/issues/4) |
| [P08 / #8](https://github.com/voltrox007/placement-preparation-agent/issues/8) | Implement student profiles, goals, and availability | @voltrox007 | P03, P04, P07 |
| [P09 / #9](https://github.com/voltrox007/placement-preparation-agent/issues/9) | Implement one-shot resume ingestion and confirmation | @SakshamSekhri | P06, P08 |
| [P10 / #10](https://github.com/voltrox007/placement-preparation-agent/issues/10) | Add skill taxonomy, role templates, and JD confirmation | @SakshamSekhri | P06, P08 |
| [P11 / #11](https://github.com/voltrox007/placement-preparation-agent/issues/11) | Implement bounded public GitHub evidence snapshots | @SakshamSekhri | P06, P09 |
| [P12 / #12](https://github.com/voltrox007/placement-preparation-agent/issues/12) | Create reviewed questions, rubrics, and activity catalogs | @Jiya-garg08 | P03, P10 |
| [P13 / #13](https://github.com/voltrox007/placement-preparation-agent/issues/13) | Implement objective diagnostic sessions and scoring | @Jiya-garg08 | P07, P10, P12 |
| [P14 / #14](https://github.com/voltrox007/placement-preparation-agent/issues/14) | Implement one-shot rubric evaluation and batch contracts | @Jiya-garg08 | P06, P12, P13 |
| [P15 / #15](https://github.com/voltrox007/placement-preparation-agent/issues/15) | Implement evidence aggregation and skill-state history | @voltrox007 | P10, P13, P14 |
| [P16 / #16](https://github.com/voltrox007/placement-preparation-agent/issues/16) | Build versioned knowledge ingestion and embedding cache | @vidhimahajan06 | P02, P03, P10 |
| [P17 / #17](https://github.com/voltrox007/placement-preparation-agent/issues/17) | Implement single-pass retrieval and citation resolution | @vidhimahajan06 | P05, P16 |
| [P18 / #18](https://github.com/voltrox007/placement-preparation-agent/issues/18) | Build explicit single-question grounded learning help | @vidhimahajan06 | P06, P07, P17 |
| [P19 / #19](https://github.com/voltrox007/placement-preparation-agent/issues/19) | Implement deterministic gaps and seven-day scheduling | @voltrox007 | P10, P12, P15 |
| [P20 / #20](https://github.com/voltrox007/placement-preparation-agent/issues/20) | Add optional one-shot plan and recommendation explanations | @vidhimahajan06 | P06, P19 |
| [P21 / #21](https://github.com/voltrox007/placement-preparation-agent/issues/21) | Build practice submissions and one-shot static code feedback | @SakshamSekhri | P12, P14, P15, P19 |
| [P22 / #22](https://github.com/voltrox007/placement-preparation-agent/issues/22) | Prepare reusable project-viva question batches | @Jiya-garg08 | P09, P11, P12, P14 |
| [P23 / #23](https://github.com/voltrox007/placement-preparation-agent/issues/23) | Implement fixed mock interviews with one final feedback report | @Jiya-garg08 | P12, P14, P15, P22 |
| [P24 / #24](https://github.com/voltrox007/placement-preparation-agent/issues/24) | Build progress views and deterministic adaptation | @voltrox007 | P15, P20, P21, P23 |
| [P25 / #25](https://github.com/voltrox007/placement-preparation-agent/issues/25) | Implement privacy, deletion, and injection defenses | @Jiya-garg08 | P09, P11, P18, P24 |
| [P26 / #26](https://github.com/voltrox007/placement-preparation-agent/issues/26) | Measure quality, credit consumption, and resilience | @Jiya-garg08 | P18, P20, P23, P24 |
| [P27 / #27](https://github.com/voltrox007/placement-preparation-agent/issues/27) | Package and deploy an authenticated single-host demo | @SakshamSekhri | P25, P26 |
| [P28 / #28](https://github.com/voltrox007/placement-preparation-agent/issues/28) | Verify recovery and deliver the final group demo | @voltrox007 | [P27 / #27](https://github.com/voltrox007/placement-preparation-agent/issues/27) |

## P01 — Review the documented baseline and establish repository workflow

- **Owner:** @voltrox007
- **Phase:** 1; **area:** planning
- **Objective:** Make the revised blueprint the team's implementation baseline.
- **Why:** Prevent scope drift and establish shared completion rules.
- **Dependencies:** None; repository initialization is already underway.
- **Inputs:** Published blueprint and owner-approved scope.
- **Outputs:** Reviewed baseline and contribution workflow.
- **Expected files/modules:** `README.md`, `docs/blueprint.md`, `docs/development.md`, `docs/team.md`, `.github/`

### Tasks and subtasks

- [ ] Review revision 1.1 and its credit-policy changes with all members.
- [ ] Confirm labels, milestones, ownership, PR/issue templates and dependency workflow.
- [ ] Record remaining decisions and the baseline version; distinguish existing setup from implementation.

### Acceptance criteria

- [ ] Mandatory persistent Foundry agent and one-shot interaction policy are explicit.
- [ ] All 28 issues have owners and dependencies; teammates know invitation status.

### Testing requirements

- Check documentation links and templates; confirm issue metadata.

### Definition of Done

Team review and baseline decisions recorded; no application feature work included. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P02 — Establish Python tooling, configuration, and CI

- **Owner:** @SakshamSekhri
- **Phase:** 1; **area:** foundation
- **Objective:** Make the future application environment reproducible.
- **Why:** Catch configuration and quality failures early.
- **Dependencies:** P01
- **Inputs:** Architecture and environment settings.
- **Outputs:** Reproducible developer setup.
- **Expected files/modules:** `pyproject.toml`, `dependency lockfile`, `src/placement_agent/config.py`, `.env.example`, `.github/workflows/`, `docs/setup.md`

### Tasks and subtasks

- [ ] Choose compatible Python/package versions and a lockfile.
- [ ] Add configuration validation, lint/type checks, offline test CI.
- [ ] Document clean-environment setup and secret handling.

### Acceptance criteria

- [ ] Fresh setup runs checks successfully.
- [ ] Missing configuration fails clearly; live AI is disabled without explicit budgets.
- [ ] CI does not invoke paid models by default.

### Testing requirements

- Configuration boundaries and clean-environment CI smoke test.

### Definition of Done

Setup verified and dependency versions pinned. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P03 — Define typed domain contracts and credit policies

- **Owner:** @vidhimahajan06
- **Phase:** 1; **area:** foundation
- **Objective:** Define shared contracts for every service and AI task.
- **Why:** Avoid incompatible component assumptions and uncontrolled calls.
- **Dependencies:** P02
- **Inputs:** Blueprint and schema design.
- **Outputs:** Validated shared models.
- **Expected files/modules:** `src/placement_agent/domain/`, `tests/unit/`, `docs/data-model.md`

### Tasks and subtasks

- [ ] Define profile, evidence, plan, evaluation and interview-batch schemas.
- [ ] Define workflow statuses, version fields and typed errors.
- [ ] Define one-request action policy and usage-reservation contract.

### Acceptance criteria

- [ ] Out-of-range scores/durations and malformed batches are rejected.
- [ ] Unknown IDs are resolved/validated at service boundaries.
- [ ] No contract implies automatic conversation continuation.

### Testing requirements

- Boundary values, malformed payloads, interview item alignment.

### Definition of Done

Contracts and examples reviewed by downstream owners. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P04 — Implement SQLite schema, migrations, and repositories

- **Owner:** @voltrox007
- **Phase:** 1; **area:** data
- **Objective:** Build authoritative, transactional student persistence.
- **Why:** Prevent data corruption and duplicate paid operations.
- **Dependencies:** P03
- **Inputs:** Typed contracts and database design.
- **Outputs:** Working repository layer.
- **Expected files/modules:** `src/placement_agent/db/`, `migrations/`, `tests/integration/`

### Tasks and subtasks

- [ ] Create schema/migrations including evaluation_batches and usage_reservations.
- [ ] Enable foreign keys, local WAL, busy timeout and scoped repositories.
- [ ] Add unique request keys and optimistic state versions.

### Acceptance criteria

- [ ] Empty DB migrates; ownership and uniqueness enforced.
- [ ] Usage reservations and attempt writes are atomic.
- [ ] External calls do not hold long database transactions.

### Testing requirements

- Migrations, rollback-on-error, constraints, concurrent duplicate operations.

### Definition of Done

Database foundation passes integration checks. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P05 — Verify Azure compatibility and register a persistent Foundry agent

- **Owner:** @vidhimahajan06
- **Phase:** 2; **area:** agent
- **Objective:** Verify the mandatory agent before dependent development.
- **Why:** Resolve region, model, SDK, access and credit constraints early.
- **Dependencies:** P02, P03
- **Inputs:** Approved Azure access and configured limits.
- **Outputs:** Verified persistent agent invocation.
- **Expected files/modules:** `src/placement_agent/agent/client.py`, `scripts/`, `docs/setup.md`

### Tasks and subtasks

- [ ] Confirm authorized Azure configuration and usage allowance before provisioning.
- [ ] Choose/pin compatible SDK/model and register versioned prompt agent.
- [ ] Run one bounded response smoke test through the persistent agent reference; record measured usage.

### Acceptance criteria

- [ ] Result identifies agent resource/version.
- [ ] Single response request is observed; SDK automatic model retries are disabled.
- [ ] No MCP or tool loop is required for acceptance.

### Testing requirements

- Offline adapter tests and one explicit budget-checked live smoke test.

### Definition of Done

Supported API path and measured usage documented. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P06 — Build single-request agent execution and budget enforcement

- **Owner:** @vidhimahajan06
- **Phase:** 2; **area:** agent
- **Objective:** Implement explicit, bounded AI actions.
- **Why:** Protect limited credits and prevent hidden model calls.
- **Dependencies:** P03, P04, P05
- **Inputs:** Task contract and trusted context.
- **Outputs:** Validated result or durable pending/failure status.
- **Expected files/modules:** `src/placement_agent/agent/{orchestrator,context,budget}.py`, `src/placement_agent/telemetry.py`

### Tasks and subtasks

- [ ] Add task modes, context limits, schema validation and sanitized run records.
- [ ] Implement atomic budget reservations and input/version-scoped cached reports.
- [ ] Prevent automatic retries/repair/tool loops; reconcile uncertain timeouts conservatively.
- [ ] Make explicit retries new budget-checked actions.

### Acceptance criteria

- [ ] At most one outbound model response request per explicit action.
- [ ] Concurrent duplicates reuse an operation; exhausted budget denies before provider access.
- [ ] Invalid JSON does not trigger repair or state change.

### Testing requirements

- Actual request counts, SDK retry behavior, concurrency, malformed output, ambiguous timeout.

### Definition of Done

Credit-policy suite passes with preserved submissions on failure. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P07 — Build Streamlit navigation and student identity boundary

- **Owner:** @SakshamSekhri
- **Phase:** 1; **area:** ui
- **Objective:** Create safe student-scoped UI foundations.
- **Why:** Support workflow pages without leaking data or triggering paid reruns.
- **Dependencies:** P04
- **Inputs:** Student identity and persisted state.
- **Outputs:** Navigable scoped interface.
- **Expected files/modules:** `app.py`, `src/placement_agent/ui/`, `src/placement_agent/bootstrap.py`

### Tasks and subtasks

- [ ] Add navigation/bootstrap and synthetic local identity.
- [ ] Scope service requests to authenticated student context.
- [ ] Keep UI state temporary; prevent side effects during render/rerun.

### Acceptance criteria

- [ ] Two synthetic students cannot access each other's records.
- [ ] Page rerun creates no writes or model requests without explicit action.

### Testing requirements

- UI smoke, ownership, rerun/double-click checks.

### Definition of Done

Page shell works with scoped test data. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P08 — Implement student profiles, goals, and availability

- **Owner:** @voltrox007
- **Phase:** 3; **area:** data
- **Objective:** Capture preparation constraints.
- **Why:** Make recommendations relevant and feasible.
- **Dependencies:** P03, P04, P07
- **Inputs:** Student-entered facts and availability.
- **Outputs:** Confirmed profile and active goal.
- **Expected files/modules:** `src/placement_agent/services/profiles.py`, `src/placement_agent/ui/pages/`, `src/placement_agent/db/`

### Tasks and subtasks

- [ ] Build profile/goal forms and correction flow.
- [ ] Validate deadlines, time budgets and one active goal.
- [ ] Persist preferences and state revisions.

### Acceptance criteria

- [ ] Profile editing incurs zero model calls.
- [ ] Saved goals survive restart and capacity rules hold.

### Testing requirements

- Validation, persistence, active-goal uniqueness, revisions.

### Definition of Done

Returning student recovers confirmed goal. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P09 — Implement one-shot resume ingestion and confirmation

- **Owner:** @SakshamSekhri
- **Phase:** 3; **area:** integration
- **Objective:** Extract inspectable resume facts.
- **Why:** Use resumes as claims with provenance, not automatic mastery.
- **Dependencies:** P06, P08
- **Inputs:** Resume PDF or pasted text.
- **Outputs:** Confirmed facts and source references.
- **Expected files/modules:** `src/placement_agent/integrations/document_parser.py`, `src/placement_agent/services/profiles.py`, `src/placement_agent/agent/prompts/`, `src/placement_agent/ui/pages/`

### Tasks and subtasks

- [ ] Validate PDF/text size/type and parse bounded text.
- [ ] Request one extraction only on explicit submission; cache by document/version.
- [ ] Present source-linked draft and require confirmation/correction; handle scanned/invalid PDFs.

### Acceptance criteria

- [ ] Unconfirmed facts do not become trusted state.
- [ ] At most one extraction response per action; reopen/confirmation costs zero calls.

### Testing requirements

- Malformed/oversized/empty/scanned inputs, injected instructions, duplicate upload.

### Definition of Done

Confirmed facts trace to source text. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P10 — Add skill taxonomy, role templates, and JD confirmation

- **Owner:** @SakshamSekhri
- **Phase:** 3; **area:** content
- **Objective:** Create explicit target requirements.
- **Why:** Avoid invented role expectations and invalid prerequisite graphs.
- **Dependencies:** P06, P08
- **Inputs:** Role template or pasted job description.
- **Outputs:** Versioned goal requirements.
- **Expected files/modules:** `content/roles/`, `src/placement_agent/domain/policies.py`, `src/placement_agent/services/profiles.py`

### Tasks and subtasks

- [ ] Seed initial role/skill taxonomy and aliases.
- [ ] Validate prerequisite acyclicity and requirement versions.
- [ ] Add optional one-shot JD extraction with student confirmation.

### Acceptance criteria

- [ ] Template selection costs zero calls; optional JD extraction is explicit and bounded.
- [ ] Unknown mappings are reviewable; requirements retain provenance.

### Testing requirements

- Aliases, cycles, ambiguous requirements, confirmed snapshot stability.

### Definition of Done

Goal requirements independent of later template changes. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P11 — Implement bounded public GitHub evidence snapshots

- **Owner:** @SakshamSekhri
- **Phase:** 3; **area:** integration
- **Objective:** Gather project context with precise provenance.
- **Why:** Ground project feedback without unsafe execution or broad scraping.
- **Dependencies:** P06, P09
- **Inputs:** Approved public repository.
- **Outputs:** Bounded source-linked snapshot.
- **Expected files/modules:** `src/placement_agent/integrations/github.py`, `src/placement_agent/db/`, `src/placement_agent/ui/pages/`

### Tasks and subtasks

- [ ] Validate public GitHub owner/repo URLs and fetch metadata/selected files.
- [ ] Limit size/requests, respect rate limits, cache commit snapshots.
- [ ] Record commit/path references and confirmed contribution; do not infer authorship.

### Acceptance criteria

- [ ] No repo writes or code execution.
- [ ] Refresh is explicit; unchanged snapshot reuse does not invoke model.
- [ ] Outages preserve dated prior evidence.

### Testing requirements

- Malicious URLs, missing files, rate limits, oversized content, injected instructions.

### Definition of Done

Snapshot findings link to exact evidence. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P12 — Create reviewed questions, rubrics, and activity catalogs

- **Owner:** @Jiya-garg08
- **Phase:** 4; **area:** assessment
- **Objective:** Provide trustworthy reusable content.
- **Why:** Fixed reviewed catalogs reduce both hallucinations and model spend.
- **Dependencies:** P03, P10
- **Inputs:** Initial role/topic scope.
- **Outputs:** Versioned reviewed catalog.
- **Expected files/modules:** `content/questions/`, `content/activities/`, `scripts/`, `tests/unit/`

### Tasks and subtasks

- [ ] Author objective keys, short-answer/code rubrics and fixed interview question templates.
- [ ] Map questions/activities to skills, subtopics, durations and prerequisites.
- [ ] Add content validation and review status; keep keys out of tutoring corpus.

### Acceptance criteria

- [ ] Every published item has a key/rubric and valid skill mapping.
- [ ] Fixed interview can start from stored questions with zero model calls.

### Testing requirements

- Schema, duplicates, broken references, answer-key segregation.

### Definition of Done

Catalog supports diagnostic, practice and fixed interview flows. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P13 — Implement objective diagnostic sessions and scoring

- **Owner:** @Jiya-garg08
- **Phase:** 4; **area:** assessment
- **Objective:** Establish a reliable performance baseline.
- **Why:** Measure knowledge without unnecessary AI calls.
- **Dependencies:** P07, P10, P12
- **Inputs:** Goal and diagnostic answers.
- **Outputs:** Durable diagnostic results.
- **Expected files/modules:** `src/placement_agent/services/assessments.py`, `src/placement_agent/ui/pages/`, `src/placement_agent/db/`

### Tasks and subtasks

- [ ] Select balanced reviewed questions and freeze prompt/key versions.
- [ ] Save/resume attempts and score objective answers deterministically.
- [ ] Protect keys until submission and deduplicate request IDs.

### Acceptance criteria

- [ ] Objective scoring incurs zero model requests.
- [ ] Refresh/retry does not duplicate attempts; incomplete session resumes.

### Testing requirements

- Key cases, answer-key exposure, session states, duplicate submissions.

### Definition of Done

Complete diagnostic works without live AI. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P14 — Implement one-shot rubric evaluation and batch contracts

- **Owner:** @Jiya-garg08
- **Phase:** 4; **area:** assessment
- **Objective:** Evaluate open answers with fixed rubrics.
- **Why:** Provide feedback at controlled cost while preserving uncertainty.
- **Dependencies:** P06, P12, P13
- **Inputs:** Frozen answer(s) and rubric(s).
- **Outputs:** Validated evaluation or pending status.
- **Expected files/modules:** `src/placement_agent/services/evaluations.py`, `src/placement_agent/agent/prompts/`, `evals/datasets/`

### Tasks and subtasks

- [ ] Implement single-answer and bounded multi-answer evaluation contracts.
- [ ] Use fresh context, evidence spans and frozen rubric versions.
- [ ] Validate all outputs without model repair; support pending/disputed results.

### Acceptance criteria

- [ ] One explicit request yields at most one model response.
- [ ] Invalid/missing item results do not partially update skill evidence.
- [ ] Student output cannot modify rubric or tool policy.

### Testing requirements

- Human-scored calibration, blank answers, injection, malformed/misaligned batches.

### Definition of Done

Measured grading agreement and call-count gates pass. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P15 — Implement evidence aggregation and skill-state history

- **Owner:** @voltrox007
- **Phase:** 4; **area:** data
- **Objective:** Convert accepted evidence into defensible student state.
- **Why:** Make personalization auditable and recomputable.
- **Dependencies:** P10, P13, P14
- **Inputs:** Accepted evaluations and sourced claims.
- **Outputs:** Skill summaries and progress events.
- **Expected files/modules:** `src/placement_agent/services/student_state.py`, `src/placement_agent/domain/policies.py`, `src/placement_agent/db/`

### Tasks and subtasks

- [ ] Add evidence mapping, coverage/reliability thresholds and repeat-attempt policy.
- [ ] Handle superseded/disputed evidence, stale observations and contradictions.
- [ ] Update affected state/history transactionally.

### Acceptance criteria

- [ ] Claims/completion do not raise mastery; unknown differs from weak.
- [ ] Aggregation costs zero model calls and every change has provenance.

### Testing requirements

- Sparse/contradictory/stale evidence, duplicate prevention, recomputation.

### Definition of Done

Before/after state can be explained from raw evidence. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P16 — Build versioned knowledge ingestion and embedding cache

- **Owner:** @vidhimahajan06
- **Phase:** 5; **area:** rag
- **Objective:** Create a controlled educational index.
- **Why:** Ground answers while avoiding repeated embedding charges.
- **Dependencies:** P02, P03, P10
- **Inputs:** Approved educational documents.
- **Outputs:** Versioned indexed corpus.
- **Expected files/modules:** `src/placement_agent/rag/{ingest,chunking}.py`, `content/knowledge-manifest/`, `scripts/`

### Tasks and subtasks

- [ ] Register permitted sources, parse/chunk and attach provenance metadata.
- [ ] Hash-cache changed chunks and compatible embedding versions.
- [ ] Build candidate index, validate, activate atomically and retire obsolete corpus.

### Acceptance criteria

- [ ] Repeat ingestion embeds only changed content.
- [ ] Failure cannot activate a partial corpus; answer keys/private student data excluded.

### Testing requirements

- Hashes, chunk provenance, embedding compatibility, partial failures.

### Definition of Done

Initial corpus indexed with valid source metadata. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P17 — Implement single-pass retrieval and citation resolution

- **Owner:** @vidhimahajan06
- **Phase:** 5; **area:** rag
- **Objective:** Supply bounded cited context before agent invocation.
- **Why:** Avoid autonomous query expansion and costly repeated retrieval.
- **Dependencies:** P05, P16
- **Inputs:** Validated query and topic filters.
- **Outputs:** Cited passage set.
- **Expected files/modules:** `src/placement_agent/rag/retrieval.py`, `evals/datasets/`, `tests/integration/`

### Tasks and subtasks

- [ ] Add hybrid search, active-version filters, deduplication and passage limits.
- [ ] Cache eligible queries and track query embedding usage.
- [ ] Resolve citation IDs and unsupported/no-result cases.

### Acceptance criteria

- [ ] One application-controlled retrieval pass by default.
- [ ] Only supplied citation IDs resolve; no hidden LLM retrieval planner.

### Testing requirements

- Gold queries, unsupported queries, stale filters, citation injection.

### Definition of Done

Retrieval target met on reviewed dataset. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P18 — Build explicit single-question grounded learning help

- **Owner:** @vidhimahajan06
- **Phase:** 5; **area:** rag
- **Objective:** Connect Foundry and retrieval without continuous chat.
- **Why:** Provide educational explanations under the credit policy.
- **Dependencies:** P06, P07, P17
- **Inputs:** One student question.
- **Outputs:** One grounded answer or limitation.
- **Expected files/modules:** `src/placement_agent/ui/pages/`, `src/placement_agent/agent/prompts/`, `src/placement_agent/agent/context.py`

### Tasks and subtasks

- [ ] Add explicit ask action, application-prefetched context and one agent response.
- [ ] Render validated citations and show cached answer.
- [ ] Add unsupported-query/outage handling; no automatic follow-up or conversational continuation.

### Acceptance criteria

- [ ] At most one response request per explicit question.
- [ ] Rerender/reopen costs zero calls; no fabricated citations.

### Testing requirements

- Real bounded Foundry/Search smoke, unsupported questions, reruns, injection.

### Definition of Done

Live one-shot cited answer demonstrated. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P19 — Implement deterministic gaps and seven-day scheduling

- **Owner:** @voltrox007
- **Phase:** 5; **area:** planning
- **Objective:** Produce feasible plans without model inference.
- **Why:** Save credits and enforce real preparation constraints.
- **Dependencies:** P10, P12, P15
- **Inputs:** Goal, skill state and capacity.
- **Outputs:** Seven-day plan.
- **Expected files/modules:** `src/placement_agent/services/planning.py`, `src/placement_agent/ui/pages/`, `src/placement_agent/db/`

### Tasks and subtasks

- [ ] Rank unknowns/gaps by documented rules.
- [ ] Select approved activities, prerequisites and available capacity.
- [ ] Version drafts/accepted plans; preserve completed work and handle insufficient content.

### Acceptance criteria

- [ ] Plan generation uses zero model calls.
- [ ] All IDs, capacity, prerequisite and horizon constraints pass.

### Testing requirements

- Sparse evidence, short deadline, unavailable activities, stale revision.

### Definition of Done

Usable deterministic plan precedes optional prose. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P20 — Add optional one-shot plan and recommendation explanations

- **Owner:** @vidhimahajan06
- **Phase:** 5; **area:** agent
- **Objective:** Explain already-valid recommendations.
- **Why:** Improve clarity without delegating feasibility to the model.
- **Dependencies:** P06, P19
- **Inputs:** Valid plan/candidates and evidence.
- **Outputs:** Optional explained recommendation.
- **Expected files/modules:** `src/placement_agent/agent/prompts/`, `src/placement_agent/services/planning.py`, `src/placement_agent/ui/pages/`

### Tasks and subtasks

- [ ] Provide selected candidates, reason codes and evidence in bounded context.
- [ ] Generate explanations only on explicit request and cache them.
- [ ] Reject stale/mismatched IDs; retain deterministic explanation fallback.

### Acceptance criteria

- [ ] No AI call needed to view/use a plan.
- [ ] One requested explanation at most; no unavailable activity or fabricated performance.

### Testing requirements

- Invalid IDs, stale state, duplicate requests, no-budget fallback.

### Definition of Done

Evidence-linked explanation is optional and reusable. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P21 — Build practice submissions and one-shot static code feedback

- **Owner:** @SakshamSekhri
- **Phase:** 6; **area:** ui
- **Objective:** Deliver exercises and a single feedback report.
- **Why:** Remove continuous coding interaction while retaining useful review.
- **Dependencies:** P12, P14, P15, P19
- **Inputs:** Student practice submission.
- **Outputs:** Stored one-shot feedback.
- **Expected files/modules:** `src/placement_agent/ui/pages/`, `src/placement_agent/services/{assessments,evaluations}.py`

### Tasks and subtasks

- [ ] Display catalog exercises and persist text/code submissions.
- [ ] Add explicit Get feedback action and immutable input hash.
- [ ] Store/report review once; update only eligible evidence and completion.

### Acceptance criteria

- [ ] No model calls while typing/editing/saving; at most one on requested review.
- [ ] No execution, inline coding assistant or automatic follow-ups.
- [ ] Report explicitly says code was not executed.

### Testing requirements

- Malicious code text, duplicate requests, failures, edit/new version, reopen.

### Definition of Done

Practice feedback and history satisfy call-count tests. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P22 — Prepare reusable project-viva question batches

- **Owner:** @Jiya-garg08
- **Phase:** 6; **area:** assessment
- **Objective:** Create evidence-linked project questions without dialogue.
- **Why:** Keep resume-to-viva useful and affordable.
- **Dependencies:** P09, P11, P12, P14
- **Inputs:** Confirmed project snapshot.
- **Outputs:** Frozen reusable viva questions.
- **Expected files/modules:** `src/placement_agent/services/interviews.py`, `src/placement_agent/agent/prompts/`, `src/placement_agent/ui/pages/`

### Tasks and subtasks

- [ ] Select confirmed project evidence and reviewed templates.
- [ ] Optionally generate one bounded question batch on explicit request.
- [ ] Validate evidence references and persist questions/rubrics for reuse.

### Acceptance criteria

- [ ] Template selection uses zero calls; optional generation uses at most one.
- [ ] No adaptive follow-up generation after answers.
- [ ] Question provenance does not invent contribution or technologies.

### Testing requirements

- Sparse/conflicting evidence, duplicate generation, injected repo text.

### Definition of Done

Reusable questions link to source snapshot. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P23 — Implement fixed mock interviews with one final feedback report

- **Owner:** @Jiya-garg08
- **Phase:** 6; **area:** assessment
- **Objective:** Deliver a complete non-conversational interview workflow.
- **Why:** Meet the owner's explicit credit-saving requirement.
- **Dependencies:** P12, P14, P15, P22
- **Inputs:** Stored questions and final answers.
- **Outputs:** One final interview report.
- **Expected files/modules:** `src/placement_agent/services/interviews.py`, `src/placement_agent/ui/pages/`, `src/placement_agent/agent/prompts/`

### Tasks and subtasks

- [ ] Freeze bounded question set and collect all answers without AI.
- [ ] Support save/resume, submission validation and explicit final evaluation.
- [ ] Evaluate full bounded session in one response; persist report and per-item evidence atomically.

### Acceptance criteria

- [ ] Zero model calls during start/display/answer save/resume.
- [ ] At most one response for final feedback; no per-answer calls or follow-ups.
- [ ] Oversized batch is rejected before model access, not silently split.

### Testing requirements

- Actual call count, refresh/double-click, timeout, missing batch items, resume.

### Definition of Done

Fixed interview meets batch validation and credit tests. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P24 — Build progress views and deterministic adaptation

- **Owner:** @voltrox007
- **Phase:** 6; **area:** data
- **Objective:** Close the evidence-to-recommendation loop.
- **Why:** Prove personalization without an always-active agent.
- **Dependencies:** P15, P20, P21, P23
- **Inputs:** Historical accepted evidence.
- **Outputs:** Inspectable trends and updated next action.
- **Expected files/modules:** `src/placement_agent/ui/pages/`, `src/placement_agent/services/{student_state,planning}.py`

### Tasks and subtasks

- [ ] Show score coverage, claims, progress and source history.
- [ ] Recompute next eligible action after accepted results.
- [ ] Add dispute/invalidation flow and material plan-revision proposals.

### Acceptance criteria

- [ ] Dashboards/state updates/ranking incur zero model calls.
- [ ] Completion and mastery remain distinct; disputed evaluations traceable.

### Testing requirements

- Before/after fixture, invalidation/recompute, unchanged evidence/no duplicate recommendation.

### Definition of Done

Evidence demonstrably changes guidance without background AI. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P25 — Implement privacy, deletion, and injection defenses

- **Owner:** @Jiya-garg08
- **Phase:** 7; **area:** security
- **Objective:** Protect student information in a public-code project.
- **Why:** Prevent data leakage and unsafe document-driven behavior.
- **Dependencies:** P09, P11, P18, P24
- **Inputs:** Privacy requests and adversarial inputs.
- **Outputs:** Tracked privacy outcomes and verified controls.
- **Expected files/modules:** `src/placement_agent/services/privacy.py`, `src/placement_agent/ui/pages/`, `tests/security/`, `docs/deployment.md`

### Tasks and subtasks

- [ ] Add authorized export/delete and tracked remote cleanup.
- [ ] Enforce ownership, upload/URL limits, secret redaction and private-cache scoping.
- [ ] Document retention/backups and no model-side mutation policy.

### Acceptance criteria

- [ ] Cross-student access denied; deleted data inaccessible locally.
- [ ] Remote failures visible/retryable; logs contain no secrets.
- [ ] Documents cannot induce extra calls or forbidden actions.

### Testing requirements

- Ownership, malicious docs/URLs, interrupted deletion, cache isolation.

### Definition of Done

Security checks pass without critical findings. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P26 — Measure quality, credit consumption, and resilience

- **Owner:** @Jiya-garg08
- **Phase:** 7; **area:** testing
- **Objective:** Establish release evidence.
- **Why:** Verify quality and savings rather than assuming one-shot behavior is cheap.
- **Dependencies:** P18, P20, P23, P24
- **Inputs:** Representative scenarios and pinned versions.
- **Outputs:** Quality/usage report.
- **Expected files/modules:** `evals/`, `src/placement_agent/telemetry.py`, `docs/testing.md`

### Tasks and subtasks

- [ ] Run retrieval/grounding/human-scored rubric datasets.
- [ ] Measure tokens, latency, actual request counts and batch evaluation alignment.
- [ ] Test quotas, outages, malformed responses and ambiguous billing; record versioned report.

### Acceptance criteria

- [ ] Defined quality gates met or release blocked with documented failures.
- [ ] All credit-policy tests pass; no hidden retries/repair calls.
- [ ] No state corruption after provider failures.

### Testing requirements

- Offline suite plus explicit small-budget live evaluation.

### Definition of Done

Measured report records dataset sizes, limits and provider versions. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P27 — Package and deploy an authenticated single-host demo

- **Owner:** @SakshamSekhri
- **Phase:** 7; **area:** deployment
- **Objective:** Make the tested project accessible for demonstration.
- **Why:** Provide reproducible hosting while respecting SQLite and budget assumptions.
- **Dependencies:** P25, P26
- **Inputs:** Tested release and approved resource budget.
- **Outputs:** Controlled hosted demo.
- **Expected files/modules:** `deploy/`, `docs/deployment.md`

### Tasks and subtasks

- [ ] Package app and single-host persistent local storage.
- [ ] Configure HTTPS, verified authentication, managed identity and usage limits.
- [ ] Document deployment, monitoring, costs and teardown.

### Acceptance criteria

- [ ] Restart preserves records; no auth bypass or secrets in image.
- [ ] No shared-network SQLite/multiple replicas.
- [ ] Live AI disabled without configured limits.

### Testing requirements

- Hosted smoke, identity boundary, restart and budget checks.

### Definition of Done

Deployment reproducible from documentation. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## P28 — Verify recovery and deliver the final group demo

- **Owner:** @voltrox007
- **Phase:** 7; **area:** deployment
- **Objective:** Finish with a recoverable demonstrable release.
- **Why:** Show real integrations and the group's complete preparation workflow.
- **Dependencies:** P27
- **Inputs:** Hosted candidate release.
- **Outputs:** Verified demo and release package.
- **Expected files/modules:** `scripts/`, `docs/demo.md`, `README.md`, `release notes`

### Tasks and subtasks

- [ ] Exercise backup/restore and compatible rollback.
- [ ] Seed synthetic student/demo repo; finalize guide and release notes.
- [ ] Demonstrate fixed interview with unchanged call counter until one final evaluation; record contributions.

### Acceptance criteria

- [ ] Restore matches expected state and reapplies deletion requirements.
- [ ] Real persistent Foundry and real retrieval shown.
- [ ] Static code review labeled unexecuted; replay clearly labeled if used.

### Testing requirements

- Recovery drill and complete end-to-end acceptance walkthrough.

### Definition of Done

Release tagged with limitations, team contributions and measured usage. Acceptance criteria pass; relevant tests pass; documentation updated; no secrets/private data committed; issue-linked PR reviewed; model-call counts verified where applicable.

## Deferred scope

Sandboxed execution, PostgreSQL/multiple replicas, private GitHub authorization, MCP interoperability, Foundry IQ, voice and additional roles remain separate future proposals. Do not create these as MVP commitments. Continuous conversation requires a new explicit scope/budget decision.
