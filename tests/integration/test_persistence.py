"""Requires SQLAlchemy and Alembic; uses a disposable local database."""

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from placement_agent.db.models import (
    AssessmentSession,
    Attempt,
    Base,
    Evaluation,
    Question,
    SessionItem,
    Student,
)
from placement_agent.db.repositories import (
    BudgetExceededError,
    BudgetRepository,
    ConflictError,
    NotFoundError,
    StudentRepository,
)
from placement_agent.db.session import create_sqlite_engine, session_factory, unit_of_work


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.url = "sqlite:///" + (Path(self.directory.name) / "test.db").as_posix()
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", self.url)
        command.upgrade(config, "head")
        self.engine = create_sqlite_engine(self.url)
        self.factory = session_factory(self.engine)
        with unit_of_work(self.factory) as session:
            session.add_all(
                [
                    Student(id="a", auth_subject="a", display_name="A"),
                    Student(id="b", auth_subject="b", display_name="B"),
                ]
            )
            session.flush()
            session.add(Question(id="q", prompt="Why?", skill_id="python", rubric={}))
            session.add(AssessmentSession(id="s", student_id="a", kind="diagnostic"))
            session.flush()
            session.add(
                SessionItem(
                    id="i",
                    session_id="s",
                    question_id="q",
                    sequence=0,
                    frozen_prompt="Why?",
                    frozen_rubric={},
                )
            )

    def tearDown(self):
        self.engine.dispose()
        self.directory.cleanup()

    def test_scoped_lookup_and_idempotent_submission(self):
        with unit_of_work(self.factory) as session:
            other = StudentRepository(session, "b")
            with self.assertRaises(NotFoundError):
                other.get_session("s")
            with self.assertRaises(NotFoundError):
                other.submit_attempt("i", "answer", "r")
            own = StudentRepository(session, "a")
            first = own.submit_attempt("i", "answer", "r")
            self.assertEqual(first.id, own.submit_attempt("i", "answer", "r").id)
            with self.assertRaises(ConflictError):
                own.submit_attempt("i", "changed", "r")

    def test_rollback_and_state_version(self):
        with self.assertRaises(RuntimeError):
            with unit_of_work(self.factory) as session:
                repo = StudentRepository(session, "a")
                repo.submit_attempt("i", "answer", "r")
                repo.bump_state(0)
                raise RuntimeError("simulate failure")
        with unit_of_work(self.factory) as session:
            self.assertIsNone(session.scalar(select(Attempt)))
            repo = StudentRepository(session, "a")
            self.assertEqual(repo.get_student().state_version, 0)
            self.assertEqual(repo.bump_state(0), 1)
            with self.assertRaises(ConflictError):
                repo.bump_state(0)

    def test_foreign_keys_and_one_active_goal(self):
        with self.assertRaises(IntegrityError):
            with unit_of_work(self.factory) as session:
                session.add(AssessmentSession(student_id="absent", kind="diagnostic"))
        with self.assertRaises(IntegrityError):
            with unit_of_work(self.factory) as session:
                repo = StudentRepository(session, "a")
                for _ in range(2):
                    repo.create_goal(role_id="backend", daily_minutes=30, weekly_minutes=150)

    def reserve(self, key):
        return BudgetRepository(self.engine).reserve(
            student_id="a",
            request_key=key,
            input_hash=key,
            action="feedback",
            period="2026-09-21",
            tokens=100,
            call_limit=1,
            token_limit=100,
            project_call_limit=10,
            project_token_limit=1000,
        )

    def test_atomic_budget_admission_and_duplicates(self):
        def worker(key):
            try:
                return self.reserve(key)
            except BudgetExceededError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(worker, ["one", "two"]))
        self.assertEqual(sum(result is not None for result in outcomes), 1)
        winner = "one" if outcomes[0] else "two"
        reservation_id, fresh = self.reserve(winner)
        self.assertFalse(fresh)
        budget = BudgetRepository(self.engine)
        self.assertTrue(budget.mark_dispatched(student_id="a", reservation_id=reservation_id))
        self.assertFalse(budget.mark_dispatched(student_id="a", reservation_id=reservation_id))
        budget.reconcile(student_id="a", reservation_id=reservation_id)
        with self.assertRaises(BudgetExceededError):
            self.reserve("three")
        with self.assertRaises(ConflictError):
            budget.reconcile(student_id="a", reservation_id=reservation_id, before_dispatch=True)
        with self.assertRaises(NotFoundError):
            budget.reconcile(student_id="b", reservation_id=reservation_id, actual_tokens=10)

    def test_known_usage_release_and_changed_request_conflict(self):
        reservation_id, _ = self.reserve("first")
        budget = BudgetRepository(self.engine)
        with self.assertRaises(ConflictError):
            budget.reserve(
                student_id="a",
                request_key="first",
                input_hash="changed",
                action="feedback",
                period="2026-09-21",
                tokens=100,
                call_limit=1,
                token_limit=100,
                project_call_limit=10,
                project_token_limit=1000,
            )
        budget.reconcile(student_id="a", reservation_id=reservation_id, before_dispatch=True)
        second, fresh = self.reserve("second")
        self.assertTrue(fresh)
        self.assertTrue(budget.mark_dispatched(student_id="a", reservation_id=second))
        budget.reconcile(student_id="a", reservation_id=second, actual_tokens=80)
        budget.reconcile(student_id="a", reservation_id=second, actual_tokens=80)
        with self.assertRaises(ConflictError):
            budget.reconcile(student_id="a", reservation_id=second, actual_tokens=90)
        with self.assertRaises(BudgetExceededError):
            self.reserve("third")

    def test_migration_round_trip(self):
        self.engine.dispose()
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", self.url)
        command.downgrade(config, "base")
        self.assertNotIn("students", inspect(self.engine).get_table_names())
        command.upgrade(config, "head")
        inspector = inspect(self.engine)
        self.assertEqual(set(Base.metadata.tables), set(inspector.get_table_names()) - {"alembic_version"})
        self.assertIn("input_hash", {column["name"] for column in inspector.get_columns("agent_results")})

    def test_cross_student_project_budget_is_atomic(self):
        def worker(student):
            try:
                return BudgetRepository(self.engine).reserve(
                    student_id=student,
                    request_key="shared",
                    input_hash="hash",
                    action="feedback",
                    period="day",
                    tokens=100,
                    call_limit=2,
                    token_limit=200,
                    project_call_limit=1,
                    project_token_limit=100,
                )
            except BudgetExceededError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, ["a", "b"]))
        self.assertEqual(sum(value is not None for value in results), 1)

    def test_dispatch_claim_and_unknown_usage_are_terminal(self):
        reservation_id, _ = self.reserve("claim")
        budget = BudgetRepository(self.engine)

        def claim(_):
            return budget.mark_dispatched(student_id="a", reservation_id=reservation_id)

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(claim, range(2))), 1)
        with self.assertRaises(ConflictError):
            budget.reconcile(student_id="a", reservation_id=reservation_id, before_dispatch=True)
        budget.reconcile(student_id="a", reservation_id=reservation_id)
        budget.reconcile(student_id="a", reservation_id=reservation_id)
        with self.assertRaises(ConflictError):
            budget.reconcile(student_id="a", reservation_id=reservation_id, actual_tokens=10)

    def test_concurrent_identical_and_conflicting_attempts(self):
        def submit(pair):
            key, answer = pair
            try:
                with unit_of_work(self.factory) as session:
                    return StudentRepository(session, "a").submit_attempt("i", answer, key).id
            except ConflictError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            same = list(pool.map(submit, [("same", "x"), ("same", "x")]))
            different = list(pool.map(submit, [("different", "x"), ("different", "y")]))
        self.assertEqual(same[0], same[1])
        self.assertEqual(sum(value is not None for value in different), 1)

    def test_timestamp_roundtrip_is_utc(self):
        value = datetime(2026, 9, 21, 12, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        with unit_of_work(self.factory) as session:
            attempt = StudentRepository(session, "a").submit_attempt("i", "x", "utc")
            attempt.submitted_at = value
            attempt_id = attempt.id
        with unit_of_work(self.factory) as session:
            actual = session.get(Attempt, attempt_id).submitted_at
            self.assertEqual(actual.tzinfo, UTC)
            self.assertEqual(actual, value.astimezone(UTC))

    def test_evaluation_history_can_supersede_same_attempt(self):
        with unit_of_work(self.factory) as session:
            attempt = StudentRepository(session, "a").submit_attempt("i", "x", "history")
            first = Evaluation(attempt_id=attempt.id, normalized_score=0.4, feedback="Initial", rubric_version="1")
            session.add(first)
            session.flush()
            second = Evaluation(
                attempt_id=attempt.id,
                normalized_score=0.7,
                feedback="Corrected",
                rubric_version="1",
                supersedes_id=first.id,
            )
            session.add(second)
        with unit_of_work(self.factory) as session:
            self.assertEqual(len(session.scalars(select(Evaluation)).all()), 2)


if __name__ == "__main__":
    unittest.main()
