"""Contatore delle visite del sito getcentral.net.

Revision ID: c5e8a2d4f716
Revises: b3d6f1a8c254

Solo aggiunta: una tabella nuova. Ripetibile.
"""

from alembic import op
import sqlalchemy as sa

from alembic_helpers import index_exists, table_exists

revision = "c5e8a2d4f716"
down_revision = "b3d6f1a8c254"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not table_exists("site_visits"):
        op.create_table(
            "site_visits",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("day", sa.Date(), nullable=False),
            sa.Column("path", sa.String(length=200), nullable=False),
            sa.Column("source", sa.String(length=80), nullable=False),
            sa.Column("referrer_host", sa.String(length=120), nullable=True),
            sa.Column("campaign", sa.String(length=80), nullable=True),
            sa.Column("device", sa.String(length=10), nullable=False),
            sa.Column("visitor", sa.String(length=16), nullable=False),
            sa.Column("entry", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not index_exists("site_visits", "ix_site_visits_day"):
        op.create_index("ix_site_visits_day", "site_visits", ["day"])


def downgrade() -> None:
    # Volutamente vuoto: dalla 1.5.0 nessuna migrazione cancella dati.
    pass
