from logging import Logger

import requests

from sms.sms import Sms

API_BASE = "https://api.telegram.org/bot{}/sendMessage"
REQUEST_TIMEOUT = 30


class TelegramClient:
    """Sends SMS messages to a Telegram chat via the Bot API."""

    __logger: Logger
    __bot_id: str
    __chat_id: str

    def __init__(self, logger: Logger, bot_id: str, chat_id: str):
        self.__logger = logger
        self.__bot_id = bot_id
        self.__chat_id = chat_id

    def send_message(self, sms: Sms) -> None:
        """Forward a single SMS to the configured Telegram chat."""

        text = "SMS\n\n"
        text += f"From: {sms.number}\n"
        text += f"Date: {sms.date}\n\n"
        text += sms.content

        url = API_BASE.format(self.__bot_id)
        self.__logger.debug("send_message: forwarding SMS %s from %s", sms.sms_id, sms.number)
        r = requests.post(url, params={"chat_id": self.__chat_id, "text": text}, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
