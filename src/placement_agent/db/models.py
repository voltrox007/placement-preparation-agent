"""Initial relational schema. Private access must use scoped repositories."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """Persist UTC as SQLite datetime and restore an aware UTC value."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must be timezone aware")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return None if value is None else value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (CheckConstraint("state_version >= 0"),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    auth_subject: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str]
    state_version: Mapped[int] = mapped_column(default=0)


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("daily_minutes > 0 AND weekly_minutes > 0"),
        CheckConstraint("status IN ('active', 'archived')"),
        Index("one_active_goal", "student_id", unique=True, sqlite_where=text("status = 'active'")),
    )
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    role_id: Mapped[str]
    daily_minutes: Mapped[int]
    weekly_minutes: Mapped[int]
    status: Mapped[str] = mapped_column(default="active")


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    prompt: Mapped[str]
    skill_id: Mapped[str]
    rubric: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(default=1)


class AssessmentSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (CheckConstraint("kind IN ('diagnostic', 'practice', 'interview')"),)
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    kind: Mapped[str]
    status: Mapped[str] = mapped_column(default="in_progress")


class SessionItem(Base):
    __tablename__ = "session_items"
    __table_args__ = (UniqueConstraint("session_id", "sequence"), CheckConstraint("sequence >= 0"))
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    sequence: Mapped[int]
    frozen_prompt: Mapped[str]
    frozen_rubric: Mapped[dict] = mapped_column(JSON)


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (UniqueConstraint("student_id", "request_key"),)
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("session_items.id"))
    request_key: Mapped[str]
    answer: Mapped[str]
    submitted_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    execution_status: Mapped[str] = mapped_column(default="not_executed")


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (CheckConstraint("normalized_score >= 0 AND normalized_score <= 1"),)
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id"))
    supersedes_id: Mapped[str | None] = mapped_column(ForeignKey("evaluations.id"))
    normalized_score: Mapped[float]
    feedback: Mapped[str]
    rubric_version: Mapped[str]


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"
    __table_args__ = (UniqueConstraint("evaluation_id", "skill_id"),)
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    skill_id: Mapped[str]
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("evaluations.id"))
    evidence_type: Mapped[str]


class EvaluationBatch(Base):
    __tablename__ = "evaluation_batches"
    __table_args__ = (UniqueConstraint("student_id", "request_key"),)
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    request_key: Mapped[str]
    input_hash: Mapped[str]
    status: Mapped[str] = mapped_column(default="pending")
    final_report: Mapped[str | None]


class UsageReservation(Base):
    __tablename__ = "usage_reservations"
    __table_args__ = (
        UniqueConstraint("student_id", "request_key"),
        CheckConstraint("reserved_tokens >= 0 AND actual_tokens >= 0"),
        CheckConstraint(
            "(status = 'completed' AND actual_tokens IS NOT NULL) OR (status != 'completed' AND actual_tokens IS NULL)"
        ),
        CheckConstraint("status IN ('reserved', 'dispatched', 'unknown', 'completed', 'released')"),
        Index("usage_student_period", "student_id", "period"),
    )
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"))
    request_key: Mapped[str]
    input_hash: Mapped[str]
    action: Mapped[str]
    period: Mapped[str]
    reserved_tokens: Mapped[int]
    actual_tokens: Mapped[int | None]
    status: Mapped[str] = mapped_column(default="reserved")


class Profile(Base):
    __tablename__ = "profiles"
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), primary_key=True)
    education: Mapped[str] = mapped_column(default="")
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    category: Mapped[str]


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (CheckConstraint("duration_minutes > 0"),)
    id: Mapped[str] = mapped_column(primary_key=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"))
    title: Mapped[str]
    duration_minutes: Mapped[int]
    resource_url: Mapped[str]
    instructions: Mapped[str]


class LearningPlan(Base):
    __tablename__ = "learning_plans"
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    state_version: Mapped[int]
    status: Mapped[str] = mapped_column(default="active")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class PlanItem(Base):
    __tablename__ = "plan_items"
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    plan_id: Mapped[str] = mapped_column(ForeignKey("learning_plans.id"))
    activity_id: Mapped[str] = mapped_column(ForeignKey("activities.id"))
    scheduled_date: Mapped[str]
    status: Mapped[str] = mapped_column(default="planned")
    reason: Mapped[str]


class ProgressEvent(Base):
    __tablename__ = "progress_events"
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    event_type: Mapped[str]
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    kind: Mapped[str]
    content_hash: Mapped[str]
    text: Mapped[str]
    confirmed_facts: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    title: Mapped[str]
    description: Mapped[str]
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)


class AgentResult(Base):
    __tablename__ = "agent_results"
    __table_args__ = (UniqueConstraint("student_id", "request_key"),)
    id: Mapped[str] = mapped_column(primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    request_key: Mapped[str]
    input_hash: Mapped[str]
    result_json: Mapped[dict] = mapped_column(JSON)
