"""add batch send windows

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa
revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("outreach_batches", sa.Column("send_hour_start", sa.Integer(), nullable=False, server_default="9"))
    op.add_column("outreach_batches", sa.Column("send_hour_end", sa.Integer(), nullable=False, server_default="17"))
    op.alter_column("outreach_batches", "send_hour_start", server_default=None)
    op.alter_column("outreach_batches", "send_hour_end", server_default=None)
def downgrade() -> None:
    op.drop_column("outreach_batches", "send_hour_end")
    op.drop_column("outreach_batches", "send_hour_start")
