# Implementation baseline and agent responsibilities

## Baseline review

The project owner authorized implementation after publication of blueprint revision 1.1. The architect agent reviewed the blueprint, architecture, data model, agent policy, roadmap, and development workflow. This records an architecture review, not attendance or approval by individual human teammates. Existing GitHub assignees remain project ownership records; agent roles below describe execution responsibility and do not impersonate those people.

The baseline is accepted for incremental implementation with these non-negotiable constraints:

- A persistent Azure Foundry agent is mandatory for live AI functionality.
- One explicit AI action permits at most one outbound model response request. SDK retries, repair calls, model-driven retrieval loops, and automatic continuation are disabled.
- Interview questions and rubrics are frozen before answers are collected. Saving answers invokes no model. Final feedback evaluates the bounded session in one request.
- Submitted code is data for static review and is never executed.
- Claims, completion, repository content, and demonstrated performance remain distinct evidence classes.
- Live Azure validation, authentication, and deployment are not satisfied by offline tests or mock providers.

## Minimal contracts for P03

Pydantic domain contracts are separate from SQLAlchemy persistence models. Reject extra fields on provider-facing outputs. Use UTC timestamps, stable string IDs, explicit enums, nonnegative versions, and bounded strings/collections. Prefer explicit field names over ambiguous unstructured dictionaries.

| Contract | Required meaning |
|---|---|
| `StudentContext` | Server-derived student ID and expected state version; never trust a UI-selected identity |
| `ProfileDraft` / `ConfirmedProfile` | Draft source spans and uncertainty versus explicitly confirmed facts |
| `GoalSpec` | Role ID, deadline, daily/weekly capacity, confirmed requirement IDs |
| `EvidenceRecord` | Student, skill, type, source reference, validity, observation time, optional evaluation ID |
| `SkillState` | Unknown/developing/working/strong, nullable observed score, coverage, reliability, computed version |
| `QuestionSnapshot` | Item ID, skill/subtopic, frozen prompt, question/rubric version; keep answer key out of display DTOs |
| `EvaluationResult` | Attempt ID, normalized score, rubric dimensions, answer evidence, uncertainty and evaluator versions |
| `InterviewBatchResult` | Session ID, frozen input hash, exactly one result for every submitted item, final report |
| `PlanDraft` | Goal, source state version, dated approved activity IDs and durations |
| `RetrievedPassage` | Supplied citation ID, passage text, trusted source locator and corpus version |
| `UsageReservation` | Student/request key, action, budget period, reserved call/token counts, reconciliation status |
| `AgentTaskResult` | Action, request key, provider reference, valid typed output or explicit failure, actual/unknown usage |

Scalar validation belongs in contracts; ownership, catalog IDs, rubric dimension equality, citation membership, and stale-version checks belong in services. Interview batch validation must reject duplicate, missing, and unexpected item IDs before inserting any evaluation or evidence. Never convert provider error text into a successful report.

## Service interfaces and dependency direction

Use explicit service methods with a trusted `StudentContext` parameter for private data. Services depend on repositories and small adapter protocols; UI modules depend on services. Domain modules do not import Streamlit, SQLAlchemy, or Azure SDK classes.

| Service | Initial operations |
|---|---|
| Profile | Read/save confirmed profile; create/revise active goal |
| Assessment | Start fixed session; read display item; submit idempotent attempt; score objective item |
| Evaluation | Freeze submission; validate single/batch feedback; apply accepted evaluations transactionally |
| Student state | Recompute affected skills from eligible evidence; append history |
| Planning | Rank eligible activities; create feasible seven-day draft; accept with expected state version |
| Interview | Freeze catalog question set; save answers; request final batch report |
| Agent executor | Execute one bounded action through a supplied provider adapter |
| Budget | Reserve atomically; reconcile known usage; retain unknown usage after ambiguous failures |
| Retrieval | Return bounded approved passages from one retrieval operation |

Provider protocol: one method takes a bounded task and returns raw output plus provider ID/usage. Tests inject a counting fake. Runtime configuration chooses offline demonstration or live Foundry explicitly; offline mode must be visibly labeled and must never silently replace a failed live call.

## Persistence implementation rules for P04

Use SQLAlchemy and Alembic with one migration authority. Keep core relationships relational; bounded JSON holds immutable rubric/extraction payloads. Include `evaluation_batches` and `usage_reservations` from the first applicable migration. A run/request key is unique within its student scope, and reuse with changed input is a conflict rather than a new paid request.

Atomic reservation must account for both completed usage and outstanding reservations under concurrent requests. External calls run outside database transactions. A timed-out call retains its reservation with unknown usage. A failure proven to occur before dispatch can release the reservation. A repeated in-flight key returns pending and cannot dispatch again. SQLite admission checks and insertion must share a write transaction; a read-then-write sequence across separate transactions is insufficient.

Evaluation acceptance, evidence insertion, skill recomputation, progress history, and state-version increment form one transaction. A complete interview batch is validated before this transaction. Every private entity lookup checks ownership, including indirect paths through session items and attempts. Use unique constraints/partial indexes for one active goal and accepted active plan, and explicit checks for state and score bounds.

Schema may be introduced incrementally, but an issue claiming the complete P04 schema must implement its documented table scope; a subset is not complete merely because migration tests pass.

## Execution allocation

All roles work in dependency order. The code reviewer independently reviews every implementation; the reviewer-owned issues below concern quality/security deliverables. Root integration owns branch integration, verification of evidence, issue comments, PR publication and issue closure. This mapping does not change human GitHub assignees.

| Issue | Primary agent role | Required supporting role |
|---|---|---|
| P01 | Architect | Root integration verifies GitHub metadata |
| P02 | Developer one | Code reviewer |
| P03 | Developer two | Architect and AI expert |
| P04 | Developer two | Architect and code reviewer |
| P05 | AI expert | Root integration for Azure access |
| P06 | AI expert | Developer two for atomic budgets |
| P07 | Developer one | Code reviewer |
| P08 | Developer two | Developer one for UI |
| P09 | Developer one | AI expert |
| P10 | Developer one | Architect |
| P11 | Developer one | Code reviewer |
| P12 | Developer two | Architect and code reviewer |
| P13 | Developer two | Developer one for UI |
| P14 | AI expert | Developer two for persistence |
| P15 | Developer two | Architect |
| P16 | AI expert | Code reviewer |
| P17 | AI expert | Code reviewer |
| P18 | Developer one | AI expert |
| P19 | Developer two | Architect |
| P20 | AI expert | Developer one for UI |
| P21 | Developer one | AI expert and code reviewer |
| P22 | AI expert | Developer two |
| P23 | Developer two | AI expert and developer one |
| P24 | Developer one | Developer two |
| P25 | Code reviewer | Developers implement findings |
| P26 | Code reviewer | AI expert measures live usage |
| P27 | Root integration | Developer one and code reviewer |
| P28 | Root integration | Architect and code reviewer |

## Completion and blockers

The architect review finds no scope contradiction in revision 1.1. The agent execution policy in this document supersedes any earlier tool-round or adaptive-interview suggestion in conversation history.

Issues remain open where acceptance criteria require unavailable Azure resources, live measurements, human content review, authenticated hosting, or recovery evidence. Code can be prepared and offline-tested for those issues, but its completion comment must distinguish implemented behavior from unverified integration. P01 human team review must not be fabricated; the owner has authorized the agent team to proceed, and any remaining human review is recorded explicitly.
