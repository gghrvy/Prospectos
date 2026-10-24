"""add Gmail activity external IDs

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa
revision = "a6b7c8d9e0f1"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("outreach_activities", sa.Column("external_id", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_outreach_activities_external_id", "outreach_activities", ["external_id"])
def downgrade() -> None:
    op.drop_constraint("uq_outreach_activities_external_id", "outreach_activities", type_="unique")
    op.drop_column("outreach_activities", "external_id")
