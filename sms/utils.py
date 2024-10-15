from datetime import datetime
import dateutil.tz
import pygsm7

from sms.sms import Sms


def parse_sms(message) -> Sms:
    """Parse native SMS format to our structure."""

    return Sms(int(message['id']), message['number'], pygsm7.decodeMessage(message['content']),
               parse_sms_date(message['date']))


def parse_sms_date(date: str) -> datetime:
    """Parse SMS date to the standard datetime."""

    fields = date.split(",")

    year = fields[0]
    month = fields[1]
    day = fields[2]
    hours = fields[3]
    minutes = fields[4]
    seconds = fields[5]
    # timezone = fields[6]

    # Because of strange bug, we force local timezone.
    # return datetime(2000 + int(year), int(month), int(day), int(hours), int(minutes), int(seconds),
    #                tzinfo=dateutil.tz.tzoffset(None, 3600 * int(timezone)))
    return datetime(2000 + int(year), int(month), int(day), int(hours), int(minutes), int(seconds),
                    tzinfo=dateutil.tz.tzlocal())
