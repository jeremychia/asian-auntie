"""add_onboarding_fields

Revision ID: c3d4e5f6a7b8
Revises: 050a342b2403
Create Date: 2026-04-24 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "050a342b2403"
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect as sa_inspect

    bind = op.get_bind()
    existing = {c["name"] for c in sa_inspect(bind).get_columns("users")}
    if "location" not in existing:
        op.add_column("users", sa.Column("location", sa.String(16), nullable=True))
    if "cuisine_prefs" not in existing:
        op.add_column("users", sa.Column("cuisine_prefs", sa.Text(), nullable=True))
    if "household_size" not in existing:
        op.add_column(
            "users", sa.Column("household_size", sa.String(16), nullable=True)
        )
    if "gdpr_consent" not in existing:
        op.add_column("users", sa.Column("gdpr_consent", sa.Boolean(), nullable=True))
    if "consent_date" not in existing:
        op.add_column("users", sa.Column("consent_date", sa.DateTime(), nullable=True))
    if "onboarding_done" not in existing:
        op.add_column(
            "users",
            sa.Column(
                "onboarding_done",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("onboarding_done")
        batch_op.drop_column("consent_date")
        batch_op.drop_column("gdpr_consent")
        batch_op.drop_column("household_size")
        batch_op.drop_column("cuisine_prefs")
        batch_op.drop_column("location")
