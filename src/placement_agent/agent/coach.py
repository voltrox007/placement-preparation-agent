"""Budgeted single-shot tasks with durable duplicate suppression and strict outputs."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, cast

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from placement_agent.config import Settings
from placement_agent.db.models import AgentResult, Student
from placement_agent.db.repositories import BudgetRepository, ConflictError, NotFoundError
from placement_agent.domain.contracts import (
    AgentTaskResult,
    EvaluationResult,
    GroundedAnswer,
    InterviewBatchResult,
    ProfileDraft,
    QuestionBatch,
    Recommendation,
    RetrievedPassage,
    StudentContext,
)
from placement_agent.domain.enums import Action, RunStatus
from placement_agent.domain.policies import validate_citations, validate_evaluation

from .client import INSTRUCTIONS, FoundryProvider

PROMPT_VERSION = "single-shot-v1"
OUTPUTS: dict[Action, type[BaseModel]] = {
    Action.EXTRACT: ProfileDraft,
    Action.LEARNING_ANSWER: GroundedAnswer,
    Action.PRACTICE_REVIEW: EvaluationResult,
    Action.INTERVIEW_REPORT: InterviewBatchResult,
    Action.PROJECT_QUESTIONS: QuestionBatch,
    Action.PLAN_EXPLANATION: Recommendation,
}


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Responses strict schemas require every object property to be required."""
    schema = model.model_json_schema()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)
    return schema


class AICoach:
    def __init__(self, settings: Settings, engine: Any, provider: Any = None):
        self.settings, self.engine, self.provider = settings, engine, provider
        self.budget = BudgetRepository(engine)

    def extract(self, context: StudentContext, request_key: str, document_id: str, text: str) -> AgentTaskResult:
        return self._run(context, request_key, Action.EXTRACT, {"document_id": document_id, "text": text})

    def answer(
        self,
        context: StudentContext,
        request_key: str,
        query: str,
        passages: list[RetrievedPassage],
    ) -> AgentTaskResult:
        return self._run(
            context,
            request_key,
            Action.LEARNING_ANSWER,
            {"query": query, "passages": [p.model_dump(mode="json") for p in passages]},
        )

    def review_code(self, context: StudentContext, request_key: str, payload: dict[str, Any]) -> AgentTaskResult:
        return self._run(context, request_key, Action.PRACTICE_REVIEW, payload)

    def interview_report(self, context: StudentContext, request_key: str, payload: dict[str, Any]) -> AgentTaskResult:
        return self._run(context, request_key, Action.INTERVIEW_REPORT, payload)

    def question_batch(self, context: StudentContext, request_key: str, project: dict[str, Any]) -> AgentTaskResult:
        return self._run(context, request_key, Action.PROJECT_QUESTIONS, project)

    def _validate(self, output: Any, payload: dict[str, Any], action: Action) -> None:
        if action == Action.LEARNING_ANSWER:
            validate_citations(output.citation_ids, {p["citation_id"] for p in payload["passages"]})
            if not output.insufficient_evidence and not output.citation_ids:
                raise ValueError("Educational answer requires evidence citations")
        elif action == Action.EXTRACT:
            if output.document_id != payload["document_id"]:
                raise ValueError("Wrong extraction document")
            for fact in output.facts:
                span = fact.source
                if span is None or span.document_id != payload["document_id"]:
                    raise ValueError("Extracted fact requires source provenance")
                if payload["text"][span.start : span.end] != span.quote:
                    raise ValueError("Extraction span does not match input")
        elif action == Action.PRACTICE_REVIEW:
            self._validate_review(output, payload)
        elif action == Action.INTERVIEW_REPORT:
            items = payload["items"]
            if output.session_id != payload["session_id"] or output.input_hash != payload["input_hash"]:
                raise ValueError("Report does not match frozen interview")
            expected = {item["item_id"]: item for item in items}
            if {e.item_id for e in output.evaluations} != set(expected):
                raise ValueError("Report must evaluate exactly the frozen items")
            for evaluation in output.evaluations:
                self._validate_review(evaluation, expected[evaluation.item_id])
        elif action == Action.PROJECT_QUESTIONS:
            evidence = set(payload.get("evidence_ids", []))
            skills = set(payload.get("skill_ids", []))
            if len(output.questions) > (self.settings.max_interview_questions or 12):
                raise ValueError("Question batch too large")
            for question in output.questions:
                if not question.evidence_ids or not set(question.evidence_ids) <= evidence:
                    raise ValueError("Question has unsupported project evidence")
                if question.skill_id not in skills:
                    raise ValueError("Question has unknown skill")

    def _validate_review(self, output: EvaluationResult, payload: dict[str, Any]) -> None:
        rubric = payload["rubric"]
        validate_evaluation(
            output,
            expected_attempt=payload["attempt_id"],
            expected_item=payload["item_id"],
            expected_dimensions=set(rubric["dimensions"]),
            expected_rubric_version=rubric["version"],
            expected_agent_version=self.settings.foundry_agent_version,
            expected_prompt_version=PROMPT_VERSION,
            answer=payload["answer"],
            dimension_weights=rubric.get("weights"),
        )

    def _run(
        self, context: StudentContext, request_key: str, action: Action, payload: dict[str, Any]
    ) -> AgentTaskResult:
        # Serialization creates a stable snapshot: no conversation IDs or prior answers are appended.
        envelope = {
            "action": action.value,
            "state_version": context.state_version,
            "agent_version": self.settings.foundry_agent_version,
            "prompt_version": PROMPT_VERSION,
            "input": payload,
        }
        prompt = json.dumps(envelope, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        digest = hashlib.sha256(prompt.encode()).hexdigest()
        with Session(self.engine) as session:
            student = session.get(Student, context.student_id)
            if student is None:
                raise NotFoundError("Resource unavailable")
            cached = session.scalar(
                select(AgentResult).where(
                    AgentResult.student_id == context.student_id,
                    AgentResult.request_key == request_key,
                )
            )
            if cached:
                if cached.input_hash != digest:
                    raise ConflictError("Request key reused with different input")
                return AgentTaskResult.model_validate_json(json.dumps(cached.result_json))
            if student.state_version != context.state_version:
                raise ConflictError("Student state changed")
        if not self.settings.live_ai_enabled:
            return AgentTaskResult(
                action=action,
                request_key=request_key,
                status=RunStatus.FAILED_BEFORE_DISPATCH,
                error_code="live_ai_disabled",
            )
        schema = strict_schema(OUTPUTS[action])
        input_limit = self.settings.max_input_tokens
        output_limit = self.settings.max_output_tokens
        assert input_limit and output_limit
        provider = self.provider or FoundryProvider(self.settings)
        provider.prepare()
        # UTF-8 bytes plus generous framing allowance is intentionally conservative.
        estimated = (
            len(prompt.encode())
            + len(json.dumps(schema).encode())
            + len(INSTRUCTIONS.encode())
            + getattr(provider, "instructions_bytes", 0)
            + 1024
        )
        if estimated > input_limit:
            raise ValueError("Input exceeds conservative token admission limit; shorten submission")
        reserved = input_limit + output_limit
        student_limit = self.settings.student_daily_token_limit
        project_limit = self.settings.project_daily_token_limit
        assert student_limit and project_limit
        reservation_id, _ = self.budget.reserve(
            student_id=context.student_id,
            request_key=request_key,
            input_hash=digest,
            action=action.value,
            period=datetime.now(UTC).date().isoformat(),
            tokens=reserved,
            call_limit=max(1, student_limit // reserved),
            token_limit=student_limit,
            project_call_limit=max(1, project_limit // reserved),
            project_token_limit=project_limit,
        )
        if not self.budget.mark_dispatched(student_id=context.student_id, reservation_id=reservation_id):
            return AgentTaskResult(
                action=action,
                request_key=request_key,
                status=RunStatus.UNKNOWN_USAGE,
                error_code="already_dispatched",
            )
        actual: int | None = None
        try:
            reply = provider.generate(prompt, schema)
            actual = reply.actual_tokens
            if len(reply.text) > 100000:
                raise ValueError("Provider output exceeds limit")
            output = OUTPUTS[action].model_validate_json(reply.text)
            self._validate(output, payload, action)
            result = AgentTaskResult(
                action=action,
                request_key=request_key,
                status=RunStatus.SUCCEEDED,
                provider_id=reply.provider_id,
                output=cast(Any, output),
                actual_tokens=actual,
            )
        except Exception:
            result = AgentTaskResult(
                action=action,
                request_key=request_key,
                status=RunStatus.INVALID if actual is not None else RunStatus.UNKNOWN_USAGE,
                actual_tokens=actual,
                error_code="provider_or_output_failure",
            )
        finally:
            self.budget.reconcile(student_id=context.student_id, reservation_id=reservation_id, actual_tokens=actual)
            if self.provider is None:
                provider.close()
        with Session(self.engine) as session, session.begin():
            session.add(
                AgentResult(
                    student_id=context.student_id,
                    request_key=request_key,
                    input_hash=digest,
                    result_json=result.model_dump(mode="json"),
                )
            )
        return result
