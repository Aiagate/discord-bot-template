"""add clean chat messages table

Revision ID: 3b8c4d2e1f90
Revises: 2473e1c2c7de
Create Date: 2026-09-05 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3b8c4d2e1f90"
down_revision: str | Sequence[str] | None = "2473e1c2c7de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the append-only ChatMessage table."""
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("conversation_scope", sa.JSON(), nullable=False),
        sa.Column("external_sender_id", sa.String(length=255), nullable=False),
        sa.Column("author_kind", sa.String(length=32), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("chat_messages", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_chat_messages_platform"),
            ["platform"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_chat_messages_external_sender_id"),
            ["external_sender_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_chat_messages_author_kind"),
            ["author_kind"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_chat_messages_occurred_at"),
            ["occurred_at"],
            unique=False,
        )


def downgrade() -> None:
    """Drop the ChatMessage table."""
    with op.batch_alter_table("chat_messages", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_chat_messages_occurred_at"))
        batch_op.drop_index(batch_op.f("ix_chat_messages_author_kind"))
        batch_op.drop_index(batch_op.f("ix_chat_messages_external_sender_id"))
        batch_op.drop_index(batch_op.f("ix_chat_messages_platform"))
    op.drop_table("chat_messages")
