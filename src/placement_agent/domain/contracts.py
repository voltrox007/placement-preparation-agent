"""Strict boundary models. Ownership and catalog membership remain service checks."""

from datetime import date, datetime, timedelta
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from placement_agent.domain.enums import Action, EvidenceKind, RunStatus, SkillLevel

Identifier = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")]
Text = Annotated[str, Field(min_length=1, max_length=20000)]
Score = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Version = Annotated[int, Field(ge=0)]
ContentHash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class StudentContext(Contract):
    """Construct only from verified server identity, never a model or user payload."""

    student_id: Identifier
    state_version: Version


class SourceSpan(Contract):
    document_id: Identifier
    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(gt=0)]
    quote: Annotated[str, Field(min_length=1, max_length=4000)]

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        if self.end <= self.start:
            raise ValueError("Source end must follow start")
        return self


class ProfileFact(Contract):
    field: Annotated[str, Field(min_length=1, max_length=80)]
    value: Annotated[str, Field(min_length=1, max_length=2000)]
    source: SourceSpan | None = None
    uncertain: bool = False


class ProfileDraft(Contract):
    document_id: Identifier
    facts: Annotated[tuple[ProfileFact, ...], Field(max_length=100)]


class ConfirmedProfile(Contract):
    student_id: Identifier
    revision: Version
    facts: Annotated[tuple[ProfileFact, ...], Field(max_length=100)]
    confirmed_at: datetime

    @field_validator("confirmed_at")
    @classmethod
    def utc_confirmation(cls, value: datetime) -> datetime:
        return require_utc(value)


class GoalSpec(Contract):
    goal_id: Identifier
    role_id: Identifier
    deadline: date
    daily_minutes: Annotated[int, Field(ge=1, le=1440)]
    weekly_minutes: Annotated[int, Field(ge=1, le=10080)]
    requirement_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def consistent_capacity(self) -> Self:
        if self.weekly_minutes > self.daily_minutes * 7:
            raise ValueError("Weekly capacity exceeds seven daily capacities")
        if len(set(self.requirement_ids)) != len(self.requirement_ids):
            raise ValueError("Requirement IDs must be unique")
        return self


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("Timestamp must be timezone-aware UTC")
    return value


class EvidenceRecord(Contract):
    evidence_id: Identifier
    student_id: Identifier
    skill_id: Identifier
    kind: EvidenceKind
    source_id: Identifier
    observed_at: datetime
    evaluation_id: Identifier | None = None
    score: Score | None = None
    valid: bool = True

    @field_validator("observed_at")
    @classmethod
    def utc_observation(cls, value: datetime) -> datetime:
        return require_utc(value)

    @model_validator(mode="after")
    def performance_needs_evaluation(self) -> Self:
        performance = {EvidenceKind.OBJECTIVE, EvidenceKind.RUBRIC, EvidenceKind.STATIC_REVIEW}
        if self.kind in performance and self.evaluation_id is None:
            raise ValueError("Performance evidence requires an evaluation reference")
        if self.kind not in performance and self.score is not None:
            raise ValueError("Claims and completion cannot carry a mastery score")
        return self


class SkillState(Contract):
    skill_id: Identifier
    level: SkillLevel = SkillLevel.UNKNOWN
    score: Score | None = None
    reliability: Literal["low", "moderate", "high"] = "low"
    subtopics: Annotated[tuple[Identifier, ...], Field(max_length=100)] = ()
    distinct_questions: Annotated[int, Field(ge=0)] = 0
    computed_version: Version = 0

    @model_validator(mode="after")
    def unknown_is_not_zero(self) -> Self:
        if self.level is SkillLevel.UNKNOWN and self.score is not None:
            raise ValueError("Unknown skill must not have an observed aggregate score")
        if self.level is not SkillLevel.UNKNOWN and self.score is None:
            raise ValueError("Assessed skill requires an observed score")
        return self


class QuestionSnapshot(Contract):
    """Student-visible DTO: deliberately excludes answer keys and grading rubrics."""

    item_id: Identifier
    skill_id: Identifier
    subtopic_id: Identifier
    prompt: Text
    question_version: Identifier
    evidence_ids: Annotated[tuple[Identifier, ...], Field(max_length=20)] = ()


class RubricDimension(Contract):
    dimension_id: Identifier
    score: Annotated[int, Field(ge=0, le=4)]
    feedback: Annotated[str, Field(min_length=1, max_length=4000)]
    answer_quotes: Annotated[tuple[Annotated[str, Field(min_length=1, max_length=2000)], ...], Field(max_length=8)] = ()


class EvaluationResult(Contract):
    attempt_id: Identifier
    item_id: Identifier
    normalized_score: Score
    dimensions: Annotated[tuple[RubricDimension, ...], Field(min_length=1, max_length=12)]
    feedback: Annotated[str, Field(min_length=1, max_length=6000)]
    uncertain: bool
    rubric_version: Identifier
    agent_version: Identifier
    prompt_version: Identifier
    execution_status: Literal["not_executed"] = "not_executed"

    @model_validator(mode="after")
    def unique_dimensions(self) -> Self:
        ids = [dimension.dimension_id for dimension in self.dimensions]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate rubric dimension")
        return self


class InterviewBatchResult(Contract):
    session_id: Identifier
    input_hash: ContentHash
    evaluations: Annotated[tuple[EvaluationResult, ...], Field(min_length=1, max_length=12)]
    report: Annotated[str, Field(min_length=1, max_length=12000)]

    @model_validator(mode="after")
    def unique_items_and_attempts(self) -> Self:
        for values in (
            [e.item_id for e in self.evaluations],
            [e.attempt_id for e in self.evaluations],
        ):
            if len(values) != len(set(values)):
                raise ValueError("Duplicate interview item or attempt")
        return self


class PlanItem(Contract):
    activity_id: Identifier
    scheduled_date: date
    duration_minutes: Annotated[int, Field(ge=1, le=1440)]


class PlanDraft(Contract):
    goal_id: Identifier
    based_on_state_version: Version
    starts_on: date
    items: Annotated[tuple[PlanItem, ...], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def seven_day_horizon(self) -> Self:
        if any(not self.starts_on <= item.scheduled_date < self.starts_on + timedelta(days=7) for item in self.items):
            raise ValueError("Plan item outside seven-day horizon")
        return self


class RetrievedPassage(Contract):
    citation_id: Identifier
    text: Annotated[str, Field(min_length=1, max_length=8000)]
    title: Annotated[str, Field(min_length=1, max_length=300)]
    source_url: Annotated[str, Field(min_length=1, max_length=2048, pattern=r"^https://")]
    locator: Annotated[str, Field(min_length=1, max_length=300)]
    corpus_version: Identifier


class UsageReservation(Contract):
    student_id: Identifier
    request_key: Identifier
    input_hash: ContentHash
    action: Action
    budget_date: date
    reserved_calls: Literal[1] = 1
    reserved_tokens: Annotated[int, Field(gt=0)]
    status: RunStatus = RunStatus.RESERVED
    actual_tokens: Annotated[int, Field(ge=0)] | None = None


class GroundedAnswer(Contract):
    answer: Text
    citation_ids: Annotated[tuple[Identifier, ...], Field(max_length=20)]
    insufficient_evidence: bool = False


class QuestionBatch(Contract):
    questions: Annotated[tuple[QuestionSnapshot, ...], Field(min_length=1, max_length=12)]


class Recommendation(Contract):
    activity_id: Identifier
    based_on_state_version: Version
    rationale: Annotated[str, Field(min_length=1, max_length=4000)]
    evidence_ids: Annotated[tuple[Identifier, ...], Field(max_length=20)]


class AgentTaskResult(Contract):
    action: Action
    request_key: Identifier
    status: RunStatus
    provider_id: Identifier | None = None
    output: (
        ProfileDraft | GroundedAnswer | EvaluationResult | InterviewBatchResult | QuestionBatch | Recommendation | None
    ) = None
    actual_tokens: Annotated[int, Field(ge=0)] | None = None
    error_code: Identifier | None = None

    @model_validator(mode="after")
    def successful_output_only(self) -> Self:
        if self.status is RunStatus.SUCCEEDED:
            if self.output is None or self.provider_id is None or self.error_code is not None:
                raise ValueError("Success requires provider ID and output without error")
            expected_types = {
                Action.EXTRACT: ProfileDraft,
                Action.LEARNING_ANSWER: GroundedAnswer,
                Action.PRACTICE_REVIEW: EvaluationResult,
                Action.INTERVIEW_REPORT: InterviewBatchResult,
                Action.PROJECT_QUESTIONS: QuestionBatch,
                Action.PLAN_EXPLANATION: Recommendation,
            }
            if not isinstance(self.output, expected_types[self.action]):
                raise ValueError("Output contract does not match the requested action")
        elif self.output is not None:
            raise ValueError("Non-success must not expose an accepted output")
        return self
