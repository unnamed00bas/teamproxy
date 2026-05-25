"""link peers to wg-easy clients and services to peers

Revision ID: c3f2a9b1e7d4
Revises: b2e1c7a4d9f0
Create Date: 2026-05-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "c3f2a9b1e7d4"
down_revision: str | None = "b2e1c7a4d9f0"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    with op.batch_alter_table("peers", schema=None) as batch_op:
        batch_op.add_column(sa.Column("external_ref", sa.String(length=255), nullable=True))
        batch_op.create_index("ix_peers_external_ref", ["external_ref"])
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.add_column(sa.Column("peer_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_services_peer_id", "peers", ["peer_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.drop_constraint("fk_services_peer_id", type_="foreignkey")
        batch_op.drop_column("peer_id")
    with op.batch_alter_table("peers", schema=None) as batch_op:
        batch_op.drop_index("ix_peers_external_ref")
        batch_op.drop_column("external_ref")
