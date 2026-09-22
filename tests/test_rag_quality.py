import pytest

from placement_agent.domain.contracts import GroundedAnswer, RetrievedPassage
from placement_agent.rag.quality import CreditReport, RetrievalCase, evaluate_retrieval, resolve_citations
from placement_agent.rag.retrieval import LocalKnowledgeSearch


def passage(cid="db-primary-key", text="A primary key uniquely identifies a row."):
    return RetrievedPassage(
        citation_id=cid,
        text=text,
        title="Database keys",
        source_url="https://example.org/db",
        locator="Primary keys",
        corpus_version="fixture-v1",
    )


def test_citations_resolve_only_from_trusted_passages():
    resolved = resolve_citations(
        GroundedAnswer(answer="It identifies a row.", citation_ids=("db-primary-key",)), [passage()]
    )
    assert resolved[0].source_url == "https://example.org/db"
    with pytest.raises(ValueError, match="not retrieved"):
        resolve_citations(GroundedAnswer(answer="Unsupported", citation_ids=("invented",)), [passage()])


def test_supported_answer_requires_citation_but_abstention_does_not():
    with pytest.raises(ValueError, match="must cite"):
        resolve_citations(GroundedAnswer(answer="Claim", citation_ids=()), [passage()])
    assert (
        resolve_citations(
            GroundedAnswer(answer="Insufficient evidence.", citation_ids=(), insufficient_evidence=True), []
        )
        == ()
    )


def test_offline_retrieval_evaluation_reports_misses():
    search = LocalKnowledgeSearch([passage()])
    cases = (
        RetrievalCase("answerable", "What does a primary key identify?", ("db-primary-key",)),
        RetrievalCase("miss", "Explain graph traversal", ("graph-bfs",)),
    )
    report = evaluate_retrieval(cases, lambda query, k: search.search(query, top=k))
    assert report.hit_at_k == 0.5
    assert report.failures == ("miss",)


def test_credit_report_enforces_call_and_retry_limits():
    CreditReport(actions=3, provider_calls=1, retries=0, unknown_usage=0, actual_tokens=400).validate(maximum_calls=1)
    with pytest.raises(ValueError, match="retries"):
        CreditReport(actions=1, provider_calls=1, retries=1, unknown_usage=0, actual_tokens=0).validate(maximum_calls=1)
