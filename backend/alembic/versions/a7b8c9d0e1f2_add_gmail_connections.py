"""add Gmail connections and sent outreach tracking

Revision ID: a7b8c9d0e1f2
Revises: f1c2d3e4a5b6
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa

revision = "a7b8c9d0e1f2"
down_revision = "f1c2d3e4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gmail_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column("outreach", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outreach", sa.Column("sent_to", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("outreach", "sent_to")
    op.drop_column("outreach", "sent_at")
    op.drop_table("gmail_connections")
