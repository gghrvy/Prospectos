"""add outreach approval state

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa
revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("outreach", sa.Column("approval_status", sa.String(20), nullable=False, server_default="DRAFT"))
    op.alter_column("outreach", "approval_status", server_default=None)
def downgrade() -> None:
    op.drop_column("outreach", "approval_status")
