"""add recipe_engagements table

Revision ID: a1b2c3d4e5f6
Revises: f3a7c1e9b2d5
Create Date: 2026-04-20 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f3a7c1e9b2d5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recipe_engagements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.String(length=64), nullable=False),
        sa.Column("feedback", sa.String(length=32), nullable=True),
        sa.Column("skip_reason", sa.String(length=64), nullable=True),
        sa.Column("engaged_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "recipe_id", name="uq_recipe_engagement"),
    )
    op.create_index(
        op.f("ix_recipe_engagements_user_id"),
        "recipe_engagements",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recipe_engagements_recipe_id"),
        "recipe_engagements",
        ["recipe_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_recipe_engagements_recipe_id"), table_name="recipe_engagements"
    )
    op.drop_index(
        op.f("ix_recipe_engagements_user_id"), table_name="recipe_engagements"
    )
    op.drop_table("recipe_engagements")
