# Demonstration guide

Hosted release: `https://placement-prep-agent-prod.proudtree-dd527a5a.uaenorth.azurecontainerapps.io/`. Sign in with an authorized account from the Chitkara tenant. Use only synthetic data.

Use only a synthetic student and approved public repository.

1. Show the confirmed role goal and 45-minute daily capacity.
2. Confirm/correct a sample resume extraction.
3. Inspect a bounded GitHub snapshot with commit/path references.
4. Complete reviewed diagnostic questions and show objective scoring.
5. Show claimed, demonstrated, and unknown skills separately.
6. Generate a seven-day schedule without an LLM call.
7. Explicitly request one grounded learning answer and inspect citations.
8. Submit a coding answer; request one static feedback report labeled not executed.
9. Start a fixed mock interview; save all answers while the model-call counter stays unchanged.
10. Request one final interview report; show one additional model response request.
11. Show accepted evidence changing a deterministic recommendation.
12. Reopen the report/restart the application and demonstrate persistence without extra model calls.

Expose sanitized agent name/version, usage counts, citations, rubric versions, evidence provenance, before/after state, and reason for changed recommendation. Do not show secrets or private reasoning.

The final acceptance demo includes a real persistent Foundry agent response and real retrieval. Offline fixtures or recorded replay are allowed for outages only when clearly labeled; they are not proof of live integration.

## Presenter checklist

Before the session, create a fresh synthetic learner, confirm the agent and corpus versions, run the automated suite, create a database backup, verify the Streamlit health endpoint, and confirm remaining Azure budget. Keep `LIVE_AI_ENABLED=false` during setup and enable it only for the planned one-shot calls. Prepare a clearly labeled offline replay for network failure.

After the session, disable live AI, export the synthetic learner if the result is needed, delete demonstration data, stop compute that is no longer required, and check Azure Cost Management. Record any live call count and token discrepancy before another run.

## v0.1.0 measured validation

The release gate used one live Foundry response request. It returned a grounded primary-key answer with citation `demo-1` and reported 280 total tokens. The hosted retrieval gate then used one embedding request and one Search request, returning approved corpus citations. The persistence gate restarted the active replica and recovered the same marker from the Azure Files mount. The recovery script was also exercised against all 19 SQLite tables using synthetic data.

The coding report remains static analysis and is labeled **not executed**. The interview workflow stores all fixed answers without model calls and permits one final evaluation request. Reopening cached reports does not dispatch another request.
