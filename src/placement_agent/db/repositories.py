"""Scoped access and conservative atomic admission for paid AI actions."""

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from .models import (
    AssessmentSession,
    Attempt,
    Goal,
    SessionItem,
    Student,
    UsageReservation,
    new_id,
    utc_now,
)


class NotFoundError(LookupError):
    """Same response for missing and unauthorized resources."""


class ConflictError(ValueError):
    pass


class BudgetExceededError(ValueError):
    pass


class StudentRepository:
    def __init__(self, session: Session, student_id: str):
        self.session = session
        self.student_id = student_id

    def get_student(self):
        result = self.session.get(Student, self.student_id)
        if result is None:
            raise NotFoundError("Resource unavailable")
        return result

    def create_goal(self, *, role_id: str, daily_minutes: int, weekly_minutes: int):
        self.get_student()
        goal = Goal(
            student_id=self.student_id,
            role_id=role_id,
            daily_minutes=daily_minutes,
            weekly_minutes=weekly_minutes,
        )
        self.session.add(goal)
        self.session.flush()
        return goal

    def get_session(self, session_id: str):
        result = self.session.scalar(
            select(AssessmentSession).where(
                AssessmentSession.id == session_id, AssessmentSession.student_id == self.student_id
            )
        )
        if result is None:
            raise NotFoundError("Resource unavailable")
        return result

    def submit_attempt(self, item_id: str, answer: str, request_key: str):
        item = self.session.scalar(
            select(SessionItem)
            .join(AssessmentSession, SessionItem.session_id == AssessmentSession.id)
            .where(SessionItem.id == item_id, AssessmentSession.student_id == self.student_id)
        )
        if item is None:
            raise NotFoundError("Resource unavailable")
        self.session.execute(
            insert(Attempt)
            .values(
                id=new_id(),
                student_id=self.student_id,
                item_id=item_id,
                answer=answer,
                request_key=request_key,
                submitted_at=utc_now(),
                execution_status="not_executed",
            )
            .on_conflict_do_nothing(index_elements=["student_id", "request_key"])
        )
        existing = self.session.scalar(
            select(Attempt).where(Attempt.student_id == self.student_id, Attempt.request_key == request_key)
        )
        if existing is not None:
            if existing.item_id != item_id or existing.answer != answer:
                raise ConflictError("Request key was reused with different input")
            return existing
        raise RuntimeError("Submission was not persisted")

    def bump_state(self, expected_version: int):
        result = self.session.execute(
            update(Student)
            .where(Student.id == self.student_id, Student.state_version == expected_version)
            .values(state_version=Student.state_version + 1)
        )
        if not isinstance(result, CursorResult) or result.rowcount != 1:
            raise ConflictError("Student state changed or is unavailable")
        return expected_version + 1


class BudgetRepository:
    """Each operation owns its transaction; never call a provider while it is open."""

    def __init__(self, engine):
        self.engine = engine

    def reserve(
        self,
        *,
        student_id: str,
        request_key: str,
        input_hash: str,
        action: str,
        period: str,
        tokens: int,
        call_limit: int,
        token_limit: int,
        project_call_limit: int,
        project_token_limit: int,
    ):
        if min(tokens, call_limit, token_limit, project_call_limit, project_token_limit) <= 0:
            raise ValueError("Reservation and budget limits must be positive")
        with self.engine.connect() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                with Session(bind=connection, expire_on_commit=False) as session:
                    existing = session.scalar(
                        select(UsageReservation).where(
                            UsageReservation.student_id == student_id,
                            UsageReservation.request_key == request_key,
                        )
                    )
                    if existing is not None:
                        if (
                            existing.input_hash,
                            existing.action,
                            existing.period,
                            existing.reserved_tokens,
                        ) != (input_hash, action, period, tokens):
                            raise ConflictError("Request key was reused with different input")
                        result = (existing.id, False)
                    else:
                        project_rows = session.scalars(
                            select(UsageReservation).where(
                                UsageReservation.period == period,
                                UsageReservation.status != "released",
                            )
                        ).all()
                        rows = [row for row in project_rows if row.student_id == student_id]

                        def usage(items):
                            return sum(
                                row.actual_tokens if row.status == "completed" else row.reserved_tokens for row in items
                            )

                        if (
                            len(rows) >= call_limit
                            or usage(rows) + tokens > token_limit
                            or len(project_rows) >= project_call_limit
                            or usage(project_rows) + tokens > project_token_limit
                        ):
                            raise BudgetExceededError("AI budget exhausted")
                        reservation = UsageReservation(
                            student_id=student_id,
                            request_key=request_key,
                            input_hash=input_hash,
                            action=action,
                            period=period,
                            reserved_tokens=tokens,
                        )
                        session.add(reservation)
                        session.flush()
                        result = (reservation.id, True)
                    connection.commit()
                    return result
            except Exception:
                connection.rollback()
                raise

    def mark_dispatched(self, *, student_id: str, reservation_id: str) -> bool:
        """Durable one-time dispatch claim; a crash afterwards conservatively spends budget."""
        with self.engine.begin() as connection:
            result = connection.execute(
                update(UsageReservation)
                .where(
                    UsageReservation.id == reservation_id,
                    UsageReservation.student_id == student_id,
                    UsageReservation.status == "reserved",
                )
                .values(status="dispatched")
            )
            return result.rowcount == 1

    def reconcile(
        self,
        *,
        student_id: str,
        reservation_id: str,
        actual_tokens: int | None = None,
        before_dispatch: bool = False,
    ):
        if actual_tokens is not None and actual_tokens < 0:
            raise ValueError("Usage cannot be negative")
        if before_dispatch and actual_tokens is not None:
            raise ValueError("A released reservation cannot have known usage")
        status = "released" if before_dispatch else "unknown" if actual_tokens is None else "completed"
        with self.engine.begin() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            row = (
                connection.execute(
                    select(UsageReservation.__table__).where(
                        UsageReservation.id == reservation_id,
                        UsageReservation.student_id == student_id,
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                raise NotFoundError("Resource unavailable")
            if row["status"] in {"completed", "released", "unknown"}:
                if row["status"] != status or row["actual_tokens"] != actual_tokens:
                    raise ConflictError("Reservation is already finalized")
                return
            if before_dispatch and row["status"] != "reserved":
                raise ConflictError("Dispatched usage cannot be released")
            if not before_dispatch and row["status"] != "dispatched":
                raise ConflictError("Usage cannot be recorded before dispatch")
            connection.execute(
                update(UsageReservation)
                .where(UsageReservation.id == reservation_id)
                .values(status=status, actual_tokens=actual_tokens)
            )
