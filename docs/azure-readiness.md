# Azure readiness and implementation contract

Read-only assessment: 2026-09-21. This document records preparation, not a successful Azure integration. P05 remains open until its authorized live acceptance test succeeds.

## Observed local readiness

- No environment-variable names containing `AZURE`, `FOUNDRY`, `SEARCH`, or `OPENAI` were present in the inspected process.
- Azure CLI (`az`) was not found on PATH.
- No `.env*` configuration files were found by the repository file search at inspection time.
- No credentials, tokens, secret values, or Azure account IDs were printed or inspected. No resources were provisioned and no paid inference or embedding requests were made.

These checks do not establish whether resources or authentication exist elsewhere (for example, in the portal or an IDE). They establish that this shell cannot currently perform the documented live acceptance path.

## What is needed before P05 can close

1. The existing Foundry project endpoint, or an approved subscription/region/resource choice if a project must be created.
2. Entra authentication with appropriate access to that project; local Azure CLI login is a suitable development path.
3. A supported deployed chat model and its deployment name. A model catalog name alone is insufficient.
4. An existing prompt-agent name and immutable version, or authorization to register the project's documented prompt agent.
5. Explicit project/student usage limits, per-action input/output ceilings, and allowance for one bounded smoke request.
6. A successful request through that agent reference with observed outbound request count and recorded provider usage.

Embedding and Search resources are additionally required for P16-P18; their absence should not prevent the isolated P05 agent smoke test. Do not ask the user to paste secrets into chat or GitHub.

## Supported API direction

Use the current Foundry **2.x** Python API generation. Microsoft documents `azure-ai-projects` 2.7.0 as of this assessment and the `v1` data-plane surface. Start compatibility resolution from that exact version, then pin the resolved, tested dependency graph. Do not claim it has been installed or verified against the user's Azure deployment yet. Avoid mixing classic 1.x thread/run examples with the current prompt-agent APIs. [SDK documentation](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme?view=azure-python)

The intended packages are `azure-ai-projects`, `azure-identity`, the compatible `openai` dependency, and later `azure-search-documents`. No agent framework or MCP dependency is required. Use `AIProjectClient`, `project.agents.create_version(...)` with `PromptAgentDefinition`, and the project-derived OpenAI Responses client. Invocation must carry `agent_reference` with the configured agent name **and version**; do not quietly substitute a direct model-only call. [Prompt-agent creation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/use-your-data-quickstart?tabs=python-new), [runtime components](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/runtime-components)

The live verification established that a Responses request referencing a persistent
agent rejects request-level `instructions` and `text` response-format overrides. The
adapter therefore embeds the action-specific JSON Schema in the single input payload
and validates the returned JSON again with the application's strict Pydantic contract.
Refusal, incomplete output, malformed JSON, unexpected IDs, or missing interview items
produce an invalid/pending result and never an automatic repair call.

## One-request provider contract

- `complete(task, trusted_context, frozen_input)` invokes `responses.create` at most once.
- Disable OpenAI SDK automatic retries with `max_retries=0`; also inspect the project client's underlying transport/retry configuration so a second retry layer cannot resend inference requests. Microsoft explicitly documents the OpenAI SDK retry switch. [Quota and retries](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/quota)
- Prove behavior with a counting HTTP transport for 429, 500, connection errors, and timeouts. Counting calls to a wrapper method alone does not prove absence of SDK retries.
- Configure no hosted tools in the pinned agent definition, and allow no runtime tool continuation. Verify the stored definition during readiness checks; one Responses request could otherwise trigger multiple internal model/tool operations.
- Omit `previous_response_id` and conversation continuation from default MVP requests. Retrieve relevant state and educational passages before inference.
- Enforce output-token and frozen-input limits before provider access. Reject oversized interview batches rather than splitting them into multiple paid evaluations.
- Return provider response ID, completion status, validated payload, configured agent version, and available usage. Preserve unknown usage as unknown.
- An ambiguous timeout retains its usage reservation and submitted work. A user-requested retry is a separate budget-checked action.
- No SDK credential acquisition, agent registration, response request, or embedding request should happen merely by importing modules or rendering a page.

Use fake providers for normal tests and label those results as synthetic. Offline success is not P05 live acceptance.

## Identity and persistence boundary

The server derives `StudentContext` from a verified identity. It checks ownership before reading data or constructing model context. The model cannot choose a student ID, execute SQL, commit state, or invoke external tools. Cache identity includes student ID, immutable input hash, task, and relevant agent/prompt/rubric/corpus/state versions.

Use local development credentials only in development. Prefer a specific managed identity credential for deployed Azure compute. Never enable full SDK HTTP-body logging for student documents or submissions. Student state remains in SQLite; persistent agent configuration is not persistent student memory.

## Retrieval and embedding contract

Use application-controlled `azure-search-documents` retrieval with one search pass. Construct active corpus/version filters in trusted application code, not model text. Supply keyword text and a query vector for hybrid retrieval, deduplicate, cap passages, and return source IDs resolved from the index. [Hybrid retrieval](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview)

Generate query/document embeddings with the same compatible deployment/version/dimension policy. The query vector must match the index vector field dimensions. Cache by normalized content hash plus embedding version and dimensions. Track embedding requests separately: zero chat responses does not imply zero Azure usage. [Vector query requirements](https://learn.microsoft.com/en-us/azure/search/vector-search-how-to-query)

Ingestion writes a candidate corpus, checks every upload result, validates retrieval, and only then switches the active corpus pointer. Failed ingestion must leave the previous corpus active. Reviewed answer keys and private student documents are excluded from the public educational index.

## Implementation that can proceed without Azure access

Typed contracts, deterministic planning/scoring, SQLite migrations, identity checks, application interfaces, fake-provider tests, credit reservations, request-count tests, chunking, citation validation, and versioned ingestion logic can proceed independently. Keep all live integrations disabled until configuration and budget checks pass. P05, live portions of P16-P18/P26, and deployment acceptance must remain explicitly incomplete until real evidence exists.
# Verified Foundry configuration

On 2026-09-22, the project owner authenticated with Azure CLI against the enabled
`Azure for Students` subscription. A read-only SDK check verified the project endpoint.
Agent `placement-preparation-agent` version `4` was then created from the repository's
canonical instructions and verified as a prompt agent using deployment `gpt-4.1-mini`
with zero tools. Agent creation and verification did not invoke the model.

The owner authorized a total project credit envelope of INR 10,000, with INR 1,500
allocated to development and integration testing and INR 200 allocated to the initial
live smoke test. The offline gates passed before the smoke request was enabled.

## Live smoke result

The bounded smoke batch made three outbound response requests. The first two were
HTTP 400 payload rejections and retained conservative unknown-usage reservations;
neither was retried automatically. The diagnostic identified that persistent-agent
requests cannot accept request-level instructions or text-format overrides. After the
adapter was corrected, the third request succeeded using agent version 4, returned a
grounded answer with the supplied citation ID, and reported 447 total tokens. The
application also denied an attempted request before provider access when the synthetic
student allowance was exhausted. No tools, conversation, continuation, or model retry
was used. Cost Management remains the source of truth for billed currency and can lag.
