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
                                    "review_status": "agent_authored_needs_human_review",
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
                                "review_status": "agent_authored_needs_human_review",
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

    def ensure_student(self, student_id="demo-student"):
        if not student_id or len(student_id) > 200:
            raise ValueError("Invalid student identifier")
        with unit_of_work(self.factory) as db:
            student = db.get(Student, student_id)
            if student is None:
                student = Student(id=student_id, auth_subject=student_id, display_name="Demo Student")
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
            return _dict(goal) if goal else None

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
        rows = db.execute(
            select(Question.skill_id, Question.id, Evaluation.normalized_score, Attempt.submitted_at)
            .join(SessionItem, SessionItem.question_id == Question.id)
            .join(Attempt, Attempt.item_id == SessionItem.id)
            .join(Evaluation, Evaluation.attempt_id == Attempt.id)
            .where(Attempt.student_id == student_id)
            .order_by(Attempt.submitted_at)
        ).all()
        latest = {}
        for skill, question, score, _ in rows:
            latest[(skill, question)] = score
        result = []
        for skill, name in SKILLS.items():
            scores = [score for (sid, _), score in latest.items() if sid == skill]
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
                    "reliability": "moderate" if len(scores) >= 3 else "low",
                    "policy": "heuristic-v1; agent-authored question bank, human review pending",
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
            if current:
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
            evaluation = db.scalar(select(Evaluation).where(Evaluation.attempt_id == attempt.id)) if attempt else None
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
            }

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
