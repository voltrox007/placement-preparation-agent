# Quality and credit evaluation

The repository contains deterministic quality instrumentation, small development fixtures, and a bounded live Azure integration smoke. The live smoke passed on 2026-09-22 against Foundry agent version 4, `text-embedding-3-small`, and Azure AI Search index `placement-knowledge-v1`.

## Reproducible local checks

```powershell
$env:PYTHONPATH="src"
python scripts/validate_content.py --report docs/reports/content-validation.json
python scripts/evaluate_retrieval.py --report docs/reports/retrieval-offline.json
pytest -q
```

The content validator checks catalog counts, source contracts, review gates and candidate chunk construction without network or model calls. The retrieval evaluator measures hit@5 against four checked-in smoke cases. These cases guard pipeline regressions; they are too small and too simple to satisfy the proposed production-quality gate.

## Measured live result

The versioned report at `docs/reports/live-rag-smoke.json` records one response request, two embedding requests (one document and one query), one Search request, zero automatic retries, 465 response tokens, 15,576 ms end-to-end latency, and a resolved citation to `live-smoke-primary-key`. The indexed passage is explicitly synthetic smoke data and is not represented as reviewed learning content.

The offline retrieval fixture contains four cases and achieved hit@5 of 1.0. The full automated suite contains 83 tests and 23 subtests across Python 3.12/3.13 CI. Failure-path tests cover budget denial, malformed provider output, idempotent replay, unknown post-dispatch usage, tenant isolation, deletion, backup/restore, and prompt-injection boundaries.

## Release gates requiring people

- A named subject reviewer must review the 40 objective questions, answer keys, explanations, five interview prompts and four knowledge summaries. Update the manifest and each source only after that review.
- Expand retrieval evaluation to at least 30 answerable cases and 20 unsupported questions. Run those cases against the configured Azure AI Search candidate index before activation.
- Collect at least 30 independently human-scored interview/practice answers to measure rubric agreement.
- Record supported-claim and abstention judgments by a human reviewer; citation-ID resolution alone does not prove claim support.
- A public or research-quality release remains blocked until the larger human-scored datasets above are completed. The student-project showcase may use the measured smoke and synthetic demo profile with these limitations displayed.

## Credit and resilience evidence

Unit and integration tests enforce one response per explicit action, stable request-key caching, no SDK retry, no automatic JSON repair, budget denial before dispatch, unknown-usage accounting after ambiguous failure, and no model calls while a student types or navigates. `CreditReport` provides a small machine-readable aggregate with hard checks for maximum calls and zero retries. Live cost figures must come from provider usage and Azure Cost Management; estimated figures must be labeled as estimates.
