"""add location to items

Revision ID: b7c8d9e0f1a2
Revises: d5e6f7a8b9c0
Create Date: 2026-04-29 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b7c8d9e0f1a2"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.add_column(sa.Column("location", sa.String(length=32), nullable=True))


def downgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.drop_column("location")
