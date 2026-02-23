# Board Game Ranker - Test Suite

Этот каталог содержит полный набор тестов для проекта Board Game Ranker.

## Структура тестов

### Unit Tests (Модульные тесты)
- `test_repositories.py` - Тесты функций репозитория (сохранение/обновление игр)
- `test_config.py` - Тесты конфигурации приложения
- `test_fuzzy_matching.py` - Тесты логики fuzzy matching
- `test_bgg_api_mock.py` - Тесты BGG API с mocked ответами
- `test_translation_service.py` - Тесты сервиса перевода

### Integration Tests (Интеграционные тесты)
- `test_import.py` - Тесты импорта данных
- `test_import_integration.py` - Полный workflow импорта
- `test_game_search_improvement.py` - Тесты поиска игр
- `test_api_games.py` - Тесты API endpoints для игр
- `test_docker_setup.py` - Тесты Docker setup (запускаются только в контейнерах)

### Configuration
- `conftest.py` - Pytest fixtures и конфигурация
- `requirements-test.txt` - Зависимости для тестирования

## Запуск тестов

### Все тесты
```bash
pytest
```

### Только unit тесты
```bash
pytest -m "not integration"
```

### Только integration тесты
```bash
pytest -m integration
```

### С покрытием кода
```bash
pytest --cov=backend --cov-report=html
```

### Конкретный тест
```bash
pytest tests/test_repositories.py::TestGameRepository::test_save_game_from_bgg_data_new_game
```

## Тестовые fixtures

### Основные fixtures (conftest.py)
- `test_db` - In-memory SQLite база данных для тестов
- `sample_game_data` - Пример данных игры
- `sample_bgg_response` - Mock ответ BGG API
- `client_app` - FastAPI test client

### Специализированные fixtures
- `mock_bgg_search_response` - Mock ответ поиска BGG
- `mock_bgg_details_response` - Mock детальный ответ BGG
- `sample_import_row` - Пример строки импорта

## Типы тестов

### 1. Repository Tests
Тестируют бизнес-логику сохранения и обновления данных:
```python
def test_save_game_from_bgg_data_new_game(test_db, sample_bgg_response):
    game = save_game_from_bgg_data(test_db, sample_bgg_response)
    assert game.name == "Test Game"
```

### 2. API Tests
Тестируют HTTP endpoints:
```python
def test_search_games_in_db_success(client, sample_game):
    response = client.get("/api/games/search?name=Test")
    assert response.status_code == 200
```

### 3. Integration Tests
Тестируют полный workflow:
```python
def test_import_with_bgg_lookup(mock_details, mock_search, test_db):
    games_imported = replace_all_from_table(test_db, [import_data])
    assert games_imported == 1
```

## Mock стратегия

### BGG API Mocks
- Используем `unittest.mock` для mock HTTP запросов
- Предоставляем реалистичные XML ответы BGG API
- Тестируем как успешные, так и ошибочные сценарии

### Database Mocks
- In-memory SQLite для изоляции тестов
- Автоматическая очистка между тестами
- Фикстуры для создания тестовых данных

## Coverage

Цель - поддерживать coverage > 80% для основного кода.

### Исключаемые файлы
- `backend/app/main.py` - точка входа
- `backend/app/config.py` - конфигурация
- Миграции Alembic
- Скрипты

## CI/CD

Тесты запускаются в GitHub Actions:
- На pull requests
- На push в main branch
- С множеством Python версий

## Добавление новых тестов

### 1. Создайте тест файл
```python
# tests/test_new_feature.py
import pytest

class TestNewFeature:
    def test_something(self, test_db):
        # Your test here
        pass
```

### 2. Добавьте fixtures если нужно
```python
@pytest.fixture
def my_fixture():
    return {"key": "value"}
```

### 3. Запустите тесты
```bash
pytest tests/test_new_feature.py
```

## Troubleshooting

### Общие проблемы
1. **ImportError**: Проверьте PYTHONPATH
2. **Database locked**: Используйте test_db fixture
3. **Mock не работает**: Проверьте scope и target

### Полезные команды
```bash
# Подробный вывод
pytest -v

# Остановить на первой ошибке
pytest -x

# Показать stdout
pytest -s

# Ререн тестов с pdb
pytest --pdb
```