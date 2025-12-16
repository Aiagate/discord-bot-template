"""rename user name to display name

Revision ID: d71330ad48f7
Revises: 5d421434096f
Create Date: 2025-12-05 15:53:53.188468

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d71330ad48f7"
down_revision: str | Sequence[str] | None = "5d421434096f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename name column to display_name (SQLite compatible)."""
    # Use batch_alter_table to handle SQLite constraints and column renaming
    # Phase 1: Rename column (and drop old index)
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index(op.f("ix_users_name"))
        batch_op.alter_column("name", new_column_name="display_name")

    # Phase 2: Create new index on the new column
    # separate batch op ensures the column exists in the reflected schema
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_index(
            op.f("ix_users_display_name"), ["display_name"], unique=False
        )


def downgrade() -> None:
    """Revert display_name column back to name (SQLite compatible)."""
    with op.batch_alter_table("users") as batch_op:
        # Step 1: Drop new index
        batch_op.drop_index(op.f("ix_users_display_name"))

        # Step 2: Rename column back
        batch_op.alter_column("display_name", new_column_name="name")

    with op.batch_alter_table("users") as batch_op:
        # Step 3: Create old index
        batch_op.create_index(op.f("ix_users_name"), ["name"], unique=False)
