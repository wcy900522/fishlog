"""add catalog modules

Revision ID: 20260707_0006
Revises: 20260707_0005
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260707_0006"
down_revision = "20260707_0005"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())

    if "fish_species" not in table_names:
        op.create_table(
            "fish_species",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.VARCHAR(length=80), nullable=False),
            sa.Column("category", sa.VARCHAR(length=50), nullable=True),
            sa.Column("image_url", sa.VARCHAR(length=255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("common_methods", sa.Text(), nullable=True),
            sa.Column("common_baits", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )

    if "baits" not in table_names:
        op.create_table(
            "baits",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.VARCHAR(length=100), nullable=False),
            sa.Column("bait_type", sa.VARCHAR(length=50), nullable=False),
            sa.Column("brand", sa.VARCHAR(length=100), nullable=True),
            sa.Column("target_species", sa.Text(), nullable=True),
            sa.Column("water_type", sa.VARCHAR(length=50), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )

    if "equipment" not in table_names:
        op.create_table(
            "equipment",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.VARCHAR(length=100), nullable=False),
            sa.Column("equipment_type", sa.VARCHAR(length=50), nullable=False),
            sa.Column("brand", sa.VARCHAR(length=100), nullable=True),
            sa.Column("model", sa.VARCHAR(length=100), nullable=True),
            sa.Column("parameters", sa.Text(), nullable=True),
            sa.Column("purchased_at", sa.DateTime(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_equipment_user_id", "equipment", ["user_id"])


def downgrade():
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())

    if "equipment" in table_names:
        op.drop_index("ix_equipment_user_id", table_name="equipment")
        op.drop_table("equipment")
    if "baits" in table_names:
        op.drop_table("baits")
    if "fish_species" in table_names:
        op.drop_table("fish_species")
