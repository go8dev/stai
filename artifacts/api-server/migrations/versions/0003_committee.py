"""Phase 3 durable research, without any trading permissions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "10af905d740f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "committee_agents",
        sa.Column("id", sa.String(24), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
    )
    op.create_table(
        "committee_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("purpose", sa.String(40), unique=True, nullable=False),
        sa.Column("symbol", sa.String(24), nullable=False),
        sa.Column("market_type", sa.String(12), nullable=False),
        sa.Column(
            "snapshot_id",
            sa.String(36),
            sa.ForeignKey("market_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(18, 10)),
        sa.Column("cost_basis", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("recommendation", postgresql.JSONB()),
        sa.Column("memory", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.Text()),
        sa.CheckConstraint(
            "status IN ('running','completed','failed','interrupted')",
            name=op.f("ck_committee_runs_status"),
        ),
        sa.CheckConstraint(
            "market_type IN ('spot','futures')", name=op.f("ck_committee_runs_market_type")
        ),
    )
    op.create_index("ix_committee_runs_started", "committee_runs", ["started_at"])
    op.create_table(
        "committee_findings",
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("committee_runs.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            sa.String(24),
            sa.ForeignKey("committee_agents.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("finding", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "committee_calls",
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("committee_runs.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("stage", sa.String(32), primary_key=True),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("cost_usd", sa.Numeric(18, 10)),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("committee_calls")
    op.drop_table("committee_findings")
    op.drop_index("ix_committee_runs_started", table_name="committee_runs")
    op.drop_table("committee_runs")
    op.drop_table("committee_agents")
