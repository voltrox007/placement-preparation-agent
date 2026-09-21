# Master project blueprint — revision 1.1

This revision incorporates the owner's requirement to conserve Foundry credits by removing continuous coding and interview conversations. It supersedes conversational/adaptive interview behavior and multi-round agent defaults in the initial planning discussion.

## 1. Understanding the idea

The system prepares a student for an entry-level software role using confirmed profile facts, diagnostic performance, project evidence, and learning history. Its core loop is assess → recommend → practice → accept evidence → update state. Updates occur after submitted activities, not through an always-active agent.

## 2. Critical analysis of the prototype

The prototype's strength is its evidence feedback loop. Its weaknesses are undefined scoring, treating resume claims as ability, excessive orchestration, unclear tool permissions, absent failure handling, and no credit policy. A "Placement Twin" is useful as a relational evidence model, not as a separate service or simulation of the student.

Add explicit state transitions, provenance, versioned question banks/rubrics, idempotent writes, identity boundaries, corrections/disputes, retrieval evaluation, privacy, recovery, and budget enforcement. Remove custom MCP, multiple agents, graph databases, automated crawling, and live coding execution from the MVP.

## 3. Product scope

Initial audience: English-language students pursuing junior Python/backend software roles. Topics: Python, foundational DSA, SQL/DBMS, software engineering basics, and project discussion. One active goal, public GitHub repositories, text-based documents and interviews, small curated corpus, controlled demo deployment.

MVP: confirmed profile/resume/JD, bounded GitHub snapshots, reviewed assessments, evidence-backed skill states, feasible seven-day plans, single-turn grounded help, one-shot static code review, fixed interview sessions with one final evaluation, progress and data controls.

Excluded: back-to-back AI conversation, autonomous continuation, live coding assistance, adaptive AI interview follow-ups, code execution, private repositories, voice/video, placement probability, job application automation, fine-tuning.

## 4–6. Architecture, diagrams, and components

See [architecture](architecture.md). Use one Python modular monolith with Streamlit, a persistent Foundry prompt agent, SQLite, and Azure AI Search. The application prefetches authorized context and controls workflows. The agent interprets and explains; deterministic code authorizes, schedules, scores objective tests, validates, and persists.

## 7. AI agent

See [agent design](agent-and-tools.md). One explicit AI action yields at most one response request by default. No automatic retries, repair calls, nested agent calls, or agent-driven retrieval loops. Inputs are bounded; outputs are typed and validated. Failed calls do not update skills. Additional attempts are explicit and budget-checked.

## 8. Student preparation profile

See [data model](data-model.md). Persist goals, confirmed facts, evidence provenance, question/attempt/evaluation versions, plan history, skill coverage and uncertainty. Claims and resource completion do not establish mastery. "Unknown" is distinct from "weak". No automatic model training occurs.

## 9. RAG

See [knowledge design](knowledge.md). Index approved educational content only. Keep student state, scores, answer keys, and private evidence outside the tutoring index. Retrieve once before the Foundry request; render only validated citation IDs.

## 10. MCP and integrations

MCP is not required. Python service calls and a bounded GitHub REST adapter meet the MVP needs. A later interoperability requirement can justify MCP, but no empty MCP server/module is planned. No arbitrary SQL, shell, URL-fetching, or repository-write tools are exposed to the model.

## 11–12. Database and contracts

See [data model](data-model.md). Use SQLAlchemy/Alembic, SQLite foreign keys, short transactions, request idempotency, and optimistic student-state versions. Typed contracts validate profiles, evidence, evaluations, plans, passages, and usage reservations.

## 13–14. Application and repository

Pages: Home; Profile & Goal; Diagnostic; Learning Plan; Learn & Practice; Interview; Progress & Data. Chat-style rendering is acceptable for one answer but must not imply an automatic ongoing dialogue. Streamlit reruns must not cause external AI requests. See [development guide](development.md) for target repository structure.

## 15–17. Phases, issues, and dependencies

See the [28-issue roadmap](roadmap.md). Phases: foundation; Foundry single-request integration; student understanding; assessment/evidence; retrieval/planning; fixed interviews/progress; hardening/deployment/demo. Issue ownership is in [team](team.md). Numbered plan IDs remain stable even if actual GitHub issue numbers differ.

## 18–20. Testing, security, and deployment

See [testing](testing.md), [setup](setup.md), and [deployment](deployment.md). No application implementation or Azure provisioning is part of repository/issue setup. Later deployments require authenticated access, single-host local SQLite storage, managed identity, backups, and a measured usage budget.

## 21. MVP versus future

Future-only: sandboxed coding execution, PostgreSQL/multiple replicas, private GitHub authorization, MCP interoperability, Foundry IQ, voice interviews, more roles/languages. Continuous conversation is not a promised later feature; revisit only if the owner changes the credit requirement.

## 22. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Credits exhausted by hidden calls | Explicit actions, one-request default, no auto retries, reservation/cap ledger |
| Large final interview payload | Fixed question/answer lengths; bounded batch; fail validation before model call |
| Invalid one-shot feedback | Preserve submission, show pending state, explicit paid retry only |
| Weak personalization | Link recommendations to accepted evidence and deterministic ranking |
| Model or Search access unavailable | Early compatibility checks, offline fixtures, clearly labeled fallback |
| False skill precision | Coverage/reliability labels and versioned heuristics |
| Repository mistaken for authorship | Confirm contributions; record commit/path provenance |
| Prompt injection | Untrusted documents, no model side effects, scoped context |
| Shared SQLite or ephemeral disk | One host with persistent local storage; migrate before scaling |
| Public-repository privacy leak | Synthetic fixtures, ignored private data, secret review |

## 23. Demonstration

See [demo](demo.md). Show the full preparation loop and the visible count of model calls. A fixed mock interview must incur no model calls while questions are displayed or answers saved; final feedback uses one bounded request.

## 24. Implementation order

P01–P04 foundation; P05–P06 Foundry/budgets; P07–P10 onboarding; P11–P15 evidence/assessment; P16–P18 retrieval; P19–P21 planning/practice; P22–P24 fixed interviews/progress; P25–P28 security/quality/deployment/demo. Dependencies take precedence over numerical order.

## 25. Final decision

A credit-conscious Foundry placement coach with evidence-backed state, deterministic workflows, and curated retrieval. The agent is invoked at deliberate checkpoints, not continuously.

## Decision record

- ADR-001: Persistent Azure Foundry prompt agent is mandatory; a plain model call alone is insufficient.
- ADR-002: Modular monolith; no separate backend until another client needs it.
- ADR-003: SQLite for single-host MVP; PostgreSQL before scaling.
- ADR-004: Azure AI Search for explicit educational retrieval; Foundry IQ deferred.
- ADR-005: Direct Python functions/GitHub REST; MCP deferred.
- ADR-006: No arbitrary code execution; feedback is static and labeled unverified.
- ADR-007: Fixed interview questions, one final report, no adaptive conversation.
- ADR-008: One response request per explicit AI action; prefetch context; no automatic AI retries.
- ADR-009: No numerical spending ceiling is invented; live AI features remain disabled until limits are configured.

## Primary technical references

- [Foundry agent options](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)
- [Foundry runtime components](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/runtime-components)
- [Azure hybrid search](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview)
- [Foundry IQ](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq)
- [SQLite WAL constraints](https://sqlite.org/wal.html)
- [GitHub REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)

Recheck model, SDK, regional availability, and prices at implementation time.
