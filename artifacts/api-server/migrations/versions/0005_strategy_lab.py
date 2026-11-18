"""Persist reproducible historical Strategy Laboratory runs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strategy_backtest_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.Text(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(12), nullable=False),
        sa.Column("requested_days", sa.Integer(), nullable=False),
        sa.Column("strategy_version", sa.String(32), nullable=False),
        sa.Column("data_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("source_snapshot", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint(
            "symbol IN ('BTCUSDT','ETHUSDT','SOLUSDT')",
            name=op.f("ck_strategy_backtest_runs_symbol"),
        ),
        sa.CheckConstraint(
            "requested_days >= 7 AND requested_days <= 30",
            name=op.f("ck_strategy_backtest_runs_requested_days"),
        ),
    )
    op.create_index(
        "ix_strategy_backtest_runs_owner_created",
        "strategy_backtest_runs",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_strategy_backtest_runs_owner_created", table_name="strategy_backtest_runs")
    op.drop_table("strategy_backtest_runs")
