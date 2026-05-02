"""add product detail fields to items

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-02

"""

from alembic import op
import sqlalchemy as sa

revision = "e2f3a4b5c6d7"
down_revision = "024a64ce1ef0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.add_column(sa.Column("brands", sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column("quantity", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("ingredients_text", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("labels_tags", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("product_data_source", sa.String(length=16), nullable=True)
        )
        batch_op.add_column(
            sa.Column("off_nutriscore_grade", sa.String(length=1), nullable=True)
        )
        batch_op.add_column(
            sa.Column("off_nutriscore_score", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("off_nova_group", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("off_ecoscore_grade", sa.String(length=1), nullable=True)
        )
        batch_op.add_column(
            sa.Column("off_ecoscore_score", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("off_categories_tags", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("off_allergens_tags", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("off_packaging_tags", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("off_data_quality_tags", sa.Text(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.drop_column("off_data_quality_tags")
        batch_op.drop_column("off_packaging_tags")
        batch_op.drop_column("off_allergens_tags")
        batch_op.drop_column("off_categories_tags")
        batch_op.drop_column("off_ecoscore_score")
        batch_op.drop_column("off_ecoscore_grade")
        batch_op.drop_column("off_nova_group")
        batch_op.drop_column("off_nutriscore_score")
        batch_op.drop_column("off_nutriscore_grade")
        batch_op.drop_column("product_data_source")
        batch_op.drop_column("labels_tags")
        batch_op.drop_column("ingredients_text")
        batch_op.drop_column("quantity")
        batch_op.drop_column("brands")
