"""add_notification_prefs_to_users

Revision ID: 050a342b2403
Revises: a1b2c3d4e5f6
Create Date: 2026-04-20 09:25:41.593578

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "050a342b2403"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect as sa_inspect

    bind = op.get_bind()
    existing = {c["name"] for c in sa_inspect(bind).get_columns("users")}
    if "cooking_days" not in existing:
        op.add_column("users", sa.Column("cooking_days", sa.Text(), nullable=True))
    if "push_subscription" not in existing:
        op.add_column("users", sa.Column("push_subscription", sa.Text(), nullable=True))
    if "notifications_enabled" not in existing:
        op.add_column(
            "users",
            sa.Column(
                "notifications_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("notifications_enabled")
        batch_op.drop_column("push_subscription")
        batch_op.drop_column("cooking_days")
