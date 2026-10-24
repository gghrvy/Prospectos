"""add batch timezone and follow-up tracking

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa

revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outreach_batches", sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"))
    op.alter_column("outreach_batches", "timezone", server_default=None)
    op.add_column("outreach", sa.Column("gmail_thread_id", sa.String(255), nullable=True))
    op.add_column("outreach", sa.Column("followup_of_id", sa.String(36), sa.ForeignKey("outreach.id", ondelete="SET NULL"), nullable=True))
    op.add_column("outreach", sa.Column("followup_due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outreach", sa.Column("followup_paused", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("outreach", "followup_paused", server_default=None)
    op.create_index("ix_outreach_followup_due_at", "outreach", ["followup_due_at"])


def downgrade() -> None:
    op.drop_index("ix_outreach_followup_due_at", table_name="outreach")
    op.drop_column("outreach", "followup_paused")
    op.drop_column("outreach", "followup_due_at")
    op.drop_column("outreach", "followup_of_id")
    op.drop_column("outreach", "gmail_thread_id")
    op.drop_column("outreach_batches", "timezone")
