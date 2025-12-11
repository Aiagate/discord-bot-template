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

    # Step 2: Drop the old primary key constraint and id column
    op.drop_constraint("users_pkey", "users", type_="primary")
    op.drop_column("users", "id")

    # Step 3: Create new id column as VARCHAR(26) for ULID
    op.add_column(
        "users",
        sa.Column("id", sa.String(length=26), nullable=False),
    )

    # Step 4: Re-create primary key constraint
    op.create_primary_key("users_pkey", "users", ["id"])


def downgrade() -> None:
    """Downgrade schema - change user id back from ULID to int."""
    # Step 1: Drop existing data (BREAKING CHANGE)
    op.execute("DELETE FROM users")

    # Step 2: Drop the primary key constraint and id column
    op.drop_constraint("users_pkey", "users", type_="primary")
    op.drop_column("users", "id")

    # Step 3: Create id column as Integer with autoincrement
    op.add_column(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
    )

    # Step 4: Re-create primary key constraint
    op.create_primary_key("users_pkey", "users", ["id"])
