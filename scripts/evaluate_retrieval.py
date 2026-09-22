"""Run the checked-in retrieval fixture offline and emit a reproducible JSON report."""

import argparse
import json
from pathlib import Path

from placement_agent.domain.contracts import RetrievedPassage
from placement_agent.rag.ingest import EducationalSource, chunk_source
from placement_agent.rag.quality import RetrievalCase, evaluate_retrieval
from placement_agent.rag.retrieval import LocalKnowledgeSearch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sources = [
        EducationalSource.model_validate(item)
        for item in json.loads((root / "content/knowledge-fixtures.json").read_text())
    ]
    passages = [
        RetrievedPassage(
            citation_id=item["id"],
            text=item["text"],
            title=item["title"],
            source_url=item["source_url"],
            locator=item["locator"],
            corpus_version=item["corpus_version"],
        )
        for source in sources
        for item in chunk_source(source, "fixture-v1")
    ]
    cases = [
        RetrievalCase(**item) for item in json.loads((root / "content/evaluation/retrieval-cases.json").read_text())
    ]
    search = LocalKnowledgeSearch(passages)
    report = evaluate_retrieval(cases, lambda query, k: search.search(query, top=k)).as_dict()
    rendered = json.dumps(report, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
