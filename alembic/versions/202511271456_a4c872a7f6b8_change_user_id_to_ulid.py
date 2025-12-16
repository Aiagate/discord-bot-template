"""change_user_id_to_ulid

Revision ID: a4c872a7f6b8
Revises: b90f56e7dd7e
Create Date: 2025-11-27 14:56:21.915235

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4c872a7f6b8"
down_revision: str | Sequence[str] | None = "b90f56e7dd7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - change user id from int to ULID (string)."""
    # Step 1: Drop existing data (BREAKING CHANGE - existing data will be lost)
    # This is acceptable for development, but in production you'd need a data migration
    op.execute("DELETE FROM users")

    # Step 2 & 3 & 4: Use batch mode to recreate the table with the new ID column
    with op.batch_alter_table("users") as batch_op:
        # In batch mode, we don't need to explicitly drop the PK constraint if we are changing the column.
        # However, to be cleaner, we can just drop the old ID and add the new one.
        batch_op.drop_column("id")
        batch_op.add_column(sa.Column("id", sa.String(length=26), nullable=False))
        batch_op.create_primary_key("users_pkey", ["id"])


def downgrade() -> None:
    """Downgrade schema - change user id back from ULID to int."""
    # Step 1: Drop existing data (BREAKING CHANGE)
    op.execute("DELETE FROM users")

    # Step 2 & 3 & 4: Use batch mode to recreate the table with the old ID column
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("id")
        batch_op.add_column(
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True)
        )
        batch_op.create_primary_key("users_pkey", ["id"])
