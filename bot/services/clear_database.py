import logging

import httpx

logger = logging.getLogger(__name__)


async def clear_database(api_base_url: str) -> dict:
    """
    Очищает всю базу данных через backend API.

    Возвращает статистику удаленных записей.
    Может возбуждать RuntimeError при ошибках API.
    """
    logger.info("Starting database cleanup")

    clear_url = f"{api_base_url}/api/clear-database"
    logger.info(f"Sending clear request to: {clear_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                clear_url,
                json={"confirm": True},
            )
            resp.raise_for_status()

        result = resp.json()
        logger.info(f"Database cleared successfully: {result}")

        return result

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during database clear: {e.response.status_code} - {e.response.text}")
        raise RuntimeError(f"Ошибка API при очистке базы данных: {e.response.status_code}")

    except Exception as e:
        logger.error(f"Unexpected error during database clear: {e}", exc_info=True)
        raise RuntimeError(f"Неожиданная ошибка при очистке базы данных: {e}")