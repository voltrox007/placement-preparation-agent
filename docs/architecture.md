# Architecture

## Boundaries

LLM: extraction drafts, grounded explanations, one-shot feedback, optional batch project questions. Deterministic application: identity, workflow, retrieval preparation, scoring keys, evidence aggregation, plan feasibility, budget checks, persistence. External adapters: Foundry, Search/embeddings, GitHub. Database: authoritative student state. RAG: approved educational passages only.

```mermaid
flowchart TB
  User[Student] --> UI[Streamlit forms and reports]
  UI --> Controller[Workflow and identity boundary]
  Controller --> Services[Domain services]
  Services --> DB[(SQLite)]
  Services --> GitHub[Bounded GitHub REST adapter]
  Services --> Retrieval[Single retrieval request]
  Retrieval --> Search[Azure AI Search]
  Controller --> Budget[Cache and budget gate]
  Budget --> Context[Prefetched authorized context]
  Context --> Foundry[Persistent Foundry agent: one response]
  Foundry --> Validate[Output validation]
  Validate --> Services
  Validate --> UI
```

## User and feedback flow

```mermaid
flowchart LR
  Profile[Confirm profile and goal] --> Assess[Reviewed diagnostic]
  Assess --> Evidence[Persist accepted evidence]
  Evidence --> State[Recompute skill state]
  State --> Plan[Deterministic seven-day plan]
  Plan --> Practice[Learn or submit practice]
  Practice --> Request[Explicit feedback request]
  Request --> Report[One AI report or objective score]
  Report --> Evidence
```

## Credit-conscious AI action

```mermaid
sequenceDiagram
  actor Student
  participant App
  participant DB
  participant Search
  participant Foundry
  Student->>App: Request feedback / one learning answer
  App->>DB: Check ownership, request key, cached result
  App->>DB: Atomically reserve permitted usage
  App->>Search: Retrieve once if needed
  Search-->>App: Bounded cited passages
  App->>Foundry: One task with prefetched context
  Foundry-->>App: One structured result
  App->>App: Validate without another model call
  App->>DB: Record usage and valid result or failure
  App-->>Student: Report or explicit retry option
```

## Fixed interview flow

```mermaid
flowchart TD
  Start[Start interview] --> Select[Select stored question set]
  Select --> Freeze[Persist all questions and rubrics]
  Freeze --> Answer[Collect and save answers: zero AI calls]
  Answer --> Submit[Submit complete session]
  Submit --> Check[Validate lengths and budget]
  Check --> Evaluate[One bounded Foundry evaluation]
  Evaluate --> Valid{Valid output?}
  Valid -->|Yes| Report[Save final report and eligible evidence]
  Valid -->|No| Pending[Keep answers; no automatic retry]
```

## Components

| Component | Purpose/responsibility | Inputs → outputs | Dependencies/technology |
|---|---|---|---|
| UI | Structured forms, session resume, reports | Actions → commands/views | Streamlit/services |
| Identity | Authoritative student scope | Verified subject → student context | Auth boundary/repositories |
| Workflow | Legal transitions and explicit AI actions | Command/state → operations | Python |
| Profile/documents | Parse, draft, confirm facts | PDF/text → confirmed versioned facts | Parser/Pydantic/Foundry |
| GitHub | Bounded evidence snapshots | Approved repo → commit/path excerpts | REST client |
| Assessment | Frozen questions and objective scoring | Goal/answers → results | Reviewed catalog/SQLite |
| Evaluation | One-shot rubric feedback | Bounded submission → valid/pending result | Foundry/validators |
| Student state | Derive skill summaries | Accepted evidence → state/history | Deterministic policies |
| Planning | Eligibility, priorities, scheduling | Goal/state/capacity → feasible plan | Catalog/prerequisites |
| Interview | Fixed sessions, batch final evaluation | Question set/answers → report | State machine/evaluator |
| Retrieval | Educational grounding | Query/filters → passages | Search/embeddings |
| Budget | Admission, deduplication, usage tracking | AI action → permit/deny | SQLite/config |
| Persistence | Ownership, transactions, migrations | Validated data → durable records | SQLAlchemy/Alembic |
| Telemetry | Sanitized usage/failure metrics | Run events → redacted records | Logs/optional Azure telemetry |

## Failure rules

Persist answers before AI access. Provider failures leave attempts intact and evaluations pending. No automatic AI retry, repair, or self-critique call. Search failure yields no fabricated citations. Invalid/stale outputs do not change state. Duplicate submissions return saved results. GitHub outages show dated snapshots. Database failures roll back related local updates.
