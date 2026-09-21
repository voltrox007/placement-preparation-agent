# Setup and environment plan

There is no runnable application yet. P02 will pin a compatible Python version, package set, lockfile, checks, and exact commands. P05 verifies Azure access before dependent feature development. Do not install or provision anything solely from this planning document.

## Future prerequisites

Git, a supported Python runtime, an isolated environment, an Azure subscription/project with approved spending, access to a compatible Foundry chat model and embedding model, Search access, and optionally a server-held read-only GitHub credential for public requests.

## Future settings

| Setting | Purpose |
|---|---|
| Foundry project endpoint | Agent invocation scope |
| Agent name/version | Persistent registered agent reference |
| Chat/embedding deployments | Compatible selected models |
| Search endpoint/index/corpus version | Approved educational retrieval |
| Database URL | Local non-synced SQLite path |
| Private storage directory | Uploads and repository artifacts |
| Authentication mode | Synthetic local identity versus verified hosted identity |
| Optional GitHub credential reference | Server-side read-only API access |
| Maximum input/output tokens | Per-action bounds |
| Per-student/project usage allowance | Admission control, required before live AI |
| Maximum interview questions/answer length | Bound one final request |
| Logging level and retention | Redacted operational records |

Credentials belong in secure local configuration/managed identity, not GitHub, issue comments, sample data, or model context. `.env.example` will contain names and placeholders only.

SQLite must be outside OneDrive/network-synced storage. The source repository may be elsewhere, but the running database requires appropriate local storage semantics.
