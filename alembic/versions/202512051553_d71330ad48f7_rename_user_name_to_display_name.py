"""rename user name to display name

Revision ID: d71330ad48f7
Revises: 5d421434096f
Create Date: 2025-12-05 15:53:53.188468

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d71330ad48f7"
down_revision: str | Sequence[str] | None = "5d421434096f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename name column to display_name (SQLite compatible)."""
    # Step 1: インデックスを削除
    op.drop_index(op.f("ix_users_name"), table_name="users")

    # Step 2: 新しいカラムを追加
    op.add_column(
        "users", sa.Column("display_name", sa.String(length=255), nullable=True)
    )

    # Step 3: データをコピー
    op.execute("UPDATE users SET display_name = name")

    # Step 4: 古いカラムを削除
    op.drop_column("users", "name")

    # Step 5: 新しいインデックスを作成
    op.create_index(
        op.f("ix_users_display_name"), "users", ["display_name"], unique=False
    )


def downgrade() -> None:
    """Revert display_name column back to name (SQLite compatible)."""
    # Step 1: インデックスを削除
    op.drop_index(op.f("ix_users_display_name"), table_name="users")

    # Step 2: 古いカラムを追加
    op.add_column("users", sa.Column("name", sa.String(length=255), nullable=True))

    # Step 3: データをコピー
    op.execute("UPDATE users SET name = display_name")

    # Step 4: 新しいカラムを削除
    op.drop_column("users", "display_name")

    # Step 5: 古いインデックスを作成
    op.create_index(op.f("ix_users_name"), "users", ["name"], unique=False)
