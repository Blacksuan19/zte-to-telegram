import requests

from sms.sms import Sms


def send_message(bot_id: str, chat_id: str, sms: Sms):
    """Send Telegram message."""

    text = 'SMS\n\n'
    text += 'From: {}\n'.format(sms.number)
    text += 'Date: {}\n\n'.format(sms.date)
    text += sms.content

    url = 'https://api.telegram.org/bot{}/sendMessage'.format(bot_id)
    params = {"chat_id": chat_id, "text": text}
    requests.post(url, params=params)
