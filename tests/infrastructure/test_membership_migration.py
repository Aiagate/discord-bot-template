"""Tests for the forward-safe membership uniqueness migration."""

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.anyio
async def test_migration_rejects_duplicates_without_deleting_rows() -> None:
    """Duplicate current rows stop the migration and remain untouched."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    metadata = sa.MetaData()
    memberships = sa.Table(
        "team_memberships",
        metadata,
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("team_id", sa.String(26), nullable=False),
        sa.Column("user_id", sa.String(26), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
    )

    migration_path = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "202609060900_7d5f0d6a2b31_add_current_membership_unique_index.py"
    )
    spec = importlib.util.spec_from_file_location(
        "membership_migration", migration_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load membership migration.")
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)
        await connection.execute(
            memberships.insert(),
            [
                {
                    "id": "period-1",
                    "team_id": "team-1",
                    "user_id": "user-1",
                    "status": "ACTIVE",
                },
                {
                    "id": "period-2",
                    "team_id": "team-1",
                    "user_id": "user-1",
                    "status": "PENDING",
                },
            ],
        )

        def run_upgrade(sync_connection: sa.Connection) -> None:
            context = MigrationContext.configure(sync_connection)
            with Operations.context(context):
                migration.upgrade()

        with pytest.raises(RuntimeError, match="no rows were deleted"):
            await connection.run_sync(run_upgrade)

        rows = (
            (
                await connection.execute(
                    sa.select(memberships.c.id).order_by(memberships.c.id)
                )
            )
            .scalars()
            .all()
        )

    await engine.dispose()
    assert rows == ["period-1", "period-2"]
