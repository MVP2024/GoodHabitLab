import os
import logging
from typing import Any, Dict, Optional, List
from django.conf import settings
import requests
from dotenv import load_dotenv
import json


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


def send_telegram_message_with_keyboard(
    chat_id: str, message: str, keyboard: List[List[Dict[str, str]]]
) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": json.dumps({"inline_keyboard": keyboard}),
    }
    try:
        response: requests.Response = requests.post(
            f"{settings.TELEGRAM_API_URL}sendMessage", json=payload
        )
        response.raise_for_status()
        logger.info(f"Сообщение с кнопками успешно отправлено в Telegram (chat_id: {chat_id}): {message}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке сообщения с кнопками в Telegram (chat_id: {chat_id}): {e}")
        return None


def remove_inline_keyboard(chat_id: str, message_id: int) -> Optional[Dict[str, Any]]:
    """
    Удаляет inline-клавиатуру из существующего сообщения.
    """
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": json.dumps({"inline_keyboard": []}), # Пустая клавиатура для удаления
    }
    try:
        response: requests.Response = requests.post(
            f"{settings.TELEGRAM_API_URL}editMessageReplyMarkup", json=payload
        )
        response.raise_for_status()
        logger.info(f"Inline-клавиатура удалена из сообщения (chat_id: {chat_id}, message_id: {message_id})")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при удалении inline-клавиатуры (chat_id: {chat_id}, message_id: {message_id}): {e}")
        return None
