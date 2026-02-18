"""add description_ru field to games table

Revision ID: 0003_add_description_ru_field
Revises: 0002_add_more_bgg_fields
Create Date: 2026-02-18 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_add_description_ru_field"
down_revision: Union[str, None] = "0002_add_more_bgg_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле для русского перевода описания игры
    op.add_column("games", sa.Column("description_ru", sa.Text(), nullable=True))


def downgrade() -> None:
    # Удаляем поле русского перевода описания
    op.drop_column("games", "description_ru")