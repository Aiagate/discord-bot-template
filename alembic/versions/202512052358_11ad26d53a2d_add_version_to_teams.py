"""add version to teams

Revision ID: 11ad26d53a2d
Revises: d71330ad48f7
Create Date: 2025-12-05 23:58:51.253603

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "11ad26d53a2d"
down_revision: str | Sequence[str] | None = "d71330ad48f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add version column with default 0, NOT NULL
    # Use server_default to handle existing rows
    op.add_column(
        "teams", sa.Column("version", sa.Integer(), nullable=False, server_default="0")
    )
    # Remove server_default after creation (application manages it)
    # This requires batch mode in SQLite
    with op.batch_alter_table("teams") as batch_op:
        batch_op.alter_column("version", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove version column from teams table
    op.drop_column("teams", "version")
