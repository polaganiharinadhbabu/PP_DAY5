from alembic import op
import sqlalchemy as sa

revision = "0001_create_notes"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column(
            "body",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "title",
            name="uq_notes_title",
        ),
    )

    op.create_index("ix_notes_id", "notes", ["id"])
    op.create_index("ix_notes_title", "notes", ["title"])
    op.create_index("ix_notes_status", "notes", ["status"])


def downgrade():
    op.drop_index("ix_notes_status", table_name="notes")
    op.drop_index("ix_notes_title", table_name="notes")
    op.drop_index("ix_notes_id", table_name="notes")
    op.drop_table("notes")
