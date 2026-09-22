"""Deterministic cross-record validation; these functions never invoke an LLM."""

from collections import defaultdict
from collections.abc import Mapping, Sequence, Set
from datetime import date
from math import isclose, isfinite

from placement_agent.domain.contracts import (
    EvaluationResult,
    GoalSpec,
    InterviewBatchResult,
    PlanDraft,
)


class PolicyViolation(ValueError):
    """Untrusted or stale output failed a business rule."""


def validate_evaluation(
    result: EvaluationResult,
    *,
    expected_attempt: str,
    expected_item: str,
    expected_dimensions: Set[str],
    expected_rubric_version: str,
    expected_agent_version: str,
    expected_prompt_version: str,
    answer: str,
    dimension_weights: Mapping[str, float] | None = None,
) -> None:
    if result.attempt_id != expected_attempt or result.item_id != expected_item:
        raise PolicyViolation("Evaluation does not match the submitted answer")
    if result.rubric_version != expected_rubric_version:
        raise PolicyViolation("Rubric version mismatch")
    if result.agent_version != expected_agent_version or result.prompt_version != expected_prompt_version:
        raise PolicyViolation("Evaluation provenance does not match server-known versions")
    if {d.dimension_id for d in result.dimensions} != expected_dimensions:
        raise PolicyViolation("Missing or unexpected rubric dimensions")
    weights = dict(dimension_weights) if dimension_weights is not None else dict.fromkeys(expected_dimensions, 1.0)
    if (
        set(weights) != expected_dimensions
        or any(not isfinite(w) or w < 0 for w in weights.values())
        or sum(weights.values()) <= 0
    ):
        raise PolicyViolation("Invalid frozen rubric weights")
    expected_score = sum(d.score * weights[d.dimension_id] for d in result.dimensions) / (4 * sum(weights.values()))
    if not isclose(result.normalized_score, expected_score, abs_tol=1e-6):
        raise PolicyViolation("Normalized score does not match frozen rubric aggregation")
    for dimension in result.dimensions:
        if any(not quote or quote not in answer for quote in dimension.answer_quotes):
            raise PolicyViolation("Feedback cites text not present in the answer")


def validate_interview_batch(
    result: InterviewBatchResult,
    *,
    session_id: str,
    input_hash: str,
    attempts_by_item: Mapping[str, str],
) -> None:
    if result.session_id != session_id or result.input_hash != input_hash:
        raise PolicyViolation("Evaluation batch does not match frozen submission")
    if {e.item_id: e.attempt_id for e in result.evaluations} != dict(attempts_by_item):
        raise PolicyViolation("Missing, unexpected or mismatched interview items")


def validate_plan(plan: PlanDraft, *, goal: GoalSpec, state_version: int, eligible_activity_ids: Set[str]) -> None:
    if plan.goal_id != goal.goal_id or plan.based_on_state_version != state_version:
        raise PolicyViolation("Plan is for another goal or stale student state")
    totals: dict[date, int] = defaultdict(int)
    for item in plan.items:
        if item.activity_id not in eligible_activity_ids:
            raise PolicyViolation("Unknown or ineligible activity")
        if item.scheduled_date > goal.deadline:
            raise PolicyViolation("Activity exceeds preparation deadline")
        totals[item.scheduled_date] += item.duration_minutes
    if any(minutes > goal.daily_minutes for minutes in totals.values()):
        raise PolicyViolation("Plan exceeds daily capacity")
    if sum(totals.values()) > goal.weekly_minutes:
        raise PolicyViolation("Plan exceeds weekly capacity")


def validate_citations(citation_ids: Sequence[str], supplied_ids: Set[str]) -> None:
    if not set(citation_ids).issubset(supplied_ids):
        raise PolicyViolation("Citation was not supplied in the retrieved context")


def validate_prerequisites(graph: Mapping[str, Sequence[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(skill: str) -> None:
        if skill in visiting:
            raise PolicyViolation("Cyclic skill prerequisites")
        if skill in visited:
            return
        if skill not in graph:
            raise PolicyViolation("Unknown prerequisite skill")
        visiting.add(skill)
        for dependency in graph[skill]:
            visit(dependency)
        visiting.remove(skill)
        visited.add(skill)

    for skill in graph:
        visit(skill)
