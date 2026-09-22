"""Initial subset: assessment ownership and paid-action reservations.

This is intentionally a fixed schema snapshot, independent of future ORM models.
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def ident():
    return sa.Column("id", sa.String(), primary_key=True)


def owner():
    return sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False)


def string(name):
    return sa.Column(name, sa.String(), nullable=False)


def upgrade():
    op.create_table("students", ident(), string("auth_subject"), string("display_name"),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("auth_subject"), sa.CheckConstraint("state_version >= 0"))
    op.create_table("goals", ident(), owner(), string("role_id"),
        sa.Column("daily_minutes", sa.Integer(), nullable=False),
        sa.Column("weekly_minutes", sa.Integer(), nullable=False), string("status"),
        sa.CheckConstraint("daily_minutes > 0 AND weekly_minutes > 0"),
        sa.CheckConstraint("status IN ('active', 'archived')"))
    op.create_index("one_active_goal", "goals", ["student_id"], unique=True,
                    sqlite_where=sa.text("status = 'active'"))
    op.create_table("questions", ident(), string("prompt"), string("skill_id"),
        sa.Column("rubric", sa.JSON(), nullable=False), sa.Column("version", sa.Integer(), nullable=False))
    op.create_table("sessions", ident(), owner(), string("kind"), string("status"),
        sa.CheckConstraint("kind IN ('diagnostic', 'practice', 'interview')"))
    op.create_table("session_items", ident(),
        sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("question_id", sa.String(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False), string("frozen_prompt"),
        sa.Column("frozen_rubric", sa.JSON(), nullable=False),
        sa.UniqueConstraint("session_id", "sequence"), sa.CheckConstraint("sequence >= 0"))
    op.create_table("attempts", ident(), owner(),
        sa.Column("item_id", sa.String(), sa.ForeignKey("session_items.id"), nullable=False),
        string("request_key"), string("answer"),
        sa.Column("submitted_at", sa.DateTime(), nullable=False), string("execution_status"),
        sa.UniqueConstraint("student_id", "request_key"))
    op.create_table("evaluations", ident(),
        sa.Column("attempt_id", sa.String(), sa.ForeignKey("attempts.id"), nullable=False),
        sa.Column("normalized_score", sa.Float(), nullable=False), string("feedback"),
        string("rubric_version"),
        sa.Column("supersedes_id", sa.String(), sa.ForeignKey("evaluations.id"), nullable=True),
        sa.CheckConstraint("normalized_score >= 0 AND normalized_score <= 1"))
    op.create_table("skill_evidence", ident(), owner(), string("skill_id"),
        sa.Column("evaluation_id", sa.String(), sa.ForeignKey("evaluations.id"), nullable=False),
        string("evidence_type"), sa.UniqueConstraint("evaluation_id", "skill_id"))
    op.create_table("evaluation_batches", ident(), owner(),
        sa.Column("session_id", sa.String(), sa.ForeignKey("sessions.id"), nullable=False),
        string("request_key"), string("input_hash"), string("status"),
        sa.Column("final_report", sa.String(), nullable=True), sa.UniqueConstraint("student_id", "request_key"))
    op.create_table("usage_reservations", ident(), owner(), string("request_key"),
        string("input_hash"), string("action"), string("period"),
        sa.Column("reserved_tokens", sa.Integer(), nullable=False),
        sa.Column("actual_tokens", sa.Integer(), nullable=True), string("status"),
        sa.UniqueConstraint("student_id", "request_key"),
        sa.CheckConstraint("reserved_tokens >= 0 AND actual_tokens >= 0"),
        sa.CheckConstraint(
            "(status = 'completed' AND actual_tokens IS NOT NULL) "
            "OR (status != 'completed' AND actual_tokens IS NULL)"
        ),
        sa.CheckConstraint("status IN ('reserved', 'dispatched', 'unknown', 'completed', 'released')"))
    for table in ("goals", "sessions", "attempts", "skill_evidence", "evaluation_batches"):
        op.create_index(f"ix_{table}_student_id", table, ["student_id"])
    op.create_index("ix_session_items_session_id", "session_items", ["session_id"])
    op.create_index("usage_student_period", "usage_reservations", ["student_id", "period"])


def downgrade():
    for table in ("usage_reservations", "evaluation_batches", "skill_evidence", "evaluations",
                  "attempts", "session_items", "sessions", "questions", "goals", "students"):
        op.drop_table(table)
