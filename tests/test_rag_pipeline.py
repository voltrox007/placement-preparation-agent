from types import SimpleNamespace

import pytest

from placement_agent.rag.ingest import EducationalSource, chunk_source, ingest_candidate


def source():
    return EducationalSource(
        source_id="keys",
        title="Keys",
        source_url="https://example.org/keys",
        text="A primary key identifies one row.",
        permitted_use="Original test content",
        reviewed_on="2026-09-22",
        review_status="human_reviewed",
        reviewer="Test reviewer",
        classification="public_educational",
    )


class Search:
    def __init__(self, fail=False):
        self.docs = {}
        self.fail = fail

    def upload_documents(self, documents):
        self.docs.update({d["id"]: d for d in documents})
        return [SimpleNamespace(succeeded=not self.fail, key=d["id"]) for d in documents]

    def get_document(self, key):
        return self.docs[key]


class Embeddings:
    def __init__(self):
        self.calls = 0
        self.embeddings = self

    def create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])])


def test_candidate_activates_only_after_success_and_reuses_embedding(tmp_path):
    embeddings = Embeddings()
    path = tmp_path / "state.json"
    for version in ("v1", "v2"):
        result = ingest_candidate(
            [source()],
            corpus_version=version,
            search_client=Search(),
            embedding_client=embeddings,
            embedding_model="embedding1",
            dimensions=2,
            state_path=path,
        )
        assert result["active_corpus"] == version
    assert embeddings.calls == 1
    before = path.read_text()
    with pytest.raises(RuntimeError):
        ingest_candidate(
            [source()],
            corpus_version="v3",
            search_client=Search(fail=True),
            embedding_client=embeddings,
            embedding_model="embedding1",
            dimensions=2,
            state_path=path,
        )
    assert path.read_text() == before


def test_chunking_and_private_source_rejection():
    assert chunk_source(source(), "v1")[0]["content_hash"]
    with pytest.raises(ValueError):
        EducationalSource(**(source().model_dump() | {"classification": "private_resume"}))


def test_draft_source_cannot_be_ingested(tmp_path):
    draft = source().model_copy(update={"review_status": "draft", "reviewer": None})
    with pytest.raises(ValueError, match="human review"):
        ingest_candidate(
            [draft],
            corpus_version="v1",
            search_client=Search(),
            embedding_client=Embeddings(),
            embedding_model="embedding1",
            dimensions=2,
            state_path=tmp_path / "state.json",
        )
