"""add outreach activity ledger

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa

revision = "b1c2d3e4f5a6"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("outreach_activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("outreach_id", sa.String(36), sa.ForeignKey("outreach.id", ondelete="SET NULL"), nullable=True),
        sa.Column("business_id", sa.String(36), sa.ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_outreach_activities_created_at", "outreach_activities", ["created_at"])
    op.create_index("ix_outreach_activities_outreach_id", "outreach_activities", ["outreach_id"])
    op.create_index("ix_outreach_activities_business_id", "outreach_activities", ["business_id"])

def downgrade() -> None:
    op.drop_table("outreach_activities")
