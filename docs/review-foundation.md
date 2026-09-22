# Foundation review

Independent code review performed on 2026-09-21. This is an agent review of the
available implementation, not a statement that human teammates reviewed it or
that the full project is complete.

## Verified scope

Reviewed the approved revision 1.1 blueprint, architecture, implementation
decisions, agent policy, configuration, domain contracts and policy functions.
Ran the complete current unit suite using the bundled Python 3.12 runtime and
Pydantic 2.13.5: **24 tests passed**. No packages were installed and no Azure
requests were made for this review.

The follow-up review verified these fixes:

- Evaluation policy checks normalized scores against frozen rubric weights and
  compares rubric, agent and prompt versions with server-known versions.
- Successful agent results require an action-compatible typed output. Arbitrary
  raw JSON text is no longer accepted as a successful payload.
- Each quoted answer excerpt has a length limit.
- Configuration rejects interview limits exceeding the 12-item batch contract.

Existing controls reject extra fields, invalid scores, duplicate batch items,
unsupported execution claims, stale plans, invalid citation membership and
cyclic prerequisites. Nested contracts and tuple collections are immutable in
normal use. Configuration defaults to offline mode and does not perform cloud
access. StudentContext is explicitly a server-created identity contract;
parsing it is not authentication.

## Persistence review remains pending

The initial database code received static review only. SQLAlchemy/Alembic were
not available for executing the integration suite at review time. Developer
corrections are underway; the following findings require follow-up inspection
and executed integration evidence before being considered resolved:

1. Enforce the project-wide budget as well as student budgets inside the same
   atomic admission transaction, including cross-student concurrency tests.
2. Persist a reserved-to-dispatched transition before provider access and
   prohibit refunds of dispatched or ambiguous operations.
3. Restore timezone-aware UTC timestamps on SQLite hydration and test round trips.
4. Make concurrent identical submissions return the stored attempt rather than
   surfacing an integrity error.

Present session and submission repository reads join through the owning student
and use a nondisclosing missing-resource error. This observation does not
establish ownership enforcement for future services or direct ORM writes.

The initial migration is explicitly a schema subset. P04 cannot be closed as a
complete database implementation on the strength of this review. Evaluation
revision/supersession support and remaining documented entities also require
implementation and validation.

## Outstanding acceptance gates

- Dependency resolution, locked-environment reproduction and hosted CI execution.
- SQLite migrations, concurrency, rollback, ownership and recovery tests.
- Paid-operation controller enforcement, including durable dispatch and actual
  SDK transport request counts under timeout/429/500 conditions.
- Real persistent Foundry agent invocation, version verification and usage capture.
- Retrieval ingestion, source validation and measured grounding quality.
- Human-reviewed educational content and rubric calibration.
- Authenticated deployment, backup/restore and final end-to-end demonstration.

The current unit results support the reviewed foundation contracts. They do not
prove live Foundry integration, production authentication, credit enforcement,
database correctness or overall project completion. Typed output validation
must be followed by the appropriate cross-record policy and ownership checks
before any student state is updated.
