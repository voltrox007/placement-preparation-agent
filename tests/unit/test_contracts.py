"""Boundary and cross-record safety cases; run with unittest or pytest."""

import json
import unittest
from datetime import date, datetime, timezone

from pydantic import ValidationError

from placement_agent.domain.contracts import (
    AgentTaskResult, EvidenceRecord, EvaluationResult, GoalSpec, InterviewBatchResult,
    PlanDraft, PlanItem, QuestionSnapshot, RubricDimension, SkillState, StudentContext,
)
from placement_agent.domain.enums import Action, EvidenceKind, RunStatus, SkillLevel
from placement_agent.domain.policies import (
    PolicyViolation, validate_citations, validate_evaluation, validate_interview_batch,
    validate_plan, validate_prerequisites,
)


def evaluation(item: str = "item1", attempt: str = "attempt1") -> EvaluationResult:
    return EvaluationResult(
        item_id=item, attempt_id=attempt, normalized_score=0.5,
        dimensions=(RubricDimension(dimension_id="accuracy", score=2, feedback="Partially supported", answer_quotes=("index",)),),
        feedback="Explain the index tradeoff", uncertain=True, rubric_version="r1",
        agent_version="a1", prompt_version="p1",
    )


class ContractTests(unittest.TestCase):
    def test_rejects_extra_provider_fields_and_coerced_state(self):
        for payload in ({"student_id": "a", "state_version": "0"}, {"student_id": "a", "state_version": 0, "admin": True}):
            with self.assertRaises(ValidationError):
                StudentContext.model_validate(payload)

    def test_unknown_is_not_zero(self):
        self.assertIsNone(SkillState(skill_id="sql").score)
        with self.assertRaises(ValidationError):
            SkillState(skill_id="sql", score=0.0)
        with self.assertRaises(ValidationError):
            SkillState(skill_id="sql", level=SkillLevel.STRONG)

    def test_claims_cannot_be_scored(self):
        with self.assertRaises(ValidationError):
            EvidenceRecord(evidence_id="e1", student_id="s1", skill_id="sql", kind=EvidenceKind.RESUME,
                           source_id="doc1", observed_at=datetime.now(timezone.utc), score=1.0)

    def test_performance_requires_evaluation_and_utc(self):
        base = dict(evidence_id="e1", student_id="s1", skill_id="sql", kind=EvidenceKind.OBJECTIVE,
                    source_id="a1", observed_at=datetime.now(timezone.utc))
        with self.assertRaises(ValidationError):
            EvidenceRecord(**base)
        base.update(evaluation_id="eval1", observed_at=datetime.now())
        with self.assertRaises(ValidationError):
            EvidenceRecord(**base)

    def test_display_question_cannot_contain_answer_key(self):
        with self.assertRaises(ValidationError):
            QuestionSnapshot.model_validate(dict(item_id="i1", skill_id="sql", subtopic_id="indexes", prompt="Explain", question_version="v1", answer_key="hidden"))

    def test_provider_cannot_claim_code_execution(self):
        payload = json.loads(evaluation().model_dump_json())
        payload["execution_status"] = "tests_passed"
        with self.assertRaises(ValidationError):
            EvaluationResult.model_validate_json(json.dumps(payload))

    def test_non_finite_score_rejected(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1):
            with self.assertRaises(ValidationError):
                evaluation().model_validate({**evaluation().model_dump(), "normalized_score": value})

    def test_batch_rejects_duplicates(self):
        with self.assertRaises(ValidationError):
            InterviewBatchResult(session_id="s1", input_hash="a"*64, evaluations=(evaluation(), evaluation()), report="Feedback")

    def test_batch_matches_exact_frozen_attempts(self):
        batch = InterviewBatchResult(session_id="s1", input_hash="a"*64, evaluations=(evaluation(),), report="Feedback")
        validate_interview_batch(batch, session_id="s1", input_hash="a"*64, attempts_by_item={"item1": "attempt1"})
        for expected in ({"item1": "other"}, {"item1": "attempt1", "item2": "attempt2"}, {}):
            with self.assertRaises(PolicyViolation):
                validate_interview_batch(batch, session_id="s1", input_hash="a"*64, attempts_by_item=expected)

    def test_rubric_and_answer_evidence_checked(self):
        kwargs = dict(expected_attempt="attempt1", expected_item="item1", expected_dimensions={"accuracy"}, expected_rubric_version="r1", expected_agent_version="a1", expected_prompt_version="p1", answer="Use an index")
        validate_evaluation(evaluation(), **kwargs)
        with self.assertRaises(PolicyViolation):
            validate_evaluation(evaluation(), **{**kwargs, "answer": "unrelated"})
        with self.assertRaises(PolicyViolation):
            validate_evaluation(evaluation(), **{**kwargs, "expected_dimensions": {"clarity"}})
        with self.assertRaises(PolicyViolation):
            validate_evaluation(evaluation(), **{**kwargs, "expected_agent_version": "different"})
        inflated = EvaluationResult(**{**evaluation().model_dump(), "normalized_score": 1.0})
        with self.assertRaises(PolicyViolation):
            validate_evaluation(inflated, **kwargs)
        with self.assertRaises(PolicyViolation):
            validate_evaluation(evaluation(), **kwargs, dimension_weights={"accuracy": 0.0})

    def test_oversized_answer_quote_rejected(self):
        with self.assertRaises(ValidationError):
            RubricDimension(dimension_id="accuracy", score=2, feedback="Review", answer_quotes=("x" * 2001,))

    def test_success_requires_typed_action_output(self):
        for output in ("not JSON", "", {}, {"unexpected": "value"}):
            with self.assertRaises(ValidationError):
                AgentTaskResult(action=Action.PRACTICE_REVIEW, request_key="r1", status=RunStatus.SUCCEEDED, provider_id="provider1", output=output)
        success = AgentTaskResult(action=Action.PRACTICE_REVIEW, request_key="r1", status=RunStatus.SUCCEEDED, provider_id="provider1", output=evaluation())
        self.assertIsInstance(success.output, EvaluationResult)
        with self.assertRaises(ValidationError):
            AgentTaskResult(action=Action.INTERVIEW_REPORT, request_key="r1", status=RunStatus.SUCCEEDED, provider_id="provider1", output=evaluation())

    def test_plan_checks_capacity_and_state(self):
        goal = GoalSpec(goal_id="g1", role_id="backend", deadline=date(2026,10,1), daily_minutes=45, weekly_minutes=180, requirement_ids=("sql",))
        plan = PlanDraft(goal_id="g1", based_on_state_version=1, starts_on=date(2026,9,21), items=(PlanItem(activity_id="a1", scheduled_date=date(2026,9,21), duration_minutes=30),))
        validate_plan(plan, goal=goal, state_version=1, eligible_activity_ids={"a1"})
        with self.assertRaises(PolicyViolation):
            validate_plan(plan, goal=goal, state_version=2, eligible_activity_ids={"a1"})
        overloaded = PlanDraft(**{**plan.model_dump(), "items": plan.items * 2})
        with self.assertRaises(PolicyViolation):
            validate_plan(overloaded, goal=goal, state_version=1, eligible_activity_ids={"a1"})

    def test_citation_membership_and_prerequisite_cycles(self):
        validate_citations(["c1"], {"c1"})
        with self.assertRaises(PolicyViolation):
            validate_citations(["invented"], {"c1"})
        validate_prerequisites({"sql": (), "indexes": ("sql",)})
        for graph in ({"a": ("b",), "b": ("a",)}, {"a": ("missing",)}):
            with self.assertRaises(PolicyViolation):
                validate_prerequisites(graph)

    def test_failed_run_cannot_publish_output(self):
        with self.assertRaises(ValidationError):
            AgentTaskResult(action=Action.PRACTICE_REVIEW, request_key="r1", status=RunStatus.INVALID, output=evaluation())


if __name__ == "__main__":
    unittest.main()
