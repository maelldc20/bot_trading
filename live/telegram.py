import os
import requests
import logging

log = logging.getLogger(__name__)


def send_telegram(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        log.warning("Telegram non configuré.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        log.error(f"Erreur Telegram : {e}")
