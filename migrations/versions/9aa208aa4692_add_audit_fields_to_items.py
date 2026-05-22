"""add_audit_fields_to_items

Revision ID: 9aa208aa4692
Revises: b1c2d3e4f5a6
Create Date: 2026-05-22 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "9aa208aa4692"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("usage_frequency", sa.String(length=16), nullable=True)
        )
        batch_op.add_column(sa.Column("last_checked_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.drop_column("last_checked_at")
        batch_op.drop_column("usage_frequency")
