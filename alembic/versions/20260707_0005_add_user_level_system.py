"""add user level system

Revision ID: 20260707_0005
Revises: 20260704_0004
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260707_0005"
down_revision = "20260704_0004"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    post_columns = {column["name"] for column in inspector.get_columns("posts")}

    with op.batch_alter_table("users") as batch_op:
        if "xp" not in user_columns:
            batch_op.add_column(sa.Column("xp", sa.Integer(), nullable=False, server_default="0"))
        if "level" not in user_columns:
            batch_op.add_column(sa.Column("level", sa.Integer(), nullable=False, server_default="1"))
        if "title" not in user_columns:
            batch_op.add_column(sa.Column("title", sa.VARCHAR(length=50), nullable=False, server_default="初学钓手"))

    with op.batch_alter_table("users") as batch_op:
        if "xp" not in user_columns:
            batch_op.alter_column("xp", server_default=None)
        if "level" not in user_columns:
            batch_op.alter_column("level", server_default=None)
        if "title" not in user_columns:
            batch_op.alter_column("title", server_default=None)

    if "xp_logs" not in inspector.get_table_names():
        op.create_table(
            "xp_logs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("xp_delta", sa.Integer(), nullable=False),
            sa.Column("reason", sa.VARCHAR(length=100), nullable=False),
            sa.Column("target_type", sa.VARCHAR(length=50), nullable=True),
            sa.Column("target_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_xp_logs_user_id", "xp_logs", ["user_id"])
        op.create_index("ix_xp_logs_target_type", "xp_logs", ["target_type"])
        op.create_index("ix_xp_logs_target_id", "xp_logs", ["target_id"])

    with op.batch_alter_table("posts") as batch_op:
        if "is_featured" not in post_columns:
            batch_op.add_column(sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()))

    with op.batch_alter_table("posts") as batch_op:
        if "is_featured" not in post_columns:
            batch_op.alter_column("is_featured", server_default=None)

    table_names = set(inspector.get_table_names())
    if "post_likes" not in table_names:
        op.create_table(
            "post_likes",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("post_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["post_id"], ["posts.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),
        )
        op.create_index("ix_post_likes_post_id", "post_likes", ["post_id"])
        op.create_index("ix_post_likes_user_id", "post_likes", ["user_id"])

    if "comment_likes" not in table_names:
        op.create_table(
            "comment_likes",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("comment_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["comment_id"], ["comments.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("comment_id", "user_id", name="uq_comment_likes_comment_user"),
        )
        op.create_index("ix_comment_likes_comment_id", "comment_likes", ["comment_id"])
        op.create_index("ix_comment_likes_user_id", "comment_likes", ["user_id"])

    if "badges" not in table_names:
        op.create_table(
            "badges",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("code", sa.VARCHAR(length=50), nullable=False),
            sa.Column("name", sa.VARCHAR(length=50), nullable=False),
            sa.Column("icon", sa.VARCHAR(length=20), nullable=False),
            sa.Column("description", sa.VARCHAR(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )

    if "user_badges" not in table_names:
        op.create_table(
            "user_badges",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("badge_code", sa.VARCHAR(length=50), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "badge_code", name="uq_user_badges_user_code"),
        )
        op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])
        op.create_index("ix_user_badges_badge_code", "user_badges", ["badge_code"])


def downgrade():
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())
    if "user_badges" in table_names:
        op.drop_index("ix_user_badges_badge_code", table_name="user_badges")
        op.drop_index("ix_user_badges_user_id", table_name="user_badges")
        op.drop_table("user_badges")
    if "badges" in table_names:
        op.drop_table("badges")
    if "comment_likes" in table_names:
        op.drop_index("ix_comment_likes_user_id", table_name="comment_likes")
        op.drop_index("ix_comment_likes_comment_id", table_name="comment_likes")
        op.drop_table("comment_likes")
    if "post_likes" in table_names:
        op.drop_index("ix_post_likes_user_id", table_name="post_likes")
        op.drop_index("ix_post_likes_post_id", table_name="post_likes")
        op.drop_table("post_likes")

    post_columns = {column["name"] for column in inspector.get_columns("posts")}
    with op.batch_alter_table("posts") as batch_op:
        if "is_featured" in post_columns:
            batch_op.drop_column("is_featured")

    if "xp_logs" in inspector.get_table_names():
        op.drop_index("ix_xp_logs_target_id", table_name="xp_logs")
        op.drop_index("ix_xp_logs_target_type", table_name="xp_logs")
        op.drop_index("ix_xp_logs_user_id", table_name="xp_logs")
        op.drop_table("xp_logs")

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    with op.batch_alter_table("users") as batch_op:
        if "title" in user_columns:
            batch_op.drop_column("title")
        if "level" in user_columns:
            batch_op.drop_column("level")
        if "xp" in user_columns:
            batch_op.drop_column("xp")
