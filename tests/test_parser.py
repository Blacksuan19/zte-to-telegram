from datetime import datetime

from sms.parser import parse_sms, parse_sms_date
from sms.sms import Sms


def test_parse_sms_date_builds_local_datetime():
    # ZTE date format: yy,mm,dd,HH,MM,SS,tz
    result = parse_sms_date("24,03,07,14,30,05,8")
    assert (result.year, result.month, result.day) == (2024, 3, 7)
    assert (result.hour, result.minute, result.second) == (14, 30, 5)
    # Workaround forces local tz (not the reported offset), so tzinfo is set.
    assert result.tzinfo is not None


def test_parse_sms_maps_raw_message():
    # "Test" UTF-16 hex: pygsm7.decodeMessage("0054006500730074") == "Test"
    message = {"id": "12", "number": "+15551234567", "content": "0054006500730074", "date": "24,03,07,14,30,05,8"}
    sms = parse_sms(message)
    assert isinstance(sms, Sms)
    assert sms.sms_id == 12
    assert sms.number == "+15551234567"
    assert sms.content == "Test"
    assert sms.date == datetime(2024, 3, 7, 14, 30, 5, tzinfo=sms.date.tzinfo)
