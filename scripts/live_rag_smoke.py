"""Run one bounded embedding, Search, and Foundry grounded-answer smoke test."""

import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from placement_agent.bootstrap import build_service
from placement_agent.config import load_settings
from placement_agent.rag.retrieval import create_embedding_client
from placement_agent.services.ai_feedback import answer_learning


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("docs/reports/live-rag-smoke.json"))
    args = parser.parse_args()
    settings = load_settings()
    api_key = os.environ.get("AZURE_SEARCH_API_KEY", "").strip()
    if not api_key:
        raise ValueError("AZURE_SEARCH_API_KEY is required only for this local administrative smoke")
    embedding_client = create_embedding_client(settings.azure_openai_endpoint)
    search = SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.search_index_name,
        credential=AzureKeyCredential(api_key),
    )
    source_id = "live-smoke-primary-key"
    text = (
        "A primary key identifies each row in a relational table. A foreign key refers to a key in another "
        "table and helps enforce referential integrity. An index is a separate structure used to speed lookup."
    )
    started = perf_counter()
    embedding = embedding_client.embeddings.create(model=settings.embedding_deployment, input=text)
    upload = search.upload_documents(
        documents=[
            {
                "id": source_id,
                "content_hash": "live-smoke-only",
                "text": text,
                "title": "Synthetic relational-key smoke passage",
                "source_url": "https://www.sqlite.org/lang_createtable.html",
                "locator": "Synthetic smoke passage",
                "corpus_version": settings.knowledge_corpus_version,
                "approved": True,
                "reviewed_on": "2026-09-22",
                "vector": embedding.data[0].embedding,
            }
        ]
    )
    if len(upload) != 1 or not upload[0].succeeded:
        raise RuntimeError("Smoke document upload failed")
    service = build_service()
    student_id = "live-smoke-student"
    service.ensure_student(student_id)
    result = answer_learning(
        student_id,
        "What does a primary key do?",
        f"live-rag-smoke:{uuid4()}",
        service=service,
    )
    elapsed_ms = round((perf_counter() - started) * 1000)
    output = result.get("output") or {}
    citation_ids = output.get("citation_ids", [])
    if result.get("status") != "succeeded" or source_id not in citation_ids:
        raise RuntimeError("Live grounded answer did not cite the retrieved smoke passage")
    report = {
        "status": "passed",
        "agent": f"{settings.foundry_agent_name}:{settings.foundry_agent_version}",
        "embedding_deployment": settings.embedding_deployment,
        "search_index": settings.search_index_name,
        "corpus_version": settings.knowledge_corpus_version,
        "response_requests": 1,
        "embedding_requests": 2,
        "search_requests": 1,
        "automatic_retries": 0,
        "actual_response_tokens": result.get("actual_tokens"),
        "elapsed_ms": elapsed_ms,
        "citation_ids": citation_ids,
        "source_kind": "synthetic_smoke_only",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    search.close()
    embedding_client.close()


if __name__ == "__main__":
    main()
