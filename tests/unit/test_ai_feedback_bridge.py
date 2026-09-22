from types import SimpleNamespace

import pytest

from placement_agent.services.ai_feedback import answer_learning, explain_next_action, request_session_feedback


class Service:
    def __init__(self):
        self.persisted = []

    def profile(self, student_id):
        return {"state_version": 3}

    def session_feedback_payload(self, student_id, session_id):
        return {
            "session_id": session_id,
            "kind": "practice",
            "input_hash": "a" * 64,
            "items": [
                {
                    "attempt_id": "attempt1",
                    "item_id": "item1",
                    "prompt": "Explain",
                    "answer": "My answer",
                    "rubric": {"dimensions": ["reasoning"], "version": "code-v1"},
                    "execution_status": "not_executed",
                }
            ],
        }

    def next_action(self, student_id):
        return {
            "action": "complete_activity",
            "plan_item_id": "item42",
            "activity_id": "activity7",
            "title": "Practice joins",
            "reason": "Lowest assessed skill",
        }

    def persist_session_feedback(self, student_id, session_id, request_key, result):
        self.persisted.append((student_id, session_id, request_key, result))


class Coach:
    def __init__(self):
        self.calls = []

    def review_code(self, context, request_key, payload):
        self.calls.append(("review", context, request_key, payload))
        return SimpleNamespace(model_dump=lambda **_: {"status": "succeeded"})

    def answer(self, context, request_key, query, passages):
        self.calls.append(("answer", context, request_key, query, passages))
        return SimpleNamespace(model_dump=lambda **_: {"status": "succeeded"})

    def explain_plan(self, context, request_key, payload):
        self.calls.append(("explain", context, request_key, payload))
        return SimpleNamespace(model_dump=lambda **_: {"status": "succeeded"})


class Retriever:
    def search(self, query, *, top):
        assert top == 5
        return [SimpleNamespace(citation_id="p1")]


@pytest.fixture(autouse=True)
def live_settings(monkeypatch):
    values = {
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
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_practice_bridge_makes_one_explicit_call_with_stable_key():
    coach = Coach()
    service = Service()
    result = request_session_feedback("student1", "session1", service=service, coach=coach)
    assert result == {"status": "succeeded"}
    assert len(coach.calls) == 1
    assert coach.calls[0][2] == "session-feedback:session1"
    assert coach.calls[0][1].state_version == 3
    assert len(service.persisted) == 1


def test_learning_bridge_retrieves_then_calls_once():
    coach = Coach()
    result = answer_learning(
        "student1",
        "What is a key?",
        "request1",
        service=Service(),
        coach=coach,
        retriever=Retriever(),
    )
    assert result["status"] == "succeeded"
    assert [call[0] for call in coach.calls] == ["answer"]


def test_learning_bridge_refuses_unconfigured_retrieval():
    with pytest.raises(ValueError, match="retrieval is not configured"):
        answer_learning("student1", "What is a key?", "request1", service=Service(), coach=Coach())


def test_partial_retrieval_configuration_is_rejected(monkeypatch):
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://search.example")
    with pytest.raises(ValueError, match="configuration must be complete"):
        answer_learning("student1", "What is a key?", "request1", service=Service(), coach=Coach())


def test_plan_explanation_calls_foundry_once_for_selected_activity():
    coach = Coach()
    result = explain_next_action("student1", "plan:item42:3", service=Service(), coach=coach)
    assert result == {"status": "succeeded"}
    assert [call[0] for call in coach.calls] == ["explain"]
    assert coach.calls[0][3]["activity_id"] == "activity7"
    assert coach.calls[0][3]["state_version"] == 3
