"""Tests for the forward-safe membership uniqueness migration."""

import importlib.util
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.ext.asyncio import create_async_engine

_MIGRATION_PATH = (
    Path(__file__).parents[2]
    / "alembic"
    / "versions"
    / "202609060900_7d5f0d6a2b31_add_current_membership_unique_index.py"
)


def _load_migration() -> Any:
    spec = importlib.util.spec_from_file_location(
        "membership_migration", _MIGRATION_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load membership migration.")
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def _membership_table(metadata: sa.MetaData) -> sa.Table:
    return sa.Table(
        "team_memberships",
        metadata,
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("team_id", sa.String(26), nullable=False),
        sa.Column("user_id", sa.String(26), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
    )


@pytest.mark.anyio
async def test_migration_rejects_duplicates_without_deleting_rows() -> None:
    """Duplicate current rows stop the migration and remain untouched."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    metadata = sa.MetaData()
    memberships = _membership_table(metadata)
    migration = _load_migration()

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


@pytest.mark.anyio
async def test_migration_upgrade_and_downgrade_preserve_clean_data() -> None:
    """A clean database can upgrade and downgrade without changing rows."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    metadata = sa.MetaData()
    memberships = _membership_table(metadata)
    migration = _load_migration()

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
                    "status": "LEAVED",
                },
            ],
        )

        def run_upgrade(sync_connection: sa.Connection) -> None:
            context = MigrationContext.configure(sync_connection)
            with Operations.context(context):
                migration.upgrade()

        def index_names(sync_connection: sa.Connection) -> set[str]:
            names: set[str] = set()
            for index in sa.inspect(sync_connection).get_indexes("team_memberships"):
                name = index["name"]
                if name is not None:
                    names.add(name)
            return names

        await connection.run_sync(run_upgrade)
        assert "uq_team_memberships_current_period" in await connection.run_sync(
            index_names
        )

        def run_downgrade(sync_connection: sa.Connection) -> None:
            context = MigrationContext.configure(sync_connection)
            with Operations.context(context):
                migration.downgrade()

        await connection.run_sync(run_downgrade)
        assert "uq_team_memberships_current_period" not in await connection.run_sync(
            index_names
        )

        rows = (
            (
                await connection.execute(
                    sa.select(memberships.c.id, memberships.c.status).order_by(
                        memberships.c.id
                    )
                )
            )
            .tuples()
            .all()
        )

    await engine.dispose()
    assert rows == [("period-1", "ACTIVE"), ("period-2", "LEAVED")]


def test_migration_offline_sql_generation_emits_index_ddl() -> None:
    """Offline SQL generation skips the data preflight and emits only DDL."""
    output = StringIO()
    context = MigrationContext.configure(
        url="sqlite://",
        opts={"as_sql": True, "output_buffer": output},
    )
    migration = _load_migration()

    with Operations.context(context):
        migration.upgrade()

    generated_sql = output.getvalue()
    assert "CREATE UNIQUE INDEX uq_team_memberships_current_period" in generated_sql
    assert "WHERE status IN ('PENDING', 'ACTIVE')" in generated_sql
