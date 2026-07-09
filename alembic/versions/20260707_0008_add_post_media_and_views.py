"""add post media and views

Revision ID: 20260707_0008
Revises: 20260707_0007
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260707_0008"
down_revision = "20260707_0007"
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
    _add_column_if_missing("posts", sa.Column("image_urls", sa.JSON(), nullable=True))
    _add_column_if_missing("posts", sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("posts", "view_count", server_default=None)


def downgrade():
    _drop_column_if_exists("posts", "view_count")
    _drop_column_if_exists("posts", "image_urls")
