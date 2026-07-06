"""add wechat login fields

Revision ID: 20260702_0002
Revises: 20260701_0001
Create Date: 2026-07-02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260702_0002"
down_revision = "20260701_0001"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("wechat_openid", sa.VARCHAR(length=128), nullable=True))
        batch_op.add_column(sa.Column("wechat_unionid", sa.VARCHAR(length=128), nullable=True))
        batch_op.create_unique_constraint("uq_users_wechat_openid", ["wechat_openid"])
        batch_op.create_unique_constraint("uq_users_wechat_unionid", ["wechat_unionid"])


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_wechat_unionid", type_="unique")
        batch_op.drop_constraint("uq_users_wechat_openid", type_="unique")
        batch_op.drop_column("wechat_unionid")
        batch_op.drop_column("wechat_openid")
