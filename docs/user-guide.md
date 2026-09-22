# Local student workflow

Run the application using the setup guide, then choose **Initialize / open local demo**.
This creates or opens the single synthetic demo student. The interface explicitly labels
local demo mode; it is not an authenticated multi-user deployment.

1. **Profile & Goal:** Save your name, education and study capacity. Upload a text PDF/TXT
   or paste resume text, review it, and explicitly confirm the facts before saving.
   Text extraction is local and makes no model request. Scanned documents need pasted text.
2. Optionally import a public GitHub project. Import reads at most six API responses:
   metadata, current commit, README and three dependency manifests. No repository code
   is run or modified. Snapshots retain commit/path citations and do not prove authorship.
3. **Diagnostic:** Start a fixed session, save each answer and finish the session.
4. **Learning Plan:** Create a seven-day plan constrained by the saved goal.
5. **Learn & Practice / Interview:** Submit answers to fixed questions. Objective scoring
   is deterministic. Open answers require an explicit one-shot feedback request when
   Foundry is configured. Code is never executed and no feedback is fabricated offline.
6. **Progress & Data:** Inspect recorded progress, export your data, or explicitly delete
   the local demo student's records. Completion and demonstrated mastery are distinct.

Page changes and ordinary rerenders do not invoke Foundry. Each answer is persisted on
submission with a stable request key. Do not enter real private information into a shared
demo. Hosted authentication and live Azure verification have separate acceptance gates.
