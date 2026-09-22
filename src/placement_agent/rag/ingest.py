"""Hash-based, educational-only candidate ingestion; activation is a separate atomic step."""

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EducationalSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    title: str = Field(min_length=1, max_length=300)
    source_url: str = Field(pattern=r"^https://", max_length=2048)
    text: str = Field(min_length=1, max_length=200000)
    permitted_use: str = Field(min_length=1)
    reviewed_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    classification: str = Field(pattern=r"^public_educational$")


def chunk_source(source: EducationalSource, corpus_version: str) -> list[dict[str, Any]]:
    if not corpus_version or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in corpus_version
    ):
        raise ValueError("Corpus version must be an index-safe identifier")
    # Paragraph boundaries retain whole short examples. Oversized paragraphs are bounded.
    chunks: list[str] = []
    current = ""
    for paragraph in source.text.split("\n\n"):
        for offset in range(0, len(paragraph), 2400):
            part = paragraph[offset : offset + 2400]
            if len(current) + len(part) + 2 > 2400 and current:
                chunks.append(current)
                current = ""
            current = (current + "\n\n" + part).strip()
    if current:
        chunks.append(current)
    result = []
    for number, text in enumerate(chunks):
        digest = hashlib.sha256(text.encode()).hexdigest()
        result.append(
            {
                "id": f"{corpus_version}_{source.source_id}_{number}",
                "content_hash": digest,
                "text": text,
                "title": source.title,
                "source_url": source.source_url,
                "locator": f"Passage {number + 1}",
                "corpus_version": corpus_version,
                "approved": True,
                "reviewed_on": source.reviewed_on,
            }
        )
    return result


def ingest_candidate(
    sources: list[EducationalSource],
    *,
    corpus_version: str,
    search_client: Any,
    embedding_client: Any,
    embedding_model: str,
    dimensions: int,
    state_path: Path,
) -> dict[str, Any]:
    """Caller explicitly authorizes embedding spend; no retries or partial activation."""
    if not sources or len({s.source_id for s in sources}) != len(sources):
        raise ValueError("Sources must be nonempty with unique IDs")
    previous = json.loads(state_path.read_text()) if state_path.exists() else {}
    if previous.get("active_corpus") == corpus_version:
        raise ValueError("Use a new candidate version; active corpus is immutable")
    cache = previous.get("embedding_cache", {})
    documents = [chunk for source in sources for chunk in chunk_source(source, corpus_version)]
    for document in documents:
        key = f"{embedding_model}:{dimensions}:{document['content_hash']}"
        if key not in cache:
            response = embedding_client.embeddings.create(model=embedding_model, input=document["text"])
            cache[key] = response.data[0].embedding
        if len(cache[key]) != dimensions:
            raise ValueError("Embedding/index dimension mismatch")
        document["vector"] = cache[key]
    results = list(search_client.upload_documents(documents=documents))
    if len(results) != len(documents) or any(not r.succeeded for r in results):
        raise RuntimeError("Candidate upload incomplete; active corpus unchanged")
    if {r.key for r in results} != {d["id"] for d in documents}:
        raise RuntimeError("Upload acknowledgement IDs differ; active corpus unchanged")
    for document in documents:
        stored = search_client.get_document(key=document["id"])
        if stored.get("content_hash") != document["content_hash"]:
            raise RuntimeError("Candidate verification failed; active corpus unchanged")
    state = {
        "active_corpus": corpus_version,
        "embedding_cache": cache,
        "document_count": len(documents),
        "embedding_model": embedding_model,
        "dimensions": dimensions,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_path.with_suffix(".pending")
    temporary.write_text(json.dumps(state), encoding="utf-8")
    temporary.replace(state_path)
    return state
