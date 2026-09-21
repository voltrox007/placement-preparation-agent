# Student state, database, and contracts

## Student Preparation Profile

Store profile, goals, confirmed resume facts, projects and contribution claims, repository snapshots, skill evidence, question/answer/evaluation history, learning completion, preferences, accepted plans, and progress. "Placement Twin" is an optional product name for this evidence model.

Self-report/resume = claim. Repository excerpt = evidence of repository content, not authorship. Activity completion = history, not mastery. Reviewed objective answers = measured performance on mapped concepts. AI rubric feedback = provisional performance evidence. Static code review does not establish executable correctness.

Skill summaries contain level (`unknown/developing/working/strong`), observed score when justified, subtopic coverage, distinct evidence count, reliability, timestamps, contradictions, and next diagnostic need. Unknown is not zero.

Aggregate latest eligible attempts per distinct reviewed question, cap repeated-session influence, separate assisted/repeated performance from first attempts, and require minimum coverage before assigning a level. Version weights/thresholds and calibrate them; an initial policy may require three distinct questions across two subtopics. Mark evidence stale instead of assuming automatic forgetting. Raw evidence remains recomputable.

## Tables

All owned entities carry or resolve a student FK; IDs are application-generated and timestamps UTC.

| Table | Important columns / relationships |
|---|---|
| students | id, unique auth_subject, display_name, consent_version, state_version |
| profiles | student_id PK/FK, education, graduation_year, preferences JSON |
| roles | id, name, description, template_version |
| goals | id, student_id, role_id, deadline, daily/weekly minutes, status, source document |
| skills | id, canonical_name unique, category, aliases |
| skill_prerequisites | skill_id/prerequisite_skill_id composite key; reject cycles |
| role_requirements | role/skill, target_level, importance, version |
| goal_requirements | goal/skill, confirmed target/importance, provenance |
| documents | id, student_id, kind, storage key, hash/version, parse status, draft JSON |
| projects | id, student_id, title, confirmed description/contribution, document FK |
| repositories | id, student_id, project FK, owner/name, URL |
| repository_snapshots | repository FK, commit SHA, fetched_at, bounded artifact manifest |
| skill_evidence | student/skill FKs, type, source refs, evaluation FK, validity, supersedes |
| student_skill_state | student/skill key, level, score, coverage, reliability, computed version |
| questions | kind, prompt, primary skill/subtopic, difficulty, private key/rubric, version/review status |
| sessions | student, diagnostic/practice/interview kind, goal, status, configuration snapshot |
| session_items | session/sequence unique, question FK, frozen prompt/rubric and evidence refs |
| attempts | item FK, answer/code, submitted_at, assistance flags, request key, execution_status |
| evaluations | attempt FK, evaluator, scores/feedback, validity, agent/prompt/rubric version, supersedes |
| evaluation_batches | session FK, frozen input hash, request key, run FK, status, final report |
| activities | kind, skill, duration, difficulty, resource/question refs, prerequisites/version |
| learning_plans | student/goal, version, status, based_on_state_version |
| plan_items | plan/activity FKs, date, duration, status, completed_at |
| recommendations | student, eligible activity, evidence refs, reason codes, optional explanation, state_version |
| progress_events | student, event type, related entity, old/new summary, timestamp |
| knowledge_sources | title, URL, permitted-use record, hash/version, reviewed_at, status |
| ingestion_runs | corpus version, status, counts, error summary |
| agent_runs | student, action, provider IDs, input hash, version fields, usage/latency/status, request key |
| usage_reservations | run/request key, student, budget period, reserved tokens/calls, known usage, reconciliation status |
| agent_conversations | optional student/purpose, remote ID, expiry/deletion status |
| deletion_jobs | student reference, resource manifest, progress/retry state |

One interview final response maps to a batch and multiple per-answer evaluations. Validate the whole bounded batch before applying evidence. This avoids one model call per answer.

## Integrity and writes

Enable foreign keys for every connection. Use local WAL, short transactions, busy timeout, unique request keys, one active goal/accepted plan, and optimistic student-state versions. Index student/time, student/skill, session sequence, and operation request keys. Keep local data outside synced/network directories.

Valid evaluation → evaluation/evidence insert → affected skill recomputation → progress event → state-version increment, in one transaction. External provider calls occur outside the database transaction, with a durable prior operation/usage reservation. Corrections supersede history. Deletions follow the retention workflow.

## Contracts

StudentContext; ProfileDraft with source spans; ConfirmedProfile; GoalSpec; EvidenceRecord; SkillState; QuestionSnapshot; EvaluationResult; InterviewBatchResult; PlanDraft; Recommendation; RetrievedPassage; UsageReservation; AgentTaskResult.

Reject unknown IDs, out-of-range rubric scores, over-capacity plans, missing citations, fabricated test status, malformed batches, and stale state writes. JSON is for bounded versioned payloads, not a replacement for relational ownership and foreign keys.

SQLite backup uses the supported backup API. Do not blindly copy a live database or share it across replicas. PostgreSQL is a future migration before horizontal scaling.
