"""add outreach reply state

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa
revision = "b7c8d9e0f1a2"
down_revision = "a6b7c8d9e0f1"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("outreach", sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True))
def downgrade() -> None:
    op.drop_column("outreach", "replied_at")
