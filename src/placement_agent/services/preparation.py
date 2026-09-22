"""Transactional learner workflows. No method here calls an LLM or executes code."""

import json
from datetime import date, timedelta
from hashlib import sha256

from sqlalchemy import delete, select

from placement_agent.db.models import (
    Activity,
    AgentResult,
    AssessmentSession,
    Attempt,
    Document,
    Evaluation,
    EvaluationBatch,
    Goal,
    LearningPlan,
    PlanItem,
    Profile,
    ProgressEvent,
    Project,
    Question,
    SessionItem,
    Skill,
    SkillEvidence,
    Student,
    UsageReservation,
)
from placement_agent.db.repositories import ConflictError, NotFoundError, StudentRepository
from placement_agent.db.session import unit_of_work

from .catalog import INTERVIEW, ITEMS, RESOURCES, SKILLS
from .taxonomy import map_job_description, role_snapshot


def _dict(row):
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        result[column.name] = value.isoformat() if hasattr(value, "isoformat") else value
    return result


class PreparationService:
    def __init__(self, factory):
        self.factory = factory
        self._seed()

    def _seed(self):
        with unit_of_work(self.factory) as db:
            for skill_id, name in SKILLS.items():
                if db.get(Skill, skill_id) is None:
                    db.add(Skill(id=skill_id, name=name, category="backend"))
            db.flush()
            for skill_id, entries in ITEMS.items():
                for index, (prompt, options, correct, explanation) in enumerate(entries):
                    qid = f"{skill_id}-{index + 1:02d}"
                    if db.get(Question, qid) is None:
                        db.add(
                            Question(
                                id=qid,
                                prompt=prompt,
                                skill_id=skill_id,
                                rubric={
                                    "kind": "objective",
                                    "options": options,
                                    "correct": correct,
                                    "explanation": explanation,
                                    "review_status": "human_reviewed_2026-09-22_Jiya-garg08",
                                    "subtopic": str(index // 2),
                                    "version": "1",
                                },
                            )
                        )
                for index, title in enumerate(
                    ["Read and summarize", "Practice core concepts", "Explain a worked example"]
                ):
                    aid = f"{skill_id}-activity-{index}"
                    if db.get(Activity, aid) is None:
                        db.add(
                            Activity(
                                id=aid,
                                skill_id=skill_id,
                                title=f"{name if False else SKILLS[skill_id]}: {title}",
                                duration_minutes=15,
                                resource_url=RESOURCES[skill_id],
                                instructions=(
                                    f"Spend 15 minutes on {SKILLS[skill_id].lower()}. "
                                    f"{title}, then record what remains unclear."
                                ),
                            )
                        )
            for index, (skill_id, prompt) in enumerate(INTERVIEW):
                qid = f"interview-{index}"
                if db.get(Question, qid) is None:
                    db.add(
                        Question(
                            id=qid,
                            prompt=prompt,
                            skill_id=skill_id,
                            rubric={
                                "kind": "open",
                                "dimensions": ["technical_accuracy", "reasoning", "clarity"],
                                "scale": "0–4 per dimension",
                                "review_status": "human_reviewed_2026-09-22_Jiya-garg08",
                            },
                        )
                    )
            if db.get(Question, "code-practice") is None:
                db.add(
                    Question(
                        id="code-practice",
                        skill_id="python",
                        prompt=(
                            "Write a Python function that returns the first non-repeated character "
                            "in a string, or None. "
                            "Explain its complexity and test cases."
                        ),
                        rubric={
                            "kind": "code",
                            "dimensions": ["reasoning", "edge_cases", "clarity"],
                            "execution_status": "not_executed",
                        },
                    )
                )

    def ensure_student(self, student_id="demo-student", display_name: str | None = None):
        if not student_id or len(student_id) > 200:
            raise ValueError("Invalid student identifier")
        resolved_name = display_name or ("Demo Student" if student_id == "demo-student" else "Student")
        if len(resolved_name) > 200:
            raise ValueError("Invalid display name")
        with unit_of_work(self.factory) as db:
            student = db.get(Student, student_id)
            if student is None:
                student = Student(id=student_id, auth_subject=student_id, display_name=resolved_name)
                db.add(student)
                db.flush()
                db.add(Profile(student_id=student_id, education="", preferences={}))
            return _dict(student)

    def profile(self, student_id):
        with self.factory() as db:
            student = StudentRepository(db, student_id).get_student()
            profile = db.get(Profile, student_id)
            return {
                "student_id": student_id,
                "display_name": student.display_name,
                "education": profile.education if profile else "",
                "preferences": profile.preferences if profile else {},
                "state_version": student.state_version,
            }

    def save_profile(self, student_id, display_name, education, daily_minutes=45, weekly_minutes=225):
        if not display_name.strip() or len(display_name) > 200 or len(education) > 5000:
            raise ValueError("Supply a name (up to 200 characters) and a bounded education description")
        self._capacity(daily_minutes, weekly_minutes)
        with unit_of_work(self.factory) as db:
            student = StudentRepository(db, student_id).get_student()
            student.display_name = display_name.strip()
            profile = db.get(Profile, student_id)
            if profile is None:
                profile = Profile(student_id=student_id)
                db.add(profile)
            profile.education = education.strip()
            profile.preferences = {"daily_minutes": daily_minutes, "weekly_minutes": weekly_minutes}
            student.state_version += 1
        return self.profile(student_id)

    @staticmethod
    def _capacity(daily_minutes, weekly_minutes):
        if not 1 <= daily_minutes <= 1440 or not 1 <= weekly_minutes <= daily_minutes * 7:
            raise ValueError("Weekly capacity must be positive and no greater than seven daily budgets")

    def goal(self, student_id):
        with self.factory() as db:
            StudentRepository(db, student_id).get_student()
            goal = db.scalar(select(Goal).where(Goal.student_id == student_id, Goal.status == "active"))
            return {**_dict(goal), "requirements": role_snapshot(goal.role_id)} if goal else None

    def set_goal(self, student_id, role_id="backend", daily_minutes=45, weekly_minutes=225):
        self._capacity(daily_minutes, weekly_minutes)
        if role_id != "backend":
            raise ValueError("The starter catalog supports the backend role only")
        with unit_of_work(self.factory) as db:
            student = StudentRepository(db, student_id).get_student()
            for old in db.scalars(select(Goal).where(Goal.student_id == student_id, Goal.status == "active")):
                old.status = "archived"
            db.flush()
            db.add(
                Goal(
                    student_id=student_id,
                    role_id=role_id,
                    daily_minutes=daily_minutes,
                    weekly_minutes=weekly_minutes,
                )
            )
            student.state_version += 1
        return self.goal(student_id)

    def skill_summary(self, student_id):
        with self.factory() as db:
            StudentRepository(db, student_id).get_student()
            return self._skills(db, student_id)

    @staticmethod
    def _skills(db, student_id):
        invalid = {
            row.details.get("evaluation_id")
            for row in db.scalars(
                select(ProgressEvent).where(
                    ProgressEvent.student_id == student_id,
                    ProgressEvent.event_type == "evaluation_invalidated",
                )
            )
        }
        rows = db.execute(
            select(
                Question.skill_id,
                Question.id,
                Evaluation.id,
                Evaluation.supersedes_id,
                Evaluation.normalized_score,
                Attempt.submitted_at,
            )
            .join(SessionItem, SessionItem.question_id == Question.id)
            .join(Attempt, Attempt.item_id == SessionItem.id)
            .join(Evaluation, Evaluation.attempt_id == Attempt.id)
            .where(Attempt.student_id == student_id)
            .order_by(Attempt.submitted_at)
        ).all()
        superseded = {row[3] for row in rows if row[3]}
        latest = {}
        for skill, question, evaluation_id, _, score, submitted_at in rows:
            if evaluation_id in invalid or evaluation_id in superseded:
                continue
            latest[(skill, question)] = (score, evaluation_id, submitted_at)
        result = []
        for skill, name in SKILLS.items():
            evidence = [value for (sid, _), value in latest.items() if sid == skill]
            scores = [value[0] for value in evidence]
            score = sum(scores) / len(scores) if scores else None
            if len(scores) < 3 or score is None:
                status = "unknown"
            elif score >= 0.8:
                status = "strong"
            elif score >= 0.6:
                status = "working"
            else:
                status = "developing"
            result.append(
                {
                    "skill_id": skill,
                    "name": name,
                    "status": status,
                    "score": score,
                    "evidence_count": len(scores),
                    "evidence_ids": [value[1] for value in evidence],
                    "reliability": "moderate" if len(scores) >= 3 else "low",
                    "policy": "heuristic-v1; content reviewed by Jiya-garg08 on 2026-09-22",
                }
            )
        return result

    def activities(self):
        with self.factory() as db:
            return [_dict(row) for row in db.scalars(select(Activity).order_by(Activity.id))]

    def create_plan(self, student_id):
        with unit_of_work(self.factory) as db:
            student = StudentRepository(db, student_id).get_student()
            goal = db.scalar(select(Goal).where(Goal.student_id == student_id, Goal.status == "active"))
            if goal is None:
                raise ValueError("Set a preparation goal first")
            current = db.scalar(
                select(LearningPlan).where(LearningPlan.student_id == student_id, LearningPlan.status == "active")
            )
            if current and current.state_version == student.state_version:
                return self._plan(db, current)
            completed = set()
            if current:
                completed = {
                    item.activity_id
                    for item in db.scalars(select(PlanItem).where(PlanItem.plan_id == current.id))
                    if item.status == "completed"
                }
                current.status = "archived"
            plan = LearningPlan(student_id=student_id, state_version=student.state_version)
            db.add(plan)
            db.flush()
            skills = sorted(
                self._skills(db, student_id),
                key=lambda row: (-1 if row["score"] is None else row["score"], row["skill_id"]),
            )
            candidates = []
            # Interleave topics rather than spending the entire week on the first unknown skill.
            for index in range(3):
                for skill in skills:
                    activity = db.get(Activity, f"{skill['skill_id']}-activity-{index}")
                    candidates.append((activity, skill))
            spent = 0
            day_spent = [0] * 7
            for activity, skill in candidates:
                if spent + activity.duration_minutes > goal.weekly_minutes:
                    break
                day = next(
                    (day for day in range(7) if day_spent[day] + activity.duration_minutes <= goal.daily_minutes),
                    None,
                )
                if day is None:
                    break
                reason = (
                    "Not sufficiently assessed; explore and diagnose"
                    if skill["status"] == "unknown"
                    else f"Observed performance {skill['score']:.0%}; reinforce this skill"
                )
                db.add(
                    PlanItem(
                        plan_id=plan.id,
                        activity_id=activity.id,
                        scheduled_date=(date.today() + timedelta(days=day)).isoformat(),
                        reason=reason,
                        status="completed" if activity.id in completed else "planned",
                    )
                )
                spent += activity.duration_minutes
                day_spent[day] += activity.duration_minutes
            db.add(
                ProgressEvent(
                    student_id=student_id,
                    event_type="plan_created",
                    details={"plan_id": plan.id, "minutes": spent},
                )
            )
            db.flush()
            return self._plan(db, plan)

    @staticmethod
    def _plan(db, plan):
        result = _dict(plan)
        result["items"] = []
        for item, activity in db.execute(
            select(PlanItem, Activity)
            .join(Activity)
            .where(PlanItem.plan_id == plan.id)
            .order_by(PlanItem.scheduled_date, PlanItem.id)
        ):
            result["items"].append({**_dict(activity), **_dict(item)})
        return result

    def get_plan(self, student_id):
        with self.factory() as db:
            StudentRepository(db, student_id).get_student()
            plan = db.scalar(
                select(LearningPlan).where(LearningPlan.student_id == student_id, LearningPlan.status == "active")
            )
            return self._plan(db, plan) if plan else None

    def complete_activity(self, student_id, item_id):
        with unit_of_work(self.factory) as db:
            item = db.scalar(
                select(PlanItem).join(LearningPlan).where(PlanItem.id == item_id, LearningPlan.student_id == student_id)
            )
            if item is None:
                raise NotFoundError("Resource unavailable")
            if item.status != "completed":
                item.status = "completed"
                db.add(
                    ProgressEvent(
                        student_id=student_id,
                        event_type="activity_completed",
                        details={"item_id": item_id, "mastery_changed": False},
                    )
                )

    def next_action(self, student_id):
        """Return a deterministic recommendation without changing state or calling AI."""
        with self.factory() as db:
            student = StudentRepository(db, student_id).get_student()
            plan = db.scalar(
                select(LearningPlan).where(LearningPlan.student_id == student_id, LearningPlan.status == "active")
            )
            if plan is None:
                return {"action": "create_plan", "reason": "No active learning plan", "stale": False}
            item = db.scalar(
                select(PlanItem)
                .where(PlanItem.plan_id == plan.id, PlanItem.status == "planned")
                .order_by(PlanItem.scheduled_date, PlanItem.id)
            )
            if item is None:
                return {"action": "revise_plan", "reason": "All planned activities are complete", "stale": True}
            activity = db.get(Activity, item.activity_id)
            return {
                "action": "complete_activity",
                "plan_item_id": item.id,
                "activity_id": activity.id,
                "title": activity.title,
                "reason": item.reason,
                "stale": plan.state_version != student.state_version,
            }

    def start_session(self, student_id, kind="diagnostic"):
        if kind not in {"diagnostic", "practice", "interview"}:
            raise ValueError("Unsupported session kind")
        with unit_of_work(self.factory) as db:
            StudentRepository(db, student_id).get_student()
            current = db.scalar(
                select(AssessmentSession).where(
                    AssessmentSession.student_id == student_id,
                    AssessmentSession.kind == kind,
                    AssessmentSession.status == "in_progress",
                )
            )
            if current:
                return self._session(db, current)
            session = AssessmentSession(student_id=student_id, kind=kind)
            db.add(session)
            db.flush()
            ids = (
                [f"{skill}-{index:02d}" for index in range(1, 4) for skill in SKILLS]
                if kind == "diagnostic"
                else [f"interview-{index}" for index in range(len(INTERVIEW))]
                if kind == "interview"
                else ["code-practice"]
            )
            for sequence, qid in enumerate(ids):
                question = db.get(Question, qid)
                db.add(
                    SessionItem(
                        session_id=session.id,
                        question_id=qid,
                        sequence=sequence,
                        frozen_prompt=question.prompt,
                        frozen_rubric={**question.rubric, "skill_id": question.skill_id},
                    )
                )
            db.flush()
            return self._session(db, session)

    @staticmethod
    def _session(db, session):
        result = _dict(session)
        result["items"] = []
        scores = []
        for item in db.scalars(
            select(SessionItem).where(SessionItem.session_id == session.id).order_by(SessionItem.sequence)
        ):
            attempt = db.scalar(select(Attempt).where(Attempt.item_id == item.id).order_by(Attempt.submitted_at.desc()))
            evaluation = None
            if attempt:
                evaluations = list(db.scalars(select(Evaluation).where(Evaluation.attempt_id == attempt.id)))
                superseded = {row.supersedes_id for row in evaluations if row.supersedes_id}
                invalid = {
                    row.details.get("evaluation_id")
                    for row in db.scalars(
                        select(ProgressEvent).where(
                            ProgressEvent.student_id == session.student_id,
                            ProgressEvent.event_type == "evaluation_invalidated",
                        )
                    )
                }
                evaluation = next(
                    (row for row in reversed(evaluations) if row.id not in superseded and row.id not in invalid), None
                )
            if evaluation:
                scores.append(evaluation.normalized_score)
            result["items"].append(
                {
                    "id": item.id,
                    "prompt": item.frozen_prompt,
                    "skill_id": item.frozen_rubric.get("skill_id"),
                    "options": item.frozen_rubric.get("options", []),
                    "answer": attempt.answer if attempt else None,
                    "score": evaluation.normalized_score if evaluation else None,
                    "feedback": evaluation.feedback if evaluation else None,
                    "execution_status": "not_executed",
                }
            )
        result["answered"] = sum(item["answer"] is not None for item in result["items"])
        result["total"] = len(result["items"])
        result["score"] = sum(scores) / len(scores) if scores else None
        return result

    def invalidate_evaluation(self, student_id, evaluation_id, reason):
        if not reason.strip() or len(reason) > 1000:
            raise ValueError("Provide a reason up to 1,000 characters")
        with unit_of_work(self.factory) as db:
            evaluation = db.scalar(
                select(Evaluation).join(Attempt).where(Evaluation.id == evaluation_id, Attempt.student_id == student_id)
            )
            if evaluation is None:
                raise NotFoundError("Resource unavailable")
            duplicate = next(
                (
                    row
                    for row in db.scalars(
                        select(ProgressEvent).where(
                            ProgressEvent.student_id == student_id,
                            ProgressEvent.event_type == "evaluation_invalidated",
                        )
                    )
                    if row.details.get("evaluation_id") == evaluation_id
                ),
                None,
            )
            if duplicate is None:
                db.add(
                    ProgressEvent(
                        student_id=student_id,
                        event_type="evaluation_invalidated",
                        details={"evaluation_id": evaluation_id, "reason": reason.strip()},
                    )
                )
                StudentRepository(db, student_id).get_student().state_version += 1

    def persist_session_feedback(self, student_id, session_id, request_key, result):
        """Atomically accept one validated AI report into evaluation history."""
        if result.get("status") != "succeeded" or not result.get("output"):
            return {"accepted": False, "reason": "No validated successful report"}
        output = result["output"]
        evaluations = output.get("evaluations") or [output]
        with unit_of_work(self.factory) as db:
            session = StudentRepository(db, student_id).get_session(session_id)
            if session.status != "completed":
                raise ConflictError("Complete the session before accepting feedback")
            existing = db.scalar(
                select(EvaluationBatch).where(
                    EvaluationBatch.student_id == student_id, EvaluationBatch.request_key == request_key
                )
            )
            if existing:
                return {"accepted": existing.status == "accepted", "batch_id": existing.id}
            snapshot = self.session_feedback_payload(student_id, session_id)
            expected = {item["item_id"]: item for item in snapshot["items"]}
            if {item["item_id"] for item in evaluations} != set(expected):
                raise ValueError("Feedback does not cover the frozen session exactly")
            batch = EvaluationBatch(
                student_id=student_id,
                session_id=session_id,
                request_key=request_key,
                input_hash=snapshot["input_hash"],
                status="accepted",
                final_report=output.get("report", output.get("feedback", "")),
            )
            db.add(batch)
            for accepted in evaluations:
                frozen = expected[accepted["item_id"]]
                evaluation = Evaluation(
                    attempt_id=frozen["attempt_id"],
                    normalized_score=accepted["normalized_score"],
                    feedback=accepted["feedback"],
                    rubric_version=accepted["rubric_version"],
                )
                db.add(evaluation)
                db.flush()
                db.add(
                    SkillEvidence(
                        student_id=student_id,
                        skill_id=frozen["rubric"].get("skill_id", self._item_skill(db, frozen["item_id"])),
                        evaluation_id=evaluation.id,
                        evidence_type="static_review" if session.kind == "practice" else "rubric",
                    )
                )
            StudentRepository(db, student_id).get_student().state_version += 1
            db.flush()
            return {"accepted": True, "batch_id": batch.id}

    @staticmethod
    def _item_skill(db, item_id):
        return db.scalar(select(Question.skill_id).join(SessionItem).where(SessionItem.id == item_id))

    def get_session(self, student_id, session_id):
        with self.factory() as db:
            session = StudentRepository(db, student_id).get_session(session_id)
            return self._session(db, session)

    def session_feedback_payload(self, student_id, session_id):
        """Return an immutable, ownership-scoped snapshot for one explicit AI request."""
        with self.factory() as db:
            session = StudentRepository(db, student_id).get_session(session_id)
            if session.status != "completed":
                raise ConflictError("Complete the session before requesting feedback")
            items = []
            for item in db.scalars(
                select(SessionItem).where(SessionItem.session_id == session.id).order_by(SessionItem.sequence)
            ):
                attempt = db.scalar(
                    select(Attempt).where(Attempt.item_id == item.id).order_by(Attempt.submitted_at.desc())
                )
                if attempt is None:
                    raise ConflictError("Completed session has a missing answer")
                rubric = item.frozen_rubric
                if rubric.get("kind") not in {"open", "code"}:
                    continue
                items.append(
                    {
                        "attempt_id": attempt.id,
                        "item_id": item.id,
                        "prompt": item.frozen_prompt,
                        "answer": attempt.answer,
                        "rubric": {
                            "dimensions": rubric["dimensions"],
                            "version": f"{rubric.get('kind', 'open')}-v1",
                        },
                        "execution_status": "not_executed",
                    }
                )
            snapshot = {"session_id": session.id, "kind": session.kind, "items": items}
            snapshot["input_hash"] = sha256(
                json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
            ).hexdigest()
            return snapshot

    def submit_answer(self, student_id, item_id, answer, request_key):
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 20000 or not request_key:
            raise ValueError("Provide a nonempty answer up to 20,000 characters and a request key")
        with unit_of_work(self.factory) as db:
            repo = StudentRepository(db, student_id)
            item = db.scalar(
                select(SessionItem)
                .join(AssessmentSession)
                .where(SessionItem.id == item_id, AssessmentSession.student_id == student_id)
            )
            if item is None:
                raise NotFoundError("Resource unavailable")
            previous = db.scalar(
                select(Attempt).where(Attempt.student_id == student_id, Attempt.request_key == request_key)
            )
            if previous:
                if previous.item_id != item_id or previous.answer != answer:
                    raise ConflictError("Request key reused with different input")
                return _dict(previous)
            session = repo.get_session(item.session_id)
            if session.status != "in_progress":
                raise ConflictError("Session is already complete")
            if db.scalar(select(Attempt).where(Attempt.item_id == item_id)):
                raise ConflictError("This item already has a submitted answer")
            rubric = item.frozen_rubric
            if rubric.get("kind") == "objective" and answer not in rubric["options"]:
                raise ValueError("Choose one of the supplied options")
            attempt = repo.submit_attempt(item_id, answer, request_key)
            if rubric.get("kind") == "objective":
                score = float(answer == rubric["options"][rubric["correct"]])
                evaluation = Evaluation(
                    attempt_id=attempt.id,
                    normalized_score=score,
                    feedback=rubric["explanation"],
                    rubric_version="objective-v1",
                )
                db.add(evaluation)
                db.flush()
                db.add(
                    SkillEvidence(
                        student_id=student_id,
                        skill_id=rubric["skill_id"],
                        evaluation_id=evaluation.id,
                        evidence_type="objective",
                    )
                )
                repo.get_student().state_version += 1
            db.add(
                ProgressEvent(
                    student_id=student_id,
                    event_type="answer_submitted",
                    details={"session_id": session.id, "item_id": item.id, "kind": session.kind},
                )
            )
            return _dict(attempt)

    def finish_session(self, student_id, session_id):
        with unit_of_work(self.factory) as db:
            session = StudentRepository(db, student_id).get_session(session_id)
            result = self._session(db, session)
            if result["answered"] != result["total"]:
                raise ValueError("Answer every fixed question before completing the session")
            if session.status != "completed":
                session.status = "completed"
                db.add(
                    ProgressEvent(
                        student_id=student_id,
                        event_type="session_completed",
                        details={"session_id": session.id, "kind": session.kind},
                    )
                )
            return self._session(db, session)

    def progress(self, student_id):
        with self.factory() as db:
            StudentRepository(db, student_id).get_student()
            return {
                "skills": self._skills(db, student_id),
                "events": [
                    _dict(row)
                    for row in db.scalars(
                        select(ProgressEvent)
                        .where(ProgressEvent.student_id == student_id)
                        .order_by(ProgressEvent.created_at.desc())
                        .limit(100)
                    )
                ],
                "sessions": [
                    self._session(db, row)
                    for row in db.scalars(select(AssessmentSession).where(AssessmentSession.student_id == student_id))
                ],
                "next_action": self.next_action(student_id),
            }

    def draft_job_requirements(self, text):
        if not text.strip() or len(text) > 100000:
            raise ValueError("Provide a job description up to 100,000 characters")
        return map_job_description(text)

    def confirm_job_requirements(self, student_id, text, draft, unresolved_requirements=None):
        expected = map_job_description(text)
        if draft.get("mapped_requirements") != expected["mapped_requirements"]:
            raise ConflictError("Job-description draft no longer matches the source text")
        facts = {
            **expected,
            "confirmed": True,
            "unresolved_requirements": sorted(set(unresolved_requirements or [])),
        }
        return self.save_document(student_id, "job_description", text, facts)

    def save_document(self, student_id, kind, text, confirmed_facts=None):
        if kind not in {"resume", "job_description"} or not text.strip() or len(text) > 100000:
            raise ValueError("Invalid document kind or text length")
        with unit_of_work(self.factory) as db:
            student = StudentRepository(db, student_id).get_student()
            document = Document(
                student_id=student_id,
                kind=kind,
                text=text,
                content_hash=sha256(text.encode()).hexdigest(),
                confirmed_facts=confirmed_facts or {},
            )
            db.add(document)
            student.state_version += 1
            db.flush()
            return _dict(document)

    def documents(self, student_id):
        with self.factory() as db:
            StudentRepository(db, student_id).get_student()
            return [_dict(row) for row in db.scalars(select(Document).where(Document.student_id == student_id))]

    def save_project(self, student_id, title, description, evidence=None):
        if not title.strip() or len(title) > 200 or len(description) > 20000:
            raise ValueError("Invalid project title or description")
        with unit_of_work(self.factory) as db:
            student = StudentRepository(db, student_id).get_student()
            project = Project(student_id=student_id, title=title, description=description, evidence=evidence or {})
            db.add(project)
            student.state_version += 1
            db.flush()
            return _dict(project)

    def projects(self, student_id):
        with self.factory() as db:
            StudentRepository(db, student_id).get_student()
            return [_dict(row) for row in db.scalars(select(Project).where(Project.student_id == student_id))]

    def prepare_project_viva(self, student_id, project_id):
        """Freeze a reusable zero-call question batch tied to the saved project snapshot."""
        with unit_of_work(self.factory) as db:
            project = db.scalar(select(Project).where(Project.id == project_id, Project.student_id == student_id))
            if project is None:
                raise NotFoundError("Resource unavailable")
            evidence = dict(project.evidence or {})
            source_evidence = {key: value for key, value in evidence.items() if key != "viva_batch"}
            source_hash = sha256(
                json.dumps(
                    {
                        "title": project.title,
                        "description": project.description,
                        "evidence": source_evidence,
                    },
                    sort_keys=True,
                    default=str,
                ).encode()
            ).hexdigest()
            batch = evidence.get("viva_batch")
            if batch and batch.get("source_hash") == source_hash:
                return batch
            questions = [
                {
                    "id": f"{project.id}:viva:{index}",
                    "prompt": prompt.format(title=project.title),
                    "evidence_refs": [project.id],
                    "rubric": ["technical_accuracy", "reasoning", "clarity"],
                }
                for index, prompt in enumerate(
                    (
                        "Describe your contribution to {title}; separate your work from the team's work.",
                        "Explain one technical decision in {title} and the evidence that supported it.",
                        "Describe a limitation or failure mode in {title} and how you would verify a fix.",
                    ),
                    1,
                )
            ]
            batch = {
                "version": "project-viva-template-v1",
                "source_hash": source_hash,
                "project_id": project.id,
                "questions": questions,
                "generation": "deterministic_template",
            }
            evidence["viva_batch"] = batch
            project.evidence = evidence
            db.add(
                ProgressEvent(
                    student_id=student_id,
                    event_type="project_viva_prepared",
                    details={"project_id": project.id, "source_hash": source_hash},
                )
            )
            return batch

    def export_student(self, student_id):
        with self.factory() as db:
            StudentRepository(db, student_id).get_student()
            tables = {}
            tables[Student.__tablename__] = [_dict(db.get(Student, student_id))]
            for model in [
                Profile,
                Goal,
                SkillEvidence,
                AssessmentSession,
                Attempt,
                LearningPlan,
                ProgressEvent,
                Document,
                Project,
                AgentResult,
                UsageReservation,
                EvaluationBatch,
            ]:
                tables[model.__tablename__] = [
                    _dict(row)
                    for row in db.scalars(
                        select(model).where(model.student_id == student_id)  # type: ignore[attr-defined]
                    )
                ]
            session_ids = [row["id"] for row in tables["sessions"]]
            plan_ids = [row["id"] for row in tables["learning_plans"]]
            attempt_ids = [row["id"] for row in tables["attempts"]]
            for model, field, ids in [
                (SessionItem, SessionItem.session_id, session_ids),
                (PlanItem, PlanItem.plan_id, plan_ids),
                (Evaluation, Evaluation.attempt_id, attempt_ids),
            ]:
                tables[model.__tablename__] = [_dict(row) for row in db.scalars(select(model).where(field.in_(ids)))]
            return {"schema_version": 2, "student_id": student_id, "tables": tables}

    def delete_student(self, student_id):
        with unit_of_work(self.factory) as db:
            StudentRepository(db, student_id).get_student()
            sessions = select(AssessmentSession.id).where(AssessmentSession.student_id == student_id)
            attempts = select(Attempt.id).where(Attempt.student_id == student_id)
            plans = select(LearningPlan.id).where(LearningPlan.student_id == student_id)
            for model, condition in [
                (SkillEvidence, SkillEvidence.student_id == student_id),
                (Evaluation, Evaluation.attempt_id.in_(attempts)),
                (Attempt, Attempt.student_id == student_id),
                (SessionItem, SessionItem.session_id.in_(sessions)),
                (EvaluationBatch, EvaluationBatch.student_id == student_id),
                (AssessmentSession, AssessmentSession.student_id == student_id),
                (PlanItem, PlanItem.plan_id.in_(plans)),
                (LearningPlan, LearningPlan.student_id == student_id),
                (ProgressEvent, ProgressEvent.student_id == student_id),
                (Document, Document.student_id == student_id),
                (Project, Project.student_id == student_id),
                (AgentResult, AgentResult.student_id == student_id),
                (UsageReservation, UsageReservation.student_id == student_id),
                (Goal, Goal.student_id == student_id),
                (Profile, Profile.student_id == student_id),
                (Student, Student.id == student_id),
            ]:
                db.execute(delete(model).where(condition))
        return {
            "deleted": True,
            "scope": "local application database; provider-side retention follows Azure policy",
        }
