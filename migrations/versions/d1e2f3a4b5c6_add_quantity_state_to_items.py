"""add quantity_state to items

Revision ID: d1e2f3a4b5c6
Revises: c9d0e1f2a3b4
Create Date: 2026-04-30 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "d1e2f3a4b5c6"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("quantity_state", sa.String(length=16), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.drop_column("quantity_state")
