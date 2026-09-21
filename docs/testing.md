# Testing and acceptance

## Layers

Unit: objective scoring, scheduling, evidence rules, budget admission, contracts. Database: migrations, ownership, transactions, unique operations. Adapters: Foundry/Search/GitHub success and failure shapes. UI: reruns, resume, submissions, reports. AI evaluation: retrieval, groundedness, rubric agreement. Security: injection, ownership, malicious inputs. Operations: restart, backup, restore, quotas.

Use mocked providers in routine CI. Live Azure smoke/evaluation suites are explicit, small, budget-checked, and version-recorded. No costly live model call on every commit.

## Mandatory credit tests

- Showing/saving interview questions/answers produces zero model requests.
- One final interview submission produces at most one model response request.
- One coding feedback request produces at most one model response request.
- Valid report reopening/page refresh produces zero additional requests.
- Model SDK does not silently retry; simulated timeout preserves answers and marks uncertain usage.
- Invalid JSON does not invoke automatic repair or update skill state.
- Concurrent duplicate clicks cannot create additional paid operations.
- Budget exhaustion denies a call before contacting the provider.
- Optional question generation and feedback are separately labeled, explicit actions.
- No oversized interview batch is silently split into multiple paid calls.

## Initial quality targets

All reviewed objective key cases pass; zero cross-student access; zero duplicate evidence writes; all plans satisfy capacity/prerequisites; citation IDs all resolve; retrieval hit@5 at least 85%; supported claims at least 90%; appropriate unsupported-query abstention at least 90%; rubric agreement within one point on a 0–4 scale at least 80%; no critical security findings.

Use at least 30 answerable retrieval cases, 20 unsupported questions, and 30 human-scored answers. Record dataset sizes/limitations and human review; these thresholds are proposed gates, not achieved results. Batch interview evaluation must also show item-to-answer alignment and no omitted answers.

## Milestone gates

A: persistent Foundry agent returns one valid bounded response. B: confirmed profile survives restart. C: reviewed diagnostic updates skill state correctly. D: educational response cites real retrieval. E: plan meets constraints. F: accepted evidence changes recommendation. G: no AI calls during interview answering, one final report request. H: authenticated deployment and restore verified.
