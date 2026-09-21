# Developer setup and environment

The configuration foundation is implemented; there is no runnable application yet.
Supported Python range is 3.12–3.13. Configuration tests run without dependencies.
Pydantic 2.13.5 is pinned from the available bundled runtime. A complete resolved
dependency lock, fresh installation, lint and type-check execution remain P02
completion gates: package-index access was unavailable in the implementation environment.
Do not treat the current metadata as a verified lockfile or P02 as complete.

## Run the verified offline configuration checks

From the repository root in PowerShell with Python 3.13.5:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests/unit -p test_config.py -v
python -m compileall -q src/placement_agent/config.py
```

On Linux/macOS prefix the test command with `PYTHONPATH=src`.
CI runs these configuration tests on Python 3.12.14 and 3.13.5 without package
installation, Azure credentials, or model calls. This is a foundation check,
not yet the complete application test suite. Ruff and strict mypy configuration
is present in `pyproject.toml`; installing/pinning their tools and executing them
must precede closing P02.

## Configuration behavior

`placement_agent.config.load_settings()` returns an immutable `Settings` object.
It reads process environment variables or an explicitly supplied mapping; it does
not load `.env`, write files, create a database, or contact Azure.
`.env.example` documents settings. Keep credentials out of source control.

`LIVE_AI_ENABLED` defaults to `false`. Enabling it requires the Foundry project
HTTPS endpoint, persistent agent name/version, and positive integer values for
`MAX_INPUT_TOKENS`, `MAX_OUTPUT_TOKENS`, `STUDENT_DAILY_TOKEN_LIMIT`,
`PROJECT_DAILY_TOKEN_LIMIT`, `MAX_INTERVIEW_QUESTIONS`, and `MAX_ANSWER_CHARS`.
Input plus output ceilings must fit the student daily allowance, which must fit
the project allowance. No paid default budget is invented. Invalid configuration
raises `ConfigurationError` without including supplied values in its message.

The budgets are token limits, not currency estimates. P06 must implement atomic
reservations and actual usage accounting; configuration validation is not a usage
ledger. Enabling a flag never itself requests feedback or starts a conversation.
Only `AUTH_MODE=local_demo` is implemented; public hosted authentication remains
unavailable. `LOG_LEVEL` defaults to `INFO`. The local database default is
`sqlite:///data/private/placement.db`; private storage defaults to `data/private`.

## Fresh environment gate (pending network availability)

Create an isolated environment with `python -m venv .venv`. Resolve and commit a
complete dependency lock, install it inside that environment, then install the
project with `--no-build-isolation --no-deps -e .`. Run `pip check`, Ruff, mypy,
and the complete offline test suite. The lock and successful results must be
documented before the reproducible-setup acceptance criterion is considered met.

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
