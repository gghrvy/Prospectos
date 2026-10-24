"""add context-aware opportunity assessments to audits

Revision ID: f1c2d3e4a5b6
Revises: 08059bdbcd49
Create Date: 2026-08-22
"""
from alembic import op
import sqlalchemy as sa

revision = "f1c2d3e4a5b6"
down_revision = "08059bdbcd49"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("website_audits", sa.Column("opportunity_assessments", sa.JSON(), nullable=True))
    op.add_column("website_audits", sa.Column("website_context", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("website_audits", "website_context")
    op.drop_column("website_audits", "opportunity_assessments")
