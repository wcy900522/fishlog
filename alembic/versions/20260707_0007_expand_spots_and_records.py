"""expand spots and records

Revision ID: 20260707_0007
Revises: 20260707_0006
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260707_0007"
down_revision = "20260707_0006"
branch_labels = None
depends_on = None


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name not in columns:
        op.add_column(table_name, column)


def _drop_column_if_exists(table_name: str, column_name: str) -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {item["name"] for item in inspector.get_columns(table_name)}
    if column_name in columns:
        op.drop_column(table_name, column_name)


def upgrade():
    _add_column_if_missing("fishing_spots", sa.Column("target_species", sa.VARCHAR(length=255), nullable=True))
    _add_column_if_missing("fishing_spots", sa.Column("best_season", sa.VARCHAR(length=100), nullable=True))
    _add_column_if_missing("fishing_spots", sa.Column("image_url", sa.VARCHAR(length=255), nullable=True))
    _add_column_if_missing("fishing_spots", sa.Column("tags", sa.VARCHAR(length=255), nullable=True))

    _add_column_if_missing("catch_logs", sa.Column("weight", sa.DECIMAL(8, 2), nullable=True))
    _add_column_if_missing("catch_logs", sa.Column("tide", sa.VARCHAR(length=100), nullable=True))
    _add_column_if_missing("catch_logs", sa.Column("equipment", sa.VARCHAR(length=255), nullable=True))
    _add_column_if_missing("catch_logs", sa.Column("rod", sa.VARCHAR(length=100), nullable=True))
    _add_column_if_missing("catch_logs", sa.Column("line_group", sa.VARCHAR(length=100), nullable=True))
    _add_column_if_missing("catch_logs", sa.Column("photo_urls", sa.JSON(), nullable=True))


def downgrade():
    _drop_column_if_exists("catch_logs", "photo_urls")
    _drop_column_if_exists("catch_logs", "line_group")
    _drop_column_if_exists("catch_logs", "rod")
    _drop_column_if_exists("catch_logs", "equipment")
    _drop_column_if_exists("catch_logs", "tide")
    _drop_column_if_exists("catch_logs", "weight")

    _drop_column_if_exists("fishing_spots", "tags")
    _drop_column_if_exists("fishing_spots", "image_url")
    _drop_column_if_exists("fishing_spots", "best_season")
    _drop_column_if_exists("fishing_spots", "target_species")
