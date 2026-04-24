"""add_other_cuisine_requests

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-04-24 13:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d5e6f7a8b9c0"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect as sa_inspect

    bind = op.get_bind()
    existing = {c["name"] for c in sa_inspect(bind).get_columns("users")}
    if "other_cuisine_requests" not in existing:
        op.add_column(
            "users", sa.Column("other_cuisine_requests", sa.Text(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("other_cuisine_requests")
