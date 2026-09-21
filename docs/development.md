# Development workflow

Implement GitHub issues in dependency order; resolving each issue produces a tested part of the project. An issue is not complete just because code exists.

1. Confirm dependencies are done and the assigned owner understands acceptance criteria.
2. Create a small issue branch (for example `issue-13-diagnostic`).
3. Implement only the issue scope and relevant tests.
4. Update affected documentation in the same PR.
5. Link the issue in the PR and show test/validation evidence.
6. Request a teammate review; fix findings before merge.
7. Merge and close using the issue reference; record any remaining limitation.

Parallel work is permitted only for dependency-ready independent issues. Shared contracts/schema changes must be coordinated. Use one primary assignee per issue and a reviewer from another area. Blocked issues retain a visible dependency note. No automatic background model calls may be introduced as a convenience.

## Shared Definition of Done

- Acceptance criteria satisfied and relevant tests passing.
- Ownership, duplicate submission, and error behavior handled where applicable.
- No secrets/private fixtures committed.
- Model calls are explicit, bounded, and tested for count where applicable.
- Documentation and dependency status updated.
- Reviewable PR linked to the issue; no unrelated scope.

## Planned structure (created incrementally)

```text
app.py
pyproject.toml
<dependency lockfile>
.env.example
src/placement_agent/
  config.py
  bootstrap.py
  ui/pages/
  domain/{contracts,enums,policies}.py
  services/{profiles,assessments,evaluations,student_state,planning,interviews,privacy}.py
  agent/{client,orchestrator,context,budget}.py
  agent/prompts/
  rag/{ingest,chunking,retrieval}.py
  integrations/{github,document_parser}.py
  db/{models,session,repositories}.py
  telemetry.py
migrations/
content/{roles,questions,activities,knowledge-manifest}/
tests/{unit,integration,ui,security,fixtures}/
evals/{datasets,reports}/
scripts/
deploy/
docs/
.github/workflows/
```

No application files, packages, CI workflows, or Azure resources are created by initial repository setup. Do not add empty MCP or multi-agent modules.
