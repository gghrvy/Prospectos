"""add Gmail message IDs

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa
revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("outreach", sa.Column("gmail_message_id", sa.String(255), nullable=True))
def downgrade() -> None:
    op.drop_column("outreach", "gmail_message_id")
