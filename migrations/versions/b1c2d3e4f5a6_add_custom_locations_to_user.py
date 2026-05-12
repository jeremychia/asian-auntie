"""add_custom_locations_to_user

Revision ID: b1c2d3e4f5a6
Revises: e2f3a4b5c6d7
Create Date: 2026-05-12 20:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "b1c2d3e4f5a6"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect as sa_inspect

    bind = op.get_bind()
    existing = {c["name"] for c in sa_inspect(bind).get_columns("users")}
    if "custom_locations" not in existing:
        op.add_column("users", sa.Column("custom_locations", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("custom_locations")
