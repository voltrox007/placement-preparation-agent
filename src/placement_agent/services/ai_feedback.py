"""Explicit one-shot bridges from application workflows to the Foundry coach.

These functions are called only by submit buttons. They create no conversation,
perform no automatic retry, and delegate idempotency and budget enforcement to
``AICoach``.
"""

from typing import Any

from placement_agent.agent.coach import AICoach
from placement_agent.bootstrap import build_service
from placement_agent.config import load_settings
from placement_agent.domain.contracts import StudentContext


def _dependencies(service=None, coach=None):
    settings = load_settings()
    service = service or build_service()
    if coach is None:
        engine = service.factory.kw["bind"]
        coach = AICoach(settings, engine)
    return settings, service, coach


def _public_result(result) -> dict[str, Any]:
    return result.model_dump(mode="json")


def request_session_feedback(
    student_id: str, session_id: str, request_key: str | None = None, *, service=None, coach=None
) -> dict[str, Any]:
    """Evaluate a completed practice/interview session in exactly one model request.

    ``request_key`` should be retained by the caller across retries. The UI derives
    a stable key from the session, so a repeated click reads the cached result.
    """
    settings, service, coach = _dependencies(service, coach)
    if not settings.live_ai_enabled:
        raise ValueError("Live Foundry feedback is disabled")
    profile = service.profile(student_id)
    payload = service.session_feedback_payload(student_id, session_id)
    if not payload["items"]:
        return {
            "status": "objective_only",
            "message": "Objective answers were scored deterministically; no model call is needed.",
        }
    max_chars = settings.max_answer_chars
    assert max_chars is not None
    if any(len(item["answer"]) > max_chars for item in payload["items"]):
        raise ValueError("An answer exceeds the configured feedback limit")
    context = StudentContext(student_id=student_id, state_version=profile["state_version"])
    key = request_key or f"session-feedback:{session_id}"
    if payload["kind"] == "interview":
        result = coach.interview_report(context, key, payload)
    elif payload["kind"] == "practice":
        if len(payload["items"]) != 1:
            raise ValueError("Practice feedback requires exactly one frozen item")
        result = coach.review_code(context, key, payload["items"][0])
    else:
        return {
            "status": "objective_only",
            "message": "Diagnostic answers were scored deterministically; no model call is needed.",
        }
    return _public_result(result)


def answer_learning(
    student_id: str, query: str, request_key: str, *, service=None, coach=None, retriever=None
) -> dict[str, Any]:
    """Retrieve first, then issue one grounded-answer request with bounded passages."""
    settings, service, coach = _dependencies(service, coach)
    if not settings.live_ai_enabled:
        raise ValueError("Live Foundry feedback is disabled")
    if not query.strip() or len(query) > 1000:
        raise ValueError("Learning question must contain 1 to 1,000 characters")
    closeables = []
    if retriever is None:
        configured = (
            settings.search_endpoint,
            settings.search_index_name,
            settings.embedding_deployment,
            settings.knowledge_corpus_version,
            settings.embedding_dimensions,
        )
        if not all(configured):
            raise ValueError("Azure knowledge retrieval is not configured")
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        from placement_agent.rag.retrieval import create_azure_search

        project = AIProjectClient(endpoint=settings.foundry_project_endpoint, credential=DefaultAzureCredential())
        embedding_client = project.get_openai_client(max_retries=0, timeout=60.0)
        retriever = create_azure_search(
            endpoint=settings.search_endpoint,
            index_name=settings.search_index_name,
            embedding_client=embedding_client,
            embedding_model=settings.embedding_deployment,
            corpus_version=settings.knowledge_corpus_version,
            dimensions=settings.embedding_dimensions,
        )
        closeables = [retriever.search_client, embedding_client, project]
    try:
        passages = retriever.search(query.strip(), top=5)
    finally:
        for resource in closeables:
            resource.close()
    profile = service.profile(student_id)
    context = StudentContext(student_id=student_id, state_version=profile["state_version"])
    result = coach.answer(context, request_key, query.strip(), passages)
    return _public_result(result)
