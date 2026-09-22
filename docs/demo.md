# Demonstration guide

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
