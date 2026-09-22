from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from placement_agent.db.models import Evaluation, EvaluationBatch, ProgressEvent, SkillEvidence
from placement_agent.db.repositories import ConflictError, NotFoundError
from placement_agent.db.session import create_sqlite_engine, run_migrations, session_factory
from placement_agent.services.preparation import PreparationService
from placement_agent.services.taxonomy import ROLE_TEMPLATES, map_job_description, validate_taxonomy


@pytest.fixture()
def service(tmp_path: Path):
    engine = create_sqlite_engine("sqlite:///" + (tmp_path / "workflows.db").as_posix())
    run_migrations(engine)
    result = PreparationService(session_factory(engine))
    result.ensure_student("student")
    yield result
    engine.dispose()


def _complete_diagnostic(service, answer_correct=True):
    session = service.start_session("student", "diagnostic")
    for item in session["items"]:
        answer = item["options"][0]
        if answer_correct:
            with service.factory() as db:
                from placement_agent.db.models import SessionItem

                frozen = db.get(SessionItem, item["id"]).frozen_rubric
                answer = frozen["options"][frozen["correct"]]
        service.submit_answer("student", item["id"], answer, f"answer:{item['id']}")
    return service.finish_session("student", session["id"])


def test_taxonomy_aliases_cycle_detection_and_confirmed_snapshot(service):
    draft = service.draft_job_requirements("We need Python3, PostgreSQL, testing, and Kubernetes.")
    assert draft["mapped_requirements"] == ["engineering", "python", "sql"]
    saved = service.confirm_job_requirements(
        "student",
        "We need Python3, PostgreSQL, testing, and Kubernetes.",
        draft,
        ["kubernetes"],
    )
    assert saved["confirmed_facts"]["confirmed"] is True
    assert saved["confirmed_facts"]["unresolved_requirements"] == ["kubernetes"]
    assert service.goal("student") is None
    service.set_goal("student")
    goal = service.goal("student")
    assert goal["requirements"]["version"] == "backend-v1"
    assert goal["requirements"]["provenance"] == "reviewed_role_template"
    cyclic = {
        "bad": {
            "requirements": ("a", "b"),
            "prerequisites": {"a": ("b",), "b": ("a",)},
        }
    }
    with pytest.raises(ValueError, match="cycle"):
        validate_taxonomy(cyclic)
    changed = {**draft, "mapped_requirements": ["dsa"]}
    with pytest.raises(ConflictError):
        service.confirm_job_requirements("student", "We need Python3, PostgreSQL, testing, and Kubernetes.", changed)


def test_diagnostic_resume_objective_scoring_and_invalidation(service):
    first = service.start_session("student", "diagnostic")
    item = first["items"][0]
    service.submit_answer("student", item["id"], item["options"][0], "stable-key")
    assert service.start_session("student", "diagnostic")["id"] == first["id"]
    assert service.submit_answer("student", item["id"], item["options"][0], "stable-key")["request_key"] == "stable-key"
    with pytest.raises(ConflictError):
        service.submit_answer("student", item["id"], item["options"][1], "stable-key")
    with service.factory() as db:
        evaluation = db.scalar(select(Evaluation))
        evaluation_id = evaluation.id
    service.invalidate_evaluation("student", evaluation_id, "Student disputed the answer key")
    assert all(evaluation_id not in row["evidence_ids"] for row in service.skill_summary("student"))
    service.invalidate_evaluation("student", evaluation_id, "Repeated click")
    with service.factory() as db:
        events = list(db.scalars(select(ProgressEvent).where(ProgressEvent.event_type == "evaluation_invalidated")))
    assert len(events) == 1


def test_plan_revision_preserves_completion_and_changes_after_evidence(service):
    service.set_goal("student", daily_minutes=30, weekly_minutes=120)
    plan = service.create_plan("student")
    assert len(plan["items"]) == 8
    completed = plan["items"][0]
    service.complete_activity("student", completed["id"])
    assert service.next_action("student")["plan_item_id"] != completed["id"]
    _complete_diagnostic(service)
    assert service.next_action("student")["stale"] is True
    revised = service.create_plan("student")
    preserved = [item for item in revised["items"] if item["activity_id"] == completed["activity_id"]]
    assert preserved and preserved[0]["status"] == "completed"
    assert service.next_action("student")["stale"] is False


def test_project_viva_is_frozen_reusable_and_scoped(service):
    project = service.save_project(
        "student", "Placement Agent", "I implemented the persistence layer.", {"commit": "abc", "paths": ["src/db.py"]}
    )
    first = service.prepare_project_viva("student", project["id"])
    second = service.prepare_project_viva("student", project["id"])
    assert first == second
    assert first["generation"] == "deterministic_template"
    assert len(first["questions"]) == 3
    assert all(question["evidence_refs"] == [project["id"]] for question in first["questions"])
    service.ensure_student("other")
    with pytest.raises(NotFoundError):
        service.prepare_project_viva("other", project["id"])


def test_one_shot_practice_report_is_persisted_once(service):
    session = service.start_session("student", "practice")
    item = session["items"][0]
    service.submit_answer("student", item["id"], "def first_unique(value): return None", "practice-answer")
    service.finish_session("student", session["id"])
    payload = service.session_feedback_payload("student", session["id"])
    frozen = payload["items"][0]
    result = {
        "status": "succeeded",
        "output": {
            "attempt_id": frozen["attempt_id"],
            "item_id": frozen["item_id"],
            "normalized_score": 0.5,
            "dimensions": [],
            "feedback": "Static review only; submitted code was not executed.",
            "uncertain": False,
            "rubric_version": "code-v1",
            "agent_version": "4",
            "prompt_version": "single-shot-v1",
            "execution_status": "not_executed",
        },
    }
    accepted = service.persist_session_feedback("student", session["id"], "feedback:practice", result)
    duplicate = service.persist_session_feedback("student", session["id"], "feedback:practice", result)
    assert accepted == duplicate
    with service.factory() as db:
        assert len(list(db.scalars(select(EvaluationBatch)))) == 1
        assert len(list(db.scalars(select(SkillEvidence)))) == 1
        evaluation = db.scalar(select(Evaluation))
        assert "not executed" in evaluation.feedback


def test_fixed_interview_batch_acceptance_requires_exact_items(service):
    session = service.start_session("student", "interview")
    for item in session["items"]:
        service.submit_answer("student", item["id"], "A bounded evidence-based answer.", f"i:{item['id']}")
    service.finish_session("student", session["id"])
    payload = service.session_feedback_payload("student", session["id"])
    evaluations = [
        {
            "attempt_id": item["attempt_id"],
            "item_id": item["item_id"],
            "normalized_score": 0.75,
            "dimensions": [],
            "feedback": "One-shot final review.",
            "rubric_version": "open-v1",
        }
        for item in payload["items"]
    ]
    result = {"status": "succeeded", "output": {"evaluations": evaluations, "report": "Final report"}}
    accepted = service.persist_session_feedback("student", session["id"], "feedback:interview", result)
    assert accepted["accepted"] is True
    with service.factory() as db:
        assert len(list(db.scalars(select(Evaluation)))) == len(payload["items"])
        assert db.scalar(select(EvaluationBatch)).final_report == "Final report"
    incomplete = {"status": "succeeded", "output": {"evaluations": evaluations[:-1], "report": "Bad"}}
    with pytest.raises(ValueError, match="exactly"):
        service.persist_session_feedback("student", session["id"], "feedback:bad", incomplete)


def test_map_job_description_is_stable():
    assert map_job_description("PYTHON and sql") == map_job_description("PYTHON and sql")
    assert "backend" in ROLE_TEMPLATES
