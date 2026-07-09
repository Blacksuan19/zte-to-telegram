from dataclasses import dataclass
from datetime import datetime


@dataclass
class Sms:
    """A single SMS message read from the modem."""

    sms_id: int
    """ID of the SMS on the device."""

    number: str
    """Sender phone number."""

    content: str
    """Decoded SMS text."""

    date: datetime
    """Date and time the SMS was sent."""
