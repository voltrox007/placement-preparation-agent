# Starter content review checklist

Issue P12 requires a named human subject reviewer. Review the 40 objective questions, answer keys, explanations, five fixed interview prompts, four learning-resource links, and four knowledge summaries. Confirm that each answer is technically correct, unambiguous for the stated level, mapped to the right skill/subtopic, and free of private data or hidden instructions.

Files to review:

- `src/placement_agent/services/catalog.py`
- `content/knowledge-fixtures.json`
- `content/catalog-manifest.json`

After a human completes the review, record their GitHub username and date in `content/catalog-manifest.json`; set each approved knowledge source to `review_status: human_reviewed` with the same reviewer; then run:

```powershell
$env:PYTHONPATH="src"
python scripts/validate_content.py --require-human-review --report docs/reports/content-validation.json
pytest -q
```

Do not mark content reviewed based only on automated checks or AI authorship.
