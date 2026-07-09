import logging
from datetime import datetime
from unittest.mock import patch

from sms.sms import Sms
from telegram.client import TelegramClient


def test_send_message_posts_formatted_text():
    sms = Sms(1, "+15551234567", "Hello world", datetime(2024, 3, 7, 14, 30, 5))
    client = TelegramClient(logging.getLogger("test"), "BOT123", "CHAT456")

    with patch("telegram.client.requests.post") as post:
        client.send_message(sms)

    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == "https://api.telegram.org/botBOT123/sendMessage"
    assert kwargs["params"]["chat_id"] == "CHAT456"
    text = kwargs["params"]["text"]
    assert "+15551234567" in text
    assert "Hello world" in text
