from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import config

DATABASE_URL = config.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=config.DEBUG, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db():
    """Database dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создает таблицы в БД, если их еще нет."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine, checkfirst=True)


