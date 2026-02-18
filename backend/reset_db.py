"""
Скрипт для полного восстановления таблиц в БД.

Использование:
    python reset_db.py          # Пересоздать все таблицы
    python reset_db.py --force  # Принудительно удалить и пересоздать
"""
import sys
from sqlalchemy import text

from app.infrastructure.db import engine, Base
from app.infrastructure import models  # noqa: F401 - импортируем для регистрации моделей


def reset_database(force: bool = False) -> None:
    """
    Восстанавливает все таблицы в БД.
    
    :param force: Если True, сначала удаляет все таблицы, затем создаёт заново.
    """
    print("=== Database Reset ===")
    
    with engine.connect() as conn:
        if force:
            print("Dropping all tables...")
            # Удаляем все таблицы в правильном порядке (с учётом foreign keys)
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS ratings CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS ranking_sessions CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS games CASCADE"))
            # Удаляем типы ENUM, если они есть
            conn.execute(text("DROP TYPE IF EXISTS gamegenre CASCADE"))
            conn.commit()
            print("All tables dropped.")
        
        print("Creating all tables...")
        # Создаём все таблицы заново
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("Tables created successfully!")
        
        # Проверяем, какие таблицы созданы
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"\nCreated tables: {', '.join(tables)}")
        
        # Применяем миграции Alembic (если нужно)
        print("\nApplying Alembic migrations...")
        import subprocess
        result = subprocess.run(
            ["alembic", "-c", "alembic.ini", "stamp", "head"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Alembic migrations stamped as applied.")
        else:
            print(f"Warning: Could not stamp Alembic migrations: {result.stderr}")
    
    print("\n=== Database reset complete! ===")


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    try:
        reset_database(force=force)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

