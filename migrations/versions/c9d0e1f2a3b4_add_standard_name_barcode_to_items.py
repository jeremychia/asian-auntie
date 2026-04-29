"""add standard_name and barcode to items

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-04-29 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c9d0e1f2a3b4"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("standard_name", sa.String(length=256), nullable=True)
        )
        batch_op.add_column(sa.Column("barcode", sa.String(length=64), nullable=True))


def downgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.drop_column("barcode")
        batch_op.drop_column("standard_name")
