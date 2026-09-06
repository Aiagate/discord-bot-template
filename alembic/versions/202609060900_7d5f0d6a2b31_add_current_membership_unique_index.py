"""Enforce one current membership period per team and user.

Revision ID: 7d5f0d6a2b31
Revises: 3b8c4d2e1f90
Create Date: 2026-09-06 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7d5f0d6a2b31"
down_revision: str | Sequence[str] | None = "3b8c4d2e1f90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INDEX_NAME = "uq_team_memberships_current_period"
_CURRENT_STATUSES = "'PENDING', 'ACTIVE'"


def upgrade() -> None:
    """Add the partial index after an online duplicate-row preflight.

    Offline ``alembic upgrade --sql`` has no data connection, so it emits only
    the index DDL. Applying that SQL still relies on the database to reject
    duplicate rows; this migration never deletes or selects rows offline.
    """
    if not op.get_context().as_sql:
        connection = op.get_bind()
        duplicate_rows = connection.execute(
            sa.text(
                "SELECT team_id, user_id, COUNT(*) AS row_count "
                "FROM team_memberships "
                f"WHERE status IN ({_CURRENT_STATUSES}) "
                "GROUP BY team_id, user_id "
                "HAVING COUNT(*) > 1"
            )
        ).fetchall()
        if duplicate_rows:
            duplicates = "; ".join(
                f"team_id={row[0]}, user_id={row[1]}, rows={row[2]}"
                for row in duplicate_rows
            )
            raise RuntimeError(
                "Cannot enforce one current membership period because duplicate "
                f"rows exist: {duplicates}. Resolve them explicitly and rerun "
                "the migration; no rows were deleted."
            )

    op.create_index(
        _INDEX_NAME,
        "team_memberships",
        ["team_id", "user_id"],
        unique=True,
        sqlite_where=sa.text(f"status IN ({_CURRENT_STATUSES})"),
        postgresql_where=sa.text(f"status IN ({_CURRENT_STATUSES})"),
    )


def downgrade() -> None:
    """Remove the current membership uniqueness constraint."""
    op.drop_index(_INDEX_NAME, table_name="team_memberships")
