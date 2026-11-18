"""Qualified paper setups and exact owner-reviewed proposals."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "setup_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("fingerprint", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "snapshot_id",
            sa.String(36),
            sa.ForeignKey("market_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(24), nullable=False),
        sa.Column("market_type", sa.String(12), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("strategy_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint(
            "market_type IN ('spot','futures')", name=op.f("ck_setup_candidates_market_type")
        ),
        sa.CheckConstraint("side IN ('long','short')", name=op.f("ck_setup_candidates_side")),
        sa.CheckConstraint(
            "score >= 70 AND score <= 100", name=op.f("ck_setup_candidates_score_eligible")
        ),
        sa.CheckConstraint(
            "status IN ('awaiting_ai_authorization','proposed','approved','rejected','expired','vetoed')",
            name=op.f("ck_setup_candidates_status"),
        ),
    )
    op.create_index(
        "ix_setup_candidates_status_created", "setup_candidates", ["status", "created_at"]
    )
    op.create_index(
        "ix_setup_candidates_symbol_market",
        "setup_candidates",
        ["symbol", "market_type", "created_at"],
    )
    op.create_table(
        "trade_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.String(36),
            sa.ForeignKey("setup_candidates.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "committee_run_id",
            sa.String(36),
            sa.ForeignKey("committee_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "snapshot_id",
            sa.String(36),
            sa.ForeignKey("market_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "permit_id",
            sa.String(64),
            sa.ForeignKey("trading_permits.id", ondelete="RESTRICT"),
            unique=True,
        ),
        sa.Column("instrument", sa.String(24), nullable=False),
        sa.Column("market_type", sa.String(12), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("entry_price", sa.Numeric(30, 12), nullable=False),
        sa.Column("stop_price", sa.Numeric(30, 12), nullable=False),
        sa.Column("target_price", sa.Numeric(30, 12), nullable=False),
        sa.Column("notional_usdt", sa.Numeric(30, 12), nullable=False),
        sa.Column("leverage", sa.Numeric(8, 4), nullable=False),
        sa.Column("planned_loss_usdt", sa.Numeric(30, 12), nullable=False),
        sa.Column("estimated_cost_usdt", sa.Numeric(30, 12), nullable=False),
        sa.Column("reward_risk", sa.Numeric(12, 6), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("decided_by", sa.Text()),
        sa.Column("decision_reason", sa.Text()),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint(
            "market_type IN ('spot','futures')", name=op.f("ck_trade_proposals_market_type")
        ),
        sa.CheckConstraint("side IN ('long','short')", name=op.f("ck_trade_proposals_side")),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected','expired','vetoed')",
            name=op.f("ck_trade_proposals_status"),
        ),
        sa.CheckConstraint("entry_price > 0", name=op.f("ck_trade_proposals_entry_positive")),
        sa.CheckConstraint("stop_price > 0", name=op.f("ck_trade_proposals_stop_positive")),
        sa.CheckConstraint("target_price > 0", name=op.f("ck_trade_proposals_target_positive")),
        sa.CheckConstraint(
            "notional_usdt > 0 AND notional_usdt <= 200",
            name=op.f("ck_trade_proposals_notional_range"),
        ),
        sa.CheckConstraint(
            "leverage >= 1 AND leverage <= 2", name=op.f("ck_trade_proposals_leverage_range")
        ),
        sa.CheckConstraint(
            "planned_loss_usdt >= 0 AND estimated_cost_usdt >= 0",
            name=op.f("ck_trade_proposals_cost_nonnegative"),
        ),
        sa.CheckConstraint(
            "reward_risk >= 0", name=op.f("ck_trade_proposals_reward_risk_nonnegative")
        ),
    )
    op.create_index(
        "uq_trade_proposals_candidate", "trade_proposals", ["candidate_id"], unique=True
    )
    op.create_index(
        "uq_trade_proposals_committee_run", "trade_proposals", ["committee_run_id"], unique=True
    )
    op.create_index("ix_trade_proposals_status_expiry", "trade_proposals", ["status", "expires_at"])


def downgrade() -> None:
    op.drop_index("ix_trade_proposals_status_expiry", table_name="trade_proposals")
    op.drop_index("uq_trade_proposals_committee_run", table_name="trade_proposals")
    op.drop_index("uq_trade_proposals_candidate", table_name="trade_proposals")
    op.drop_table("trade_proposals")
    op.drop_index("ix_setup_candidates_symbol_market", table_name="setup_candidates")
    op.drop_index("ix_setup_candidates_status_created", table_name="setup_candidates")
    op.drop_table("setup_candidates")
