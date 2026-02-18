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
    # Для PostgreSQL используем стандартный синтаксис Alembic
    # Если колонки уже существуют, миграция упадёт - это нормально при повторном запуске
    op.add_column("games", sa.Column("bgg_id", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("yearpublished", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("bayesaverage", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("usersrated", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("image", sa.String(), nullable=True))
    op.add_column("games", sa.Column("thumbnail", sa.String(), nullable=True))
    op.add_column("games", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("games", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("games", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # Индекс для bgg_id
    op.create_index("ix_games_bgg_id", "games", ["bgg_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_games_bgg_id", table_name="games")

    op.drop_column("games", "updated_at")
    op.drop_column("games", "created_at")
    op.drop_column("games", "description")
    op.drop_column("games", "thumbnail")
    op.drop_column("games", "image")
    op.drop_column("games", "usersrated")
    op.drop_column("games", "bayesaverage")
    op.drop_column("games", "yearpublished")
    op.drop_column("games", "bgg_id")


