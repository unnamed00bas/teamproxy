"""add value and ttl to domains

Revision ID: b2e1c7a4d9f0
Revises: 1ad8c0df45a9
Create Date: 2026-05-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "b2e1c7a4d9f0"
down_revision: str | None = "1ad8c0df45a9"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    with op.batch_alter_table("domains", schema=None) as batch_op:
        batch_op.add_column(sa.Column("value", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("ttl", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("domains", schema=None) as batch_op:
        batch_op.drop_column("ttl")
        batch_op.drop_column("value")
