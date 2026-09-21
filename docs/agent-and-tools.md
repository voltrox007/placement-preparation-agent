# Foundry agent, functions, and credit policy

## Agent

One persistent, versioned Foundry prompt agent (`placement-coach` conceptually). All production actions invoke that agent reference. Pin a compatible model/SDK/agent version during P05. Do not substitute an unregistered model call for the mandatory agent.

Task modes: extraction, grounded single-answer help, optional plan explanation, static practice review, optional project-question batch, final interview evaluation. Each mode has a strict output contract and a bounded context. Fresh evaluation context prevents earlier hints from contaminating grading.

## Call policy

| Action | Default model response requests |
|---|---:|
| Profile edits, role template, dashboards, resume sessions | 0 |
| Objective scoring, skill aggregation, next-activity ranking | 0 |
| Deterministic plan generation | 0 |
| Explicit resume/JD extraction | At most 1 per submitted document action |
| Explicit grounded learning question | At most 1 |
| Explicit optional plan explanation | At most 1 |
| Coding/short-answer feedback request | At most 1 per frozen submission |
| Start/resume interview, show questions, save answers | 0 |
| Final interview feedback request | At most 1 for the bounded session |
| Optional project-question preparation | At most 1 per explicitly requested batch |
| Reopen valid cached feedback | 0 |

"At most 1" is an application request limit, not a promise of constant cost. Set output token ceilings and input limits; measure provider usage. Disable SDK automatic retries for model requests where supported and test actual outbound request counts. Do not add reasoning/self-critique or repair calls behind the UI.

## Budget and duplicate protection

Before live calls are enabled, configure per-action token limits, maximum interview questions/answer lengths, per-student limits, and a project daily allowance. No invented currency budget. Maintain a server-side usage ledger and atomic reservations so concurrent clicks cannot bypass limits.

Cache keys include student, task, immutable input hash, goal/state where relevant, prompt/agent/rubric/corpus versions. Student-specific results never share an unscoped cache. Page reruns and repeated request keys reuse existing operations. Avoid automatically returning cached output for different input versions.

Persist provider response IDs and known usage. For ambiguous timeouts, mark usage unknown and conservatively retain the reservation until reconciliation; never assume no charge or automatically repeat the request. An explicit retry is a new budget-checked action and warns that the earlier attempt may have consumed usage. Internal DB idempotency does not guarantee provider billing idempotency.

## Context and memory

Supply task contract, trusted identity scope, relevant confirmed facts, frozen answers/rubrics, selected evidence, and retrieved passages. Do not transmit full histories or unrelated private data. SQLite is authoritative. Foundry conversations are optional bounded session artifacts, not long-term student memory; fresh single-task contexts are preferred for evaluation.

## Functions and tools

The application normally calls functions before the agent request, reducing model/tool round trips:

| Function | Inputs → outputs | Use / avoid | Security |
|---|---|---|---|
| Preparation summary | Requested fields → current summary | Prefetch relevant state; omit unrelated history | Server injects student scope |
| Skill evidence | Skill/limit → sourced observations | Explain gaps; not generic prose | Ownership and bounds |
| Learning search | Query/topic → cited passages | Technical knowledge only; never scores | Active approved corpus |
| Eligible activities | Goal/constraints → ranked approved activities | Plan/recommendation inputs | IDs validated in code |
| Project evidence | Owned project/topic → excerpts | Ground questions/reviews | Bounded commit/path content |
| Progress summary | Date range → aggregates | Progress reports | Scoped dates and student |

No model-driven function loops are enabled in the default MVP path. These are ordinary Python service functions, not MCP servers. A tool-calling demonstration is not required and must not be added solely to consume extra turns.

User-triggered application commands own resume/GitHub imports, submission, accepted plans, corrections, and deletion. The model cannot write state, run SQL/shell/code, fetch arbitrary URLs, read secrets, or modify GitHub.

## Grounding and feedback

Emit only supplied citation/evidence IDs. Resolve links in code. Evaluation uses frozen rubric dimensions, answer excerpts, uncertainty flags, and per-item scores. Missing or invalid per-item results make the batch pending, without silent extra calls. Student disputes supersede evaluations through an auditable workflow.

Static code feedback must say **not executed** and may discuss likely issues, complexity assumptions, and readability. It must never claim hidden tests passed. Interview reports are preparation feedback, not hiring predictions.

## MCP decision

Defer MCP until another independent client needs shared tools or a proven existing integration reduces work. If added, retain read-only allowlists, identity scopes, input validation, secret isolation, and call budgets. No generic database or shell MCP.
