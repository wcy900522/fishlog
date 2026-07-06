"""add user admin flag

Revision ID: 20260703_0003
Revises: 20260702_0002
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_0003"
down_revision = "20260702_0002"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.execute("UPDATE users SET is_admin = TRUE WHERE phone = '18610137321'")

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("is_admin", server_default=None)


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_admin")
