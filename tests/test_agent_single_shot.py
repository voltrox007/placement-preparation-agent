import json
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from placement_agent.agent.client import FoundryProvider, ProviderReply
from placement_agent.agent.coach import AICoach
from placement_agent.config import load_settings
from placement_agent.db.models import Base, Student
from placement_agent.domain.contracts import RetrievedPassage, StudentContext
from placement_agent.domain.enums import RunStatus


def settings():
    return load_settings(
        {
            "LIVE_AI_ENABLED": "true",
            "FOUNDRY_PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/demo",
            "FOUNDRY_AGENT_NAME": "coach",
            "FOUNDRY_AGENT_VERSION": "1",
            "MAX_INPUT_TOKENS": "20000",
            "MAX_OUTPUT_TOKENS": "2000",
            "STUDENT_DAILY_TOKEN_LIMIT": "44000",
            "PROJECT_DAILY_TOKEN_LIMIT": "88000",
            "MAX_INTERVIEW_QUESTIONS": "6",
            "MAX_ANSWER_CHARS": "10000",
        }
    )


class FakeProvider:
    def __init__(self, text=None, fail=False):
        self.text = text or json.dumps(
            {
                "answer": "A primary key identifies a row.",
                "citation_ids": ["source1"],
                "insufficient_evidence": False,
            }
        )
        self.fail, self.calls = fail, 0

    def prepare(self):
        return {}

    def generate(self, prompt, schema):
        self.calls += 1
        if self.fail:
            raise TimeoutError("uncertain dispatch")
        return ProviderReply("response1", self.text, 100)


@pytest.fixture
def store():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        session.add(Student(id="student1", auth_subject="test-subject", display_name="Demo"))
    return engine


def passage():
    return RetrievedPassage(
        citation_id="source1",
        text="A primary key identifies a row.",
        title="Keys",
        source_url="https://example.org/keys",
        locator="1",
        corpus_version="v1",
    )


def test_success_is_cached_without_second_call(store):
    provider = FakeProvider()
    coach = AICoach(settings(), store, provider)
    context = StudentContext(student_id="student1", state_version=0)
    first = coach.answer(context, "request1", "What is a primary key?", [passage()])
    second = coach.answer(context, "request1", "What is a primary key?", [passage()])
    assert first.status == RunStatus.SUCCEEDED
    assert first == second
    assert provider.calls == 1


def test_timeout_is_never_automatically_retried(store):
    provider = FakeProvider(fail=True)
    coach = AICoach(settings(), store, provider)
    context = StudentContext(student_id="student1", state_version=0)
    for _ in range(2):
        result = coach.answer(context, "request1", "keys", [passage()])
        assert result.status == RunStatus.UNKNOWN_USAGE
    assert provider.calls == 1


def test_invalid_citation_is_not_repaired(store):
    provider = FakeProvider(
        json.dumps({"answer": "claim", "citation_ids": ["invented"], "insufficient_evidence": False})
    )
    result = AICoach(settings(), store, provider).answer(
        StudentContext(student_id="student1", state_version=0), "request1", "keys", [passage()]
    )
    assert result.status == RunStatus.INVALID
    assert provider.calls == 1


def test_provider_pins_agent_and_uses_no_history():
    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(status="completed", output=[], id="r1", output_text="{}", usage=None)

    client = SimpleNamespace(responses=SimpleNamespace(create=create))
    definition = SimpleNamespace(kind="prompt", tools=[], model="deployment", instructions="safe")
    project = SimpleNamespace(
        agents=SimpleNamespace(
            get_version=lambda **kw: SimpleNamespace(definition=definition, version="1", name="coach")
        )
    )
    provider = FoundryProvider(settings(), project=project, client=client)
    provider.prepare()
    provider.generate("{}", {"type": "object", "properties": {}})
    assert captured["extra_body"]["agent_reference"]["version"] == "1"
    assert "output_contract" in captured["input"]
    assert "tools" not in captured and "tool_choice" not in captured
    assert "instructions" not in captured and "text" not in captured
    assert captured["store"] is False
    assert "conversation" not in captured and "previous_response_id" not in captured


def test_real_openai_sdk_http_retry_disabled():
    import httpx
    from openai import OpenAI, RateLimitError

    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(429, json={"error": {"message": "quota", "type": "rate_limit"}})

    with OpenAI(
        api_key="offline-test",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(respond)),
    ) as client:
        with pytest.raises(RateLimitError):
            client.responses.create(model="fake", input="test")
    assert len(requests) == 1
