"""Persist bounded, owner-requested historical AI reviews."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strategy_backtest_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "backtest_id",
            sa.String(36),
            sa.ForeignKey("strategy_backtest_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Text(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("data_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("reserved_usd", sa.Numeric(18, 10), nullable=False),
        sa.Column("cost_usd", sa.Numeric(18, 10)),
        sa.Column("answer", postgresql.JSONB()),
        sa.Column("error", sa.Text()),
        sa.CheckConstraint(
            "status IN ('running','completed','unknown')",
            name=op.f("ck_strategy_backtest_reviews_status"),
        ),
        sa.CheckConstraint(
            "reserved_usd >= 0",
            name=op.f("ck_strategy_backtest_reviews_reserved_nonnegative"),
        ),
    )
    op.create_index(
        "ix_strategy_backtest_reviews_owner_created",
        "strategy_backtest_reviews",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_strategy_backtest_reviews_run_created",
        "strategy_backtest_reviews",
        ["backtest_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_strategy_backtest_reviews_run_created", table_name="strategy_backtest_reviews"
    )
    op.drop_index(
        "ix_strategy_backtest_reviews_owner_created", table_name="strategy_backtest_reviews"
    )
    op.drop_table("strategy_backtest_reviews")
