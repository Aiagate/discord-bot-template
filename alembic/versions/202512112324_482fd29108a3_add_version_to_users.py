"""add version to users

Revision ID: 482fd29108a3
Revises: 11ad26d53a2d
Create Date: 2025-12-11 23:24:46.168981

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "482fd29108a3"
down_revision: str | Sequence[str] | None = "11ad26d53a2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add version column with default 0, NOT NULL
    # Use server_default to handle existing rows
    op.add_column(
        "users", sa.Column("version", sa.Integer(), nullable=False, server_default="0")
    )
    # Remove server_default after creation (application manages it)
    op.alter_column("users", "version", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove version column from users table
    op.drop_column("users", "version")
