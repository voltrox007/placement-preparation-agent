"""Validate versioned starter content without network calls or model usage."""

import argparse
import json
from pathlib import Path

from placement_agent.rag.ingest import EducationalSource, chunk_source
from placement_agent.services.catalog import INTERVIEW, ITEMS, RESOURCES, SKILLS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-human-review", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "content/catalog-manifest.json").read_text(encoding="utf-8"))
    sources = [
        EducationalSource.model_validate(item)
        for item in json.loads((root / "content/knowledge-fixtures.json").read_text(encoding="utf-8"))
    ]
    actual = {
        "skills": len(SKILLS),
        "objective_questions": sum(len(items) for items in ITEMS.values()),
        "interview_questions": len(INTERVIEW),
        "resource_links": len(RESOURCES),
    }
    if actual != manifest["scope"]:
        raise SystemExit(f"Catalog manifest mismatch: expected {manifest['scope']}, found {actual}")
    for skill in SKILLS:
        if skill not in ITEMS or skill not in RESOURCES:
            raise SystemExit(f"Skill {skill!r} lacks questions or a resource")
    approved = sum(source.approved_for_ingestion() for source in sources)
    if args.require_human_review and (manifest["review_status"] != "human_reviewed" or approved != len(sources)):
        raise SystemExit("Human review gate has not been satisfied")
    report = {
        "catalog_version": manifest["catalog_version"],
        "catalog_review_status": manifest["review_status"],
        "catalog_counts": actual,
        "knowledge_sources": len(sources),
        "approved_knowledge_sources": approved,
        "candidate_chunks": sum(len(chunk_source(source, "fixture-v1")) for source in sources),
        "network_calls": 0,
        "model_calls": 0,
    }
    rendered = json.dumps(report, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
