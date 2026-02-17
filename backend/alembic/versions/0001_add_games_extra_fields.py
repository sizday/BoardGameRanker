"""add extra fields to games table

Revision ID: 0001_add_games_extra_fields
Revises: 
Create Date: 2026-02-17 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_add_games_extra_fields"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Дополнительные поля BGG и метаданные в таблице games
    with op.batch_alter_table("games") as batch_op:
        batch_op.add_column(sa.Column("bgg_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("yearpublished", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("bayesaverage", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("usersrated", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("image", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("thumbnail", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # Индекс для bgg_id
    op.create_index("ix_games_bgg_id", "games", ["bgg_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_games_bgg_id", table_name="games")

    with op.batch_alter_table("games") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("description")
        batch_op.drop_column("thumbnail")
        batch_op.drop_column("image")
        batch_op.drop_column("usersrated")
        batch_op.drop_column("bayesaverage")
        batch_op.drop_column("yearpublished")
        batch_op.drop_column("bgg_id")


