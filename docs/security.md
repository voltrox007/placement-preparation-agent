# Security model

## Trust boundaries

Resume text, job descriptions, repository content, student answers, and retrieved passages are untrusted data. They may contain prompt injection. The application stores them as evidence, uses immutable rubric snapshots, bounds their size, and sends them to Foundry only inside a typed one-shot request. Submitted code is never executed. The Foundry agent has no tools or web search.

Student-owned reads and writes include the student identifier in the database query. Missing and unauthorized resources return the same `Resource unavailable` error. This prevents basic resource enumeration. Local demo mode still uses a fixed synthetic identity and is not authentication.

## Secrets and logs

Use `DefaultAzureCredential` or workload managed identity. Never store API keys, access tokens, connection strings, `.env` files, databases, or backups in Git. `placement_agent.security.redact` provides defensive structured-log redaction for sensitive key names, bearer credentials, and Azure API-key text. Application logs should contain operation IDs, status, latency, agent/corpus versions, and aggregate token counts; they should not contain resumes, answers, retrieved passages, credentials, or raw model responses.

## Abuse controls

Input sizes, fixed interview length, request idempotency, ownership checks, HTTPS-only Azure endpoints, allowlisted GitHub URLs, bounded repository snapshots, deterministic scoring, atomic token reservations, no retries, and disabled agent tools limit common abuse paths. Treat model output as untrusted: validate strict schemas, cited evidence IDs, score ranges, and stored input hashes before presenting or persisting it.

## Known limitation

Hosted authentication is not implemented. `DEPLOYMENT_ENVIRONMENT=hosted` fails closed at startup. The current build is for localhost demonstrations only until Entra authentication and the associated HTTP/session controls are implemented and independently tested.
