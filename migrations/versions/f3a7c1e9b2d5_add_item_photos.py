"""add item_photos table

Revision ID: f3a7c1e9b2d5
Revises: cbd9a34f66e5
Create Date: 2026-04-19 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f3a7c1e9b2d5"
down_revision = "cbd9a34f66e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "item_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("photo_path", sa.String(length=512), nullable=False),
        sa.Column("photo_type", sa.String(length=32), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("item_photos", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_item_photos_item_id"), ["item_id"], unique=False
        )

    # Migrate existing single photo_path values into item_photos
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, photo_path FROM items WHERE photo_path IS NOT NULL")
    )
    for row in rows:
        conn.execute(
            sa.text(
                "INSERT INTO item_photos (item_id, photo_path, photo_type, display_order, created_at) "
                "VALUES (:item_id, :photo_path, 'appearance', 0, CURRENT_TIMESTAMP)"
            ),
            {"item_id": row[0], "photo_path": row[1]},
        )

    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.drop_column("photo_path")


def downgrade():
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("photo_path", sa.String(length=512), nullable=True)
        )

    # Restore first appearance photo per item
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT item_id, photo_path FROM item_photos "
            "WHERE photo_type = 'appearance' ORDER BY display_order"
        )
    )
    for row in rows:
        conn.execute(
            sa.text(
                "UPDATE items SET photo_path = :path WHERE id = :id AND photo_path IS NULL"
            ),
            {"path": row[1], "id": row[0]},
        )

    with op.batch_alter_table("item_photos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_item_photos_item_id"))

    op.drop_table("item_photos")
