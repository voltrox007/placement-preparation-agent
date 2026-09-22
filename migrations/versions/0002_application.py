"""Add the application, planning, evidence, and cached-agent tables.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "profiles",
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), primary_key=True),
        sa.Column("education", sa.String(), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "activities",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("skill_id", sa.String(), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("resource_url", sa.String(), nullable=False),
        sa.Column("instructions", sa.String(), nullable=False),
        sa.CheckConstraint("duration_minutes > 0"),
    )
    op.create_table(
        "learning_plans",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_learning_plans_student_id", "learning_plans", ["student_id"])
    op.create_table(
        "plan_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("plan_id", sa.String(), sa.ForeignKey("learning_plans.id"), nullable=False),
        sa.Column("activity_id", sa.String(), sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("scheduled_date", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
    )
    op.create_table(
        "progress_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_progress_events_student_id", "progress_events", ["student_id"])
    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("confirmed_facts", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_documents_student_id", "documents", ["student_id"])
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
    )
    op.create_index("ix_projects_student_id", "projects", ["student_id"])
    op.create_table(
        "agent_results",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("request_key", sa.String(), nullable=False),
        sa.Column("input_hash", sa.String(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint("student_id", "request_key"),
    )
    op.create_index("ix_agent_results_student_id", "agent_results", ["student_id"])


def downgrade():
    for table in (
        "agent_results",
        "projects",
        "documents",
        "progress_events",
        "plan_items",
        "learning_plans",
        "activities",
        "skills",
        "profiles",
    ):
        op.drop_table(table)
