from datetime import datetime


class Sms:
    """Definition of SMS message."""

    sms_id: int
    """ID of SMS on the device."""

    number: str
    """Phone number."""

    content: str
    """SMS text."""

    date: datetime
    """Date and time when SMS was sent."""

    def __init__(self, sms_id: int, number: str, content: str, date: datetime):
        self.sms_id = sms_id
        self.number = number
        self.content = content
        self.date = date
