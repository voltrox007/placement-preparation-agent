# v0.1.0 — authenticated placement-preparation MVP

This release delivers the complete student workflow in a modular Streamlit application backed by SQLite, deterministic assessment and planning logic, curated Azure AI Search retrieval, and one-shot Azure Foundry feedback.

## Release behavior

- Tenant-authenticated Azure Container Apps demo over HTTPS.
- Persistent single-host SQLite storage on Azure Files with one-replica enforcement.
- Profile, resume/JD confirmation, bounded GitHub evidence, diagnostics, skill evidence, seven-day plans, learning questions, static coding feedback, fixed interviews, recommendations, export, and deletion.
- Persistent Foundry prompt agent `placement-preparation-agent:4`, with no agent tools or automatic continuation.
- Approved `starter-v1` knowledge corpus and citation-bearing hybrid retrieval.
- Atomic usage reservation, bounded tokens, cached successful outputs, and no automatic model retries.

## Validation

- 83 automated tests and 23 subtests passed before deployment.
- Ruff and mypy passed.
- Anonymous ingress redirected to Entra login.
- Persistent data survived a replica restart.
- One live Foundry request completed with 280 total tokens and zero retries.
- Hosted managed-identity embedding and Search retrieval passed.
- Backup/restore matched all 19 database tables using synthetic data.

## Known limitations

- Coding submissions are reviewed statically and are never executed.
- Interviews use fixed questions and one final report; there is no continuous AI conversation.
- SQLite requires a single replica and is intended only for the group showcase.
- Only synthetic demo data and approved public sources are supported.
- The product does not predict placement probability or replace professional career advice.

## Team contributions

The 28 implementation issues were divided evenly among @voltrox007, @SakshamSekhri, @vidhimahajan06, and @Jiya-garg08. The release corpus was approved by @Jiya-garg08.
