#!/usr/bin/env python3
"""
Скрипт для миграции базы данных с Integer ID на UUID.

Этот скрипт изменяет типы колонок id в таблицах games, ratings и ranking_sessions
с INTEGER на UUID. Также обновляет внешние ключи.

ВНИМАНИЕ: Этот скрипт изменяет структуру базы данных!
Рекомендуется сделать бэкап перед запуском.

Запуск:
    python scripts/migrate_to_uuid.py
"""

import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.infrastructure.db import get_db_url

def migrate_to_uuid():
    """Выполняет миграцию базы данных на UUID"""
    print("🔄 Начинаю миграцию базы данных на UUID...")

    db_url = get_db_url()
    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            # Начинаем транзакцию
            trans = conn.begin()

            print("📋 Проверяю текущую структуру таблиц...")

            # Проверяем, что таблицы существуют и имеют правильную структуру
            result = conn.execute(text("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_name IN ('games', 'ratings', 'ranking_sessions')
                AND column_name = 'id'
                ORDER BY table_name;
            """))

            current_structure = list(result)
            print("Текущая структура ID колонок:")
            for table, column, data_type in current_structure:
                print(f"  {table}.{column}: {data_type}")

            # Проверяем, что все ID колонки имеют тип integer
            integer_ids = [row for row in current_structure if row[2] == 'integer']
            if len(integer_ids) != 3:
                print("❌ Не все ID колонки имеют тип integer. Миграция невозможна.")
                trans.rollback()
                return False

            print("✅ Структура корректна для миграции")

            # Добавляем колонки с UUID
            print("🔧 Добавляю новые UUID колонки...")

            # Для games
            conn.execute(text("""
                ALTER TABLE games ADD COLUMN id_uuid UUID DEFAULT gen_random_uuid();
                UPDATE games SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL;
                ALTER TABLE games ALTER COLUMN id_uuid SET NOT NULL;
            """))

            # Для ratings
            conn.execute(text("""
                ALTER TABLE ratings ADD COLUMN id_uuid UUID DEFAULT gen_random_uuid();
                UPDATE ratings SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL;
                ALTER TABLE ratings ALTER COLUMN id_uuid SET NOT NULL;

                ALTER TABLE ratings ADD COLUMN game_id_uuid UUID;
                UPDATE ratings SET game_id_uuid = games.id_uuid
                FROM games WHERE ratings.game_id = games.id;
                ALTER TABLE ratings ALTER COLUMN game_id_uuid SET NOT NULL;
            """))

            # Для ranking_sessions
            conn.execute(text("""
                ALTER TABLE ranking_sessions ADD COLUMN id_uuid UUID DEFAULT gen_random_uuid();
                UPDATE ranking_sessions SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL;
                ALTER TABLE ranking_sessions ALTER COLUMN id_uuid SET NOT NULL;
            """))

            print("🔄 Обновляю внешние ключи и индексы...")

            # Удаляем старые внешние ключи и индексы
            conn.execute(text("ALTER TABLE ratings DROP CONSTRAINT IF EXISTS ratings_game_id_fkey;"))
            conn.execute(text("DROP INDEX IF EXISTS ix_games_id;"))
            conn.execute(text("DROP INDEX IF EXISTS ix_ratings_id;"))
            conn.execute(text("DROP INDEX IF EXISTS ix_ratings_game_id;"))
            conn.execute(text("DROP INDEX IF EXISTS ix_ranking_sessions_id;"))

            # Переименовываем колонки
            conn.execute(text("ALTER TABLE games RENAME COLUMN id TO id_old;"))
            conn.execute(text("ALTER TABLE games RENAME COLUMN id_uuid TO id;"))

            conn.execute(text("ALTER TABLE ratings RENAME COLUMN id TO id_old;"))
            conn.execute(text("ALTER TABLE ratings RENAME COLUMN id_uuid TO id;"))
            conn.execute(text("ALTER TABLE ratings RENAME COLUMN game_id TO game_id_old;"))
            conn.execute(text("ALTER TABLE ratings RENAME COLUMN game_id_uuid TO game_id;"))

            conn.execute(text("ALTER TABLE ranking_sessions RENAME COLUMN id TO id_old;"))
            conn.execute(text("ALTER TABLE ranking_sessions RENAME COLUMN id_uuid TO id;"))

            # Создаем новые индексы
            conn.execute(text("CREATE UNIQUE INDEX ix_games_id ON games(id);"))
            conn.execute(text("CREATE UNIQUE INDEX ix_ratings_id ON ratings(id);"))
            conn.execute(text("CREATE INDEX ix_ratings_game_id ON ratings(game_id);"))
            conn.execute(text("CREATE UNIQUE INDEX ix_ranking_sessions_id ON ranking_sessions(id);"))

            # Добавляем новые внешние ключи
            conn.execute(text("""
                ALTER TABLE ratings ADD CONSTRAINT ratings_game_id_fkey
                FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE;
            """))

            # Удаляем старые колонки
            print("🗑️ Удаляю старые колонки...")
            conn.execute(text("ALTER TABLE games DROP COLUMN id_old;"))
            conn.execute(text("ALTER TABLE ratings DROP COLUMN id_old;"))
            conn.execute(text("ALTER TABLE ratings DROP COLUMN game_id_old;"))
            conn.execute(text("ALTER TABLE ranking_sessions DROP COLUMN id_old;"))

            # Завершаем транзакцию
            trans.commit()

            print("✅ Миграция завершена успешно!")
            print("📊 Новая структура:")
            print("  - games.id: UUID")
            print("  - ratings.id: UUID")
            print("  - ratings.game_id: UUID (ссылка на games.id)")
            print("  - ranking_sessions.id: UUID")

            return True

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        if 'trans' in locals():
            trans.rollback()
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    success = migrate_to_uuid()
    sys.exit(0 if success else 1)