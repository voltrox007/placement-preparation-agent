# Quality and credit evaluation

The repository contains deterministic quality instrumentation and small development fixtures. It does not claim a completed human evaluation or a live Azure AI Search benchmark.

## Reproducible local checks

```powershell
$env:PYTHONPATH="src"
python scripts/validate_content.py --report docs/reports/content-validation.json
python scripts/evaluate_retrieval.py --report docs/reports/retrieval-offline.json
pytest -q
```

The content validator checks catalog counts, source contracts, review gates and candidate chunk construction without network or model calls. The retrieval evaluator measures hit@5 against four checked-in smoke cases. These cases guard pipeline regressions; they are too small and too simple to satisfy the proposed production-quality gate.

## Release gates requiring people or Azure

- A named subject reviewer must review the 40 objective questions, answer keys, explanations, five interview prompts and four knowledge summaries. Update the manifest and each source only after that review.
- Expand retrieval evaluation to at least 30 answerable cases and 20 unsupported questions. Run those cases against the configured Azure AI Search candidate index before activation.
- Collect at least 30 independently human-scored interview/practice answers to measure rubric agreement.
- Record supported-claim and abstention judgments by a human reviewer; citation-ID resolution alone does not prove claim support.
- Run the bounded live Foundry suite only under the authorized development allowance. Store counts, token usage, version and failure status; do not store private student content in reports.

## Credit and resilience evidence

Unit and integration tests enforce one response per explicit action, stable request-key caching, no SDK retry, no automatic JSON repair, budget denial before dispatch, unknown-usage accounting after ambiguous failure, and no model calls while a student types or navigates. `CreditReport` provides a small machine-readable aggregate with hard checks for maximum calls and zero retries. Live cost figures must come from provider usage and Azure Cost Management; estimated figures must be labeled as estimates.
