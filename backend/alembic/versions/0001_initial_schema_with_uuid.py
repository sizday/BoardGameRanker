"""initial schema with UUID

Revision ID: 0001_initial_schema_with_uuid
Revises:
Create Date: 2026-02-19 13:37:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "0001_initial_schema_with_uuid"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы games с UUID
    op.create_table(
        "games",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("bgg_id", sa.Integer(), nullable=True),
        sa.Column("bgg_rank", sa.Integer(), nullable=True),
        sa.Column("niza_games_rank", sa.Integer(), nullable=True),
        sa.Column("genre", sa.Enum("STRATEGY", "FAMILY", "PARTY", "COOP", "AMERITRASH", "EURO", "ABSTRACT", name="gamegenre"), nullable=True),
        sa.Column("yearpublished", sa.Integer(), nullable=True),
        sa.Column("bayesaverage", sa.Float(), nullable=True),
        sa.Column("usersrated", sa.Integer(), nullable=True),
        sa.Column("minplayers", sa.Integer(), nullable=True),
        sa.Column("maxplayers", sa.Integer(), nullable=True),
        sa.Column("playingtime", sa.Integer(), nullable=True),
        sa.Column("minplaytime", sa.Integer(), nullable=True),
        sa.Column("maxplaytime", sa.Integer(), nullable=True),
        sa.Column("minage", sa.Integer(), nullable=True),
        sa.Column("average", sa.Float(), nullable=True),
        sa.Column("numcomments", sa.Integer(), nullable=True),
        sa.Column("owned", sa.Integer(), nullable=True),
        sa.Column("trading", sa.Integer(), nullable=True),
        sa.Column("wanting", sa.Integer(), nullable=True),
        sa.Column("wishing", sa.Integer(), nullable=True),
        sa.Column("averageweight", sa.Float(), nullable=True),
        sa.Column("numweights", sa.Integer(), nullable=True),
        sa.Column("categories", sa.JSON(), nullable=True),
        sa.Column("mechanics", sa.JSON(), nullable=True),
        sa.Column("designers", sa.JSON(), nullable=True),
        sa.Column("publishers", sa.JSON(), nullable=True),
        sa.Column("image", sa.String(), nullable=True),
        sa.Column("thumbnail", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Создание таблицы ratings
    op.create_table(
        "ratings",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_name", sa.String(), nullable=False),
        sa.Column("game_id", UUID(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Создание таблицы ranking_sessions
    op.create_table(
        "ranking_sessions",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_name", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("games", sa.JSON(), nullable=False),
        sa.Column("first_tiers", sa.JSON(), nullable=False),
        sa.Column("second_tiers", sa.JSON(), nullable=False),
        sa.Column("candidate_ids", sa.JSON(), nullable=True),
        sa.Column("group_orders", sa.JSON(), nullable=True),
        sa.Column("final_order", sa.JSON(), nullable=True),
        sa.Column("current_index_first", sa.Integer(), nullable=False),
        sa.Column("current_index_second", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Создание индексов
    op.create_index("ix_games_id", "games", ["id"], unique=False)
    op.create_index("ix_games_bgg_id", "games", ["bgg_id"], unique=False)
    op.create_index("ix_ratings_id", "ratings", ["id"], unique=False)
    op.create_index("ix_ratings_game_id", "ratings", ["game_id"], unique=False)
    op.create_index("ix_ratings_user_name", "ratings", ["user_name"], unique=False)
    op.create_index("ix_ranking_sessions_id", "ranking_sessions", ["id"], unique=False)
    op.create_index("ix_ranking_sessions_user_name", "ranking_sessions", ["user_name"], unique=False)


def downgrade() -> None:
    # Удаление индексов
    op.drop_index("ix_ranking_sessions_user_name", table_name="ranking_sessions")
    op.drop_index("ix_ranking_sessions_id", table_name="ranking_sessions")
    op.drop_index("ix_ratings_user_name", table_name="ratings")
    op.drop_index("ix_ratings_game_id", table_name="ratings")
    op.drop_index("ix_ratings_id", table_name="ratings")
    op.drop_index("ix_games_bgg_id", table_name="games")
    op.drop_index("ix_games_id", table_name="games")

    # Удаление таблиц
    op.drop_table("ranking_sessions")
    op.drop_table("ratings")
    op.drop_table("games")

    # Удаление enum
    op.execute("DROP TYPE IF EXISTS gamegenre")