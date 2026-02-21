"""remove user_name from ratings

Revision ID: 0003_remove_user_name_from_ratings
Revises: 0002_add_user_model_and_update_ratings
Create Date: 2026-02-21 23:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_remove_user_name_from_ratings"
down_revision: Union[str, None] = "0002_add_user_model_and_update_ratings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаление индекса для user_name в ratings
    op.drop_index("ix_ratings_user_name", table_name="ratings")

    # Удаление колонки user_name из таблицы ratings
    op.drop_column("ratings", "user_name")


def downgrade() -> None:
    # Добавление колонки user_name обратно в таблицу ratings
    op.add_column("ratings", sa.Column("user_name", sa.String(), nullable=True))

    # Создание индекса для user_name в ratings
    op.create_index("ix_ratings_user_name", "ratings", ["user_name"], unique=False)