"""
Скрипт для проверки наличия таблиц в БД и их автоматического восстановления при необходимости.
"""
import sys
from sqlalchemy import text, inspect

from app.infrastructure.db import engine, Base
from app.infrastructure import models  # noqa: F401 - импортируем для регистрации моделей


def check_and_restore_tables() -> bool:
    """
    Проверяет наличие всех необходимых таблиц в БД.
    Если таблицы отсутствуют, автоматически восстанавливает их.
    
    :return: True если таблицы были восстановлены, False если всё уже было на месте
    """
    required_tables = ["games", "ratings", "ranking_sessions"]
    
    print("Checking database tables...")
    
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
    except Exception as e:
        print(f"⚠ Warning: Could not inspect database: {e}")
        print("Attempting to restore tables anyway...")
        existing_tables = set()
    
    missing_tables = [tbl for tbl in required_tables if tbl not in existing_tables]
    
    if not missing_tables:
        print("✓ All required tables exist.")
        return False
    
    print(f"⚠ Missing tables: {', '.join(missing_tables)}")
    print("Restoring tables...")
    
    try:
        # Восстанавливаем все таблицы
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        # Проверяем результат
        inspector = inspect(engine)
        existing_tables_after = set(inspector.get_table_names())
        
        still_missing = [tbl for tbl in required_tables if tbl not in existing_tables_after]
        
        if still_missing:
            print(f"✗ ERROR: Failed to create tables: {', '.join(still_missing)}")
            return False
        
        print("✓ Tables restored successfully!")
        
        # Помечаем миграции Alembic как применённые, чтобы избежать конфликтов
        if "alembic_version" not in existing_tables_after:
            try:
                import subprocess
                result = subprocess.run(
                    ["alembic", "-c", "alembic.ini", "stamp", "head"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print("✓ Alembic migrations stamped as applied.")
                else:
                    print(f"⚠ Warning: Could not stamp Alembic migrations: {result.stderr}")
            except Exception as e:
                print(f"⚠ Warning: Could not stamp Alembic migrations: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: Failed to restore tables: {e}")
        raise


if __name__ == "__main__":
    try:
        restored = check_and_restore_tables()
        sys.exit(0 if restored else 0)  # Всё ок в любом случае
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

