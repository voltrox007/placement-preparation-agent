"""Explicit admin ingestion. Requires an existing Search index and embedding deployment."""

import argparse
import json
import os
from pathlib import Path

from placement_agent.agent.client import FoundryProvider
from placement_agent.config import load_settings
from placement_agent.rag.ingest import EducationalSource, ingest_candidate
from placement_agent.rag.retrieval import create_azure_search


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--corpus-version", required=True)
    parser.add_argument("--authorize-embedding-spend", action="store_true")
    parser.add_argument("--state", type=Path, default=Path("data/private/knowledge-state.json"))
    args = parser.parse_args()
    sources = [EducationalSource.model_validate(item) for item in json.loads(args.manifest.read_text(encoding="utf-8"))]
    if not args.authorize_embedding_spend:
        print(f"Validated {len(sources)} sources. No network calls; explicitly authorize ingestion to proceed.")
        return
    provider = FoundryProvider(load_settings())
    try:
        search = create_azure_search(
            endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
            index_name=os.environ["AZURE_SEARCH_INDEX_NAME"],
            embedding_client=provider.client,
            embedding_model=os.environ["EMBEDDING_DEPLOYMENT"],
            corpus_version=args.corpus_version,
            dimensions=int(os.environ["EMBEDDING_DIMENSIONS"]),
        )
        result = ingest_candidate(
            sources,
            corpus_version=args.corpus_version,
            search_client=search.search_client,
            embedding_client=search.embedding_client,
            embedding_model=search.embedding_model,
            dimensions=search.dimensions,
            state_path=args.state,
        )
        print(
            json.dumps(
                {
                    "active_corpus": result["active_corpus"],
                    "document_count": result["document_count"],
                }
            )
        )
    finally:
        provider.close()


if __name__ == "__main__":
    main()
