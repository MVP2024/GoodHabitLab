import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: str, message: str) -> Optional[Dict[str, Any]]:
    payload: Dict[str, str] = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        response: requests.Response = requests.post(
            f"{settings.TELEGRAM_API_URL}sendMessage", data=payload)
        response.raise_for_status()
        logger.info(f"Сообщение успешно отправлено в Telegram (chat_id: {chat_id}): {message}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram (chat_id: {chat_id}): {e}")
        return None
