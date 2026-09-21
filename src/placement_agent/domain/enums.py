"""Stable business-state values shared by application boundaries."""

from enum import StrEnum


class SkillLevel(StrEnum):
    UNKNOWN = "unknown"
    DEVELOPING = "developing"
    WORKING = "working"
    STRONG = "strong"


class EvidenceKind(StrEnum):
    SELF_REPORT = "self_report"
    RESUME = "resume"
    REPOSITORY = "repository"
    COMPLETION = "completion"
    OBJECTIVE = "objective"
    RUBRIC = "rubric"
    STATIC_REVIEW = "static_review"


class Action(StrEnum):
    EXTRACT = "extract"
    LEARNING_ANSWER = "learning_answer"
    PLAN_EXPLANATION = "plan_explanation"
    PRACTICE_REVIEW = "practice_review"
    PROJECT_QUESTIONS = "project_questions"
    INTERVIEW_REPORT = "interview_report"


class RunStatus(StrEnum):
    RESERVED = "reserved"
    DISPATCHED = "dispatched"
    SUCCEEDED = "succeeded"
    INVALID = "invalid"
    UNKNOWN_USAGE = "unknown_usage"
    FAILED_BEFORE_DISPATCH = "failed_before_dispatch"
