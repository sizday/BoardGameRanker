import csv
import io
from typing import List, Dict

import httpx


def _parse_int_or_none(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


async def import_ratings_from_sheet(
    api_base_url: str,
    sheet_csv_url: str,
) -> int:
    """
    Загружает CSV из Google-таблицы, парсит её и отправляет данные в backend API.

    Возвращает количество импортированных игр.
    Может возбуждать ValueError при проблемах с форматом данных.
    """
    if not sheet_csv_url:
        raise ValueError(
            "Переменная окружения RATING_SHEET_CSV_URL не задана. "
            "Укажи ссылку на CSV Google-таблицы в конфигурации бота."
        )

    async with httpx.AsyncClient() as client:
        resp = await client.get(sheet_csv_url)
        resp.raise_for_status()

    text = resp.text
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return 0

    header = rows[0]
    if len(header) < 5:
        raise ValueError("Неожиданный формат таблицы: ожидается минимум 5 колонок.")

    # Предполагаемый формат:
    # 0: название игры
    # 1: место на BGG
    # 2: место Низа Гамс
    # 3: жанр
    # 4..N: имена пользователей (столбцы рейтингов)
    user_names: List[str] = [h.strip() for h in header[4:] if h.strip()]

    data_rows: List[Dict] = []
    for row in rows[1:]:
        # пропустим полностью пустые строки
        if not any(cell.strip() for cell in row):
            continue

        name = (row[0] or "").strip() if len(row) > 0 else ""
        if not name:
            continue

        bgg_rank = _parse_int_or_none(row[1]) if len(row) > 1 else None
        niza_rank = _parse_int_or_none(row[2]) if len(row) > 2 else None
        genre = (row[3] or "").strip().lower() if len(row) > 3 else None

        ratings: Dict[str, int] = {}
        for idx, user_name in enumerate(user_names, start=4):
            if idx >= len(row):
                continue
            cell = (row[idx] or "").strip()
            if not cell or cell.lower() == "нет":
                continue
            try:
                ratings[user_name] = int(cell)
            except ValueError:
                # игнорируем некорректные значения
                continue

        data_rows.append(
            {
                "name": name,
                "bgg_rank": bgg_rank,
                "niza_games_rank": niza_rank,
                "genre": genre or None,
                "ratings": ratings,
            }
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{api_base_url}/api/import-table",
            json={"rows": data_rows},
            timeout=60.0,
        )
        resp.raise_for_status()

    return len(data_rows)


