"""target, scan, metadata and provider-result tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "targets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("canonical_url", sa.String(2048), nullable=False),
        sa.Column("canonical_hash", sa.String(64), nullable=False),
        sa.Column("hostname", sa.String(253), nullable=False),
        sa.Column("scheme", sa.String(8), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_targets_canonical_hash", "targets", ["canonical_hash"], unique=True)
    op.create_index("ix_targets_hostname", "targets", ["hostname"])
    op.create_table(
        "scans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("target_id", sa.Uuid(), sa.ForeignKey("targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("submitted_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.String(500)),
    )
    op.create_index("ix_scans_status", "scans", ["status"])
    op.create_index(
        "uq_scans_active_target", "scans", ["target_id"], unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )
    op.create_table(
        "scan_metadata",
        sa.Column("scan_id", sa.Uuid(), sa.ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "provider_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scan_id", sa.Uuid(), sa.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("verdict", sa.String(16), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.String(500)),
        sa.UniqueConstraint("scan_id", "provider", name="uq_scan_provider"),
    )
    op.create_index("ix_provider_results_scan_id", "provider_results", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_provider_results_scan_id", table_name="provider_results")
    op.drop_table("provider_results")
    op.drop_table("scan_metadata")
    op.drop_index("uq_scans_active_target", table_name="scans")
    op.drop_index("ix_scans_status", table_name="scans")
    op.drop_table("scans")
    op.drop_index("ix_targets_hostname", table_name="targets")
    op.drop_index("ix_targets_canonical_hash", table_name="targets")
    op.drop_table("targets")
