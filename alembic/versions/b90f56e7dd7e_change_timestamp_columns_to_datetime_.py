"""Change timestamp columns to datetime type

Revision ID: b90f56e7dd7e
Revises: 22c0012f5007
Create Date: 2025-11-26 18:16:05.615858

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b90f56e7dd7e"
down_revision: str | Sequence[str] | None = "22c0012f5007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLiteでは型変更が直接できないため、カラムを再作成する

    # 1. 一時カラムを追加
    op.add_column(
        "users",
        sa.Column(
            "created_at_new",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "updated_at_new",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # 2. 古いカラムを削除
    op.drop_column("users", "created_at")
    op.drop_column("users", "updated_at")

    # 3. 新しいカラムの名前を変更
    op.alter_column("users", "created_at_new", new_column_name="created_at")
    op.alter_column("users", "updated_at_new", new_column_name="updated_at")


def downgrade() -> None:
    """Downgrade schema."""
    # 1. 一時カラムを追加（文字列型）
    op.add_column("users", sa.Column("created_at_old", sa.String(), nullable=True))
    op.add_column("users", sa.Column("updated_at_old", sa.String(), nullable=True))

    # 2. 現在のカラムを削除
    op.drop_column("users", "created_at")
    op.drop_column("users", "updated_at")

    # 3. 古いカラムの名前を戻す
    op.alter_column("users", "created_at_old", new_column_name="created_at")
    op.alter_column("users", "updated_at_old", new_column_name="updated_at")
