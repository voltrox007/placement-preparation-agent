"""Bounded lexical demo retrieval and explicitly configured Azure hybrid retrieval."""

import re
from typing import Any

from placement_agent.domain.contracts import RetrievedPassage


class LocalKnowledgeSearch:
    """Deterministic offline reference retrieval; never presented as Azure Search."""

    def __init__(self, passages: list[RetrievedPassage]):
        self.passages = passages

    def search(self, query: str, *, top: int = 5) -> list[RetrievedPassage]:
        if not 1 <= len(query.strip()) <= 1000 or not 1 <= top <= 6:
            raise ValueError("Invalid query or retrieval limit")
        terms = set(re.findall(r"[a-z0-9]+", query.lower())) - {
            "the",
            "a",
            "is",
            "what",
            "how",
            "of",
            "in",
        }
        scored = [
            (len(terms & set(re.findall(r"[a-z0-9]+", (p.title + " " + p.text).lower()))), p) for p in self.passages
        ]
        return [p for score, p in sorted(scored, key=lambda item: (-item[0], item[1].citation_id))[:top] if score > 0]


class AzureKnowledgeSearch:
    """One embedding request + one Search request, no agent tool continuation."""

    def __init__(
        self,
        search_client: Any,
        embedding_client: Any,
        embedding_model: str,
        corpus_version: str,
        dimensions: int,
    ):
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", corpus_version):
            raise ValueError("Invalid corpus version")
        self.search_client, self.embedding_client = search_client, embedding_client
        self.embedding_model, self.corpus_version = embedding_model, corpus_version
        self.dimensions = dimensions
        self._cache: dict[str, list[float]] = {}

    def search(self, query: str, *, top: int = 5) -> list[RetrievedPassage]:
        from azure.search.documents.models import VectorizedQuery

        if not 1 <= len(query.strip()) <= 1000 or not 1 <= top <= 6:
            raise ValueError("Invalid query or retrieval limit")
        query = query.strip()
        if query not in self._cache:
            result = self.embedding_client.embeddings.create(model=self.embedding_model, input=query)
            vector = result.data[0].embedding
            if len(vector) != self.dimensions:
                raise ValueError("Embedding dimensions differ from configured index")
            if len(self._cache) >= 128:
                self._cache.clear()
            self._cache[query] = vector
        vector_query = VectorizedQuery(vector=self._cache[query], fields="vector", k_nearest_neighbors=20)
        rows = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=f"corpus_version eq '{self.corpus_version}' and approved eq true",
            top=top,
            select=["id", "text", "title", "source_url", "locator", "corpus_version"],
        )
        passages: list[RetrievedPassage] = []
        hashes: set[str] = set()
        for row in rows:
            if row["text"] in hashes:
                continue
            hashes.add(row["text"])
            passages.append(
                RetrievedPassage(
                    citation_id=row["id"],
                    text=row["text"],
                    title=row["title"],
                    source_url=row["source_url"],
                    locator=row["locator"],
                    corpus_version=row["corpus_version"],
                )
            )
        return passages


def create_azure_search(
    *,
    endpoint: str,
    index_name: str,
    embedding_client: Any,
    embedding_model: str,
    corpus_version: str,
    dimensions: int,
) -> AzureKnowledgeSearch:
    from azure.core.pipeline.policies import RetryPolicy
    from azure.identity import DefaultAzureCredential
    from azure.search.documents import SearchClient

    client = SearchClient(
        endpoint,
        index_name,
        DefaultAzureCredential(),
        retry_policy=RetryPolicy(retry_total=0, retry_connect=0, retry_read=0, retry_status=0),
    )
    return AzureKnowledgeSearch(
        client,
        embedding_client.with_options(max_retries=0),
        embedding_model,
        corpus_version,
        dimensions,
    )
