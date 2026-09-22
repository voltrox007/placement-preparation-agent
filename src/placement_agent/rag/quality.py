"""Deterministic RAG quality checks; this module never contacts Azure or an LLM."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from placement_agent.domain.contracts import GroundedAnswer, RetrievedPassage


@dataclass(frozen=True)
class Citation:
    citation_id: str
    title: str
    source_url: str
    locator: str


def resolve_citations(answer: GroundedAnswer, passages: Sequence[RetrievedPassage]) -> tuple[Citation, ...]:
    """Resolve model-returned IDs through trusted retrieval data and reject unknown IDs."""
    by_id = {passage.citation_id: passage for passage in passages}
    missing = set(answer.citation_ids) - set(by_id)
    if missing:
        raise ValueError("Answer contains citation IDs that were not retrieved")
    if not answer.insufficient_evidence and not answer.citation_ids:
        raise ValueError("A supported answer must cite at least one retrieved passage")
    return tuple(
        Citation(
            citation_id=item, title=by_id[item].title, source_url=by_id[item].source_url, locator=by_id[item].locator
        )
        for item in answer.citation_ids
    )


@dataclass(frozen=True)
class RetrievalCase:
    case_id: str
    query: str
    expected_citation_ids: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalReport:
    cases: int
    hits: int
    hit_at_k: float
    failures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_retrieval(
    cases: Iterable[RetrievalCase], search: Callable[[str, int], Sequence[RetrievedPassage]], *, k: int = 5
) -> RetrievalReport:
    if not 1 <= k <= 6:
        raise ValueError("k must be between 1 and 6")
    materialized = tuple(cases)
    if not materialized:
        raise ValueError("At least one retrieval case is required")
    failures: list[str] = []
    for case in materialized:
        found = {passage.citation_id for passage in search(case.query, k)}
        if not found.intersection(case.expected_citation_ids):
            failures.append(case.case_id)
    hits = len(materialized) - len(failures)
    return RetrievalReport(len(materialized), hits, hits / len(materialized), tuple(failures))


@dataclass(frozen=True)
class CreditReport:
    actions: int
    provider_calls: int
    retries: int
    unknown_usage: int
    actual_tokens: int

    def validate(self, *, maximum_calls: int) -> None:
        if self.provider_calls > maximum_calls:
            raise ValueError("Provider-call budget exceeded")
        if self.retries:
            raise ValueError("Automatic retries are prohibited")

    def as_dict(self) -> dict[str, int]:
        return asdict(self)
