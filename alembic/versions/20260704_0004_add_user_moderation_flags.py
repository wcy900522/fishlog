"""add user moderation flags

Revision ID: 20260704_0004
Revises: 20260703_0003
Create Date: 2026-07-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260704_0004"
down_revision = "20260703_0003"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}

    with op.batch_alter_table("users") as batch_op:
        if "is_disabled" not in columns:
            batch_op.add_column(sa.Column("is_disabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        if "can_post" not in columns:
            batch_op.add_column(sa.Column("can_post", sa.Boolean(), nullable=False, server_default=sa.true()))

    with op.batch_alter_table("users") as batch_op:
        if "is_disabled" not in columns:
            batch_op.alter_column("is_disabled", server_default=None)
        if "can_post" not in columns:
            batch_op.alter_column("can_post", server_default=None)


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}

    with op.batch_alter_table("users") as batch_op:
        if "can_post" in columns:
            batch_op.drop_column("can_post")
        if "is_disabled" in columns:
            batch_op.drop_column("is_disabled")
