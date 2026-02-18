"""add more bgg fields to games table and fix numeric types

Revision ID: 0002_add_more_bgg_fields
Revises: 0001_add_games_extra_fields
Create Date: 2026-02-18 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_more_bgg_fields"
down_revision: Union[str, None] = "0001_add_games_extra_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Числовые поля рейтингов на BGG должны быть float, а не int
    op.alter_column(
        "games",
        "bayesaverage",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        postgresql_using="bayesaverage::double precision",
        existing_nullable=True,
    )

    # Доп. параметры игры
    op.add_column("games", sa.Column("minplayers", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("maxplayers", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("playingtime", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("minplaytime", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("maxplaytime", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("minage", sa.Integer(), nullable=True))

    # Доп. статистика BGG
    op.add_column("games", sa.Column("average", sa.Float(), nullable=True))
    op.add_column("games", sa.Column("numcomments", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("owned", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("trading", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("wanting", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("wishing", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("averageweight", sa.Float(), nullable=True))
    op.add_column("games", sa.Column("numweights", sa.Integer(), nullable=True))

    # Списки из link-ов BGG. Храним в JSON-массивах.
    op.add_column("games", sa.Column("categories", sa.JSON(), nullable=True))
    op.add_column("games", sa.Column("mechanics", sa.JSON(), nullable=True))
    op.add_column("games", sa.Column("designers", sa.JSON(), nullable=True))
    op.add_column("games", sa.Column("publishers", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("games", "publishers")
    op.drop_column("games", "designers")
    op.drop_column("games", "mechanics")
    op.drop_column("games", "categories")

    op.drop_column("games", "numweights")
    op.drop_column("games", "averageweight")
    op.drop_column("games", "wishing")
    op.drop_column("games", "wanting")
    op.drop_column("games", "trading")
    op.drop_column("games", "owned")
    op.drop_column("games", "numcomments")
    op.drop_column("games", "average")

    op.drop_column("games", "minage")
    op.drop_column("games", "maxplaytime")
    op.drop_column("games", "minplaytime")
    op.drop_column("games", "playingtime")
    op.drop_column("games", "maxplayers")
    op.drop_column("games", "minplayers")

    op.alter_column(
        "games",
        "bayesaverage",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        postgresql_using="bayesaverage::integer",
        existing_nullable=True,
    )


