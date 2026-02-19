#!/usr/bin/env python3
import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.infrastructure.db import SessionLocal
from app.infrastructure.models import RatingModel

def check_obshii_ratings():
    db = SessionLocal()
    try:
        # Проверим, есть ли рейтинги для пользователя 'Общий'
        obshii_ratings = db.query(RatingModel).filter(RatingModel.user_name.ilike('%общий%')).all()
        print(f'Найдено рейтингов для пользователя "Общий": {len(obshii_ratings)}')

        if obshii_ratings:
            print('Примеры:')
            for r in obshii_ratings[:5]:
                print(f'  - Game ID: {r.game_id}, User: {repr(r.user_name)}, Rank: {r.rank}')

        # Проверим общее количество рейтингов
        total_ratings = db.query(RatingModel).count()
        print(f'Общее количество рейтингов в БД: {total_ratings}')

        # Проверим уникальных пользователей
        unique_users = db.query(RatingModel.user_name).distinct().all()
        print(f'Уникальные пользователи: {[u[0] for u in unique_users]}')

    finally:
        db.close()

if __name__ == '__main__':
    check_obshii_ratings()