"""add outreach batches

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa
revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table("outreach_batches", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.add_column("outreach", sa.Column("batch_id", sa.String(36), sa.ForeignKey("outreach_batches.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_outreach_batch_id", "outreach", ["batch_id"])
def downgrade() -> None:
    op.drop_column("outreach", "batch_id")
    op.drop_table("outreach_batches")
