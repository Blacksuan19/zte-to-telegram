import hashlib
import logging

from zte.connection import ZteConnection
from zte.exception import ZteModemException


def _expected_password(password: str, ld: str) -> str:
    prefix = hashlib.sha256(password.encode("utf-8")).hexdigest().upper()
    return hashlib.sha256((prefix + ld.upper()).encode("utf-8")).hexdigest().upper()


def test_calculate_password_matches_sha256_chain():
    conn = ZteConnection(logging.getLogger("test"), "192.168.0.1", "secret")
    assert conn._calculate_password("abcdef") == _expected_password("secret", "abcdef")


def test_zte_modem_exception_is_exception():
    assert issubclass(ZteModemException, Exception)
