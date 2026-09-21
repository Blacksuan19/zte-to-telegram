import hashlib
import logging
from unittest.mock import patch

import pytest
from Crypto.PublicKey import RSA

from zte.connection import ZteConnection
from zte.exception import ZteModemException

# Generated once and reused: login() RSA-encrypts a session key against the
# device's public key, so tests need a real (but throwaway) key pair to mock it.
_TEST_RSA_KEY = RSA.generate(2048)
_TEST_PUBLIC_PEM = (
    _TEST_RSA_KEY.publickey().export_key().decode("ascii").replace("\n", "")
)


def _expected_password(password: str, ld: str) -> str:
    prefix = hashlib.sha256(password.encode("utf-8")).hexdigest().upper()
    return hashlib.sha256((prefix + ld.upper()).encode("utf-8")).hexdigest().upper()


class MockResponse:
    """Minimal stand-in for ``requests.Response`` used by the ZTE client."""

    def __init__(self, json_data=None, cookies=None, raise_for_status=None):
        self._json = json_data if json_data is not None else {}
        self.cookies = _Cookies(cookies or {})
        self.content = b"<content>"
        self._raise = raise_for_status

    def json(self):
        return self._json

    def raise_for_status(self):
        if self._raise is not None:
            raise self._raise


class _Cookies:
    def __init__(self, data):
        self._data = data

    def get(self, key):
        return self._data.get(key)


def _conn():
    return ZteConnection(logging.getLogger("test"), "192.168.0.1", "secret")


def _authenticate(conn):
    """Populate the private session fields as a successful login would."""

    conn._ZteConnection__cookie = "tok"
    conn._ZteConnection__cr_version = "CR"
    conn._ZteConnection__wa_inner_version = "WA"


def test_calculate_password_matches_sha256_chain():
    assert _conn()._calculate_password("abcdef") == _expected_password(
        "secret", "abcdef"
    )


def test_zte_modem_exception_is_exception():
    assert issubclass(ZteModemException, Exception)


def test_login_full_flow_stores_cookie():
    conn = _conn()
    get_responses = [
        MockResponse(
            {"cr_version": "CR", "wa_inner_version": "WA"}
        ),  # __parse_device_version
        MockResponse({"LD": "abcdef"}),  # __get_ld
        MockResponse({"result": _TEST_PUBLIC_PEM}),  # web_crt_get
        MockResponse({"RD": "abc"}),  # __get_rd (for the encryption session AD)
    ]
    login_response = MockResponse({"result": "0"}, cookies={"stok": "cookie-value"})
    enstr_response = MockResponse({"result": "success"})

    with (
        patch("zte.connection.requests.get", side_effect=get_responses) as get,
        patch(
            "zte.connection.requests.post", side_effect=[login_response, enstr_response]
        ) as post,
    ):
        conn.login()

    assert conn._ZteConnection__cookie == "cookie-value"
    assert conn._ZteConnection__cr_version == "CR"
    assert conn._ZteConnection__wa_inner_version == "WA"
    assert conn._ZteConnection__session_key is not None
    assert get.call_count == 4
    # The posted password must be the hashed value, never the plaintext.
    posted_password = post.call_args_list[0].kwargs["data"]["password"]
    assert posted_password == _expected_password("secret", "abcdef")


def test_get_ld_missing_raises():
    conn = _conn()
    responses = [
        MockResponse({"cr_version": "CR", "wa_inner_version": "WA"}),
        MockResponse({}),  # no LD key
    ]
    with patch("zte.connection.requests.get", side_effect=responses):
        with pytest.raises(ZteModemException):
            conn.login()


def test_login_non_successful_result_raises():
    conn = _conn()
    responses = [
        MockResponse({"cr_version": "CR", "wa_inner_version": "WA"}),
        MockResponse({"LD": "abcdef"}),
    ]
    with (
        patch("zte.connection.requests.get", side_effect=responses),
        patch(
            "zte.connection.requests.post", return_value=MockResponse({"result": "1"})
        ),
    ):
        with pytest.raises(ZteModemException):
            conn.login()


def test_login_missing_cookie_raises():
    conn = _conn()
    responses = [
        MockResponse({"cr_version": "CR", "wa_inner_version": "WA"}),
        MockResponse({"LD": "abcdef"}),
    ]
    with (
        patch("zte.connection.requests.get", side_effect=responses),
        patch(
            "zte.connection.requests.post",
            return_value=MockResponse({"result": "0"}, cookies={}),
        ),
    ):
        with pytest.raises(ZteModemException):
            conn.login()


def test_logout_success():
    conn = _conn()
    _authenticate(conn)
    with (
        patch("zte.connection.requests.get", return_value=MockResponse({"RD": "abc"})),
        patch(
            "zte.connection.requests.post",
            return_value=MockResponse({"result": "success"}),
        ) as post,
    ):
        conn.logout()
    assert post.call_args.kwargs["data"]["goformId"] == "LOGOUT"


def test_get_rd_missing_raises():
    conn = _conn()
    _authenticate(conn)
    with patch("zte.connection.requests.get", return_value=MockResponse({})):
        with pytest.raises(ZteModemException):
            conn.logout()


def test_logout_non_successful_result_raises():
    conn = _conn()
    _authenticate(conn)
    with (
        patch("zte.connection.requests.get", return_value=MockResponse({"RD": "abc"})),
        patch(
            "zte.connection.requests.post",
            return_value=MockResponse({"result": "fail"}),
        ),
    ):
        with pytest.raises(ZteModemException):
            conn.logout()


def _sms_list(*messages):
    return MockResponse({"messages": list(messages)})


_READ = {"tag": "1", "received_all_concat_sms": "1", "id": "1"}
_ALREADY_READ = {"tag": "0", "received_all_concat_sms": "1", "id": "2"}


def test_get_all_sms_unread_filters_by_tag():
    conn = _conn()
    _authenticate(conn)
    with patch(
        "zte.connection.requests.get", return_value=_sms_list(_READ, _ALREADY_READ)
    ):
        result = conn.get_all_sms(unread=True)
    assert [m["id"] for m in result] == ["1"]


def test_get_all_sms_all_includes_read():
    conn = _conn()
    _authenticate(conn)
    with patch(
        "zte.connection.requests.get", return_value=_sms_list(_READ, _ALREADY_READ)
    ):
        result = conn.get_all_sms(unread=False)
    assert {m["id"] for m in result} == {"1", "2"}


def test_read_all_sms_empty_returns_early():
    conn = _conn()
    _authenticate(conn)
    with (
        patch(
            "zte.connection.requests.get", return_value=_sms_list(_ALREADY_READ)
        ) as get,
        patch("zte.connection.requests.post") as post,
    ):
        result = conn.read_all_sms(delete=True)
    assert result == []
    # No RD fetch or delete when there is nothing to read.
    assert get.call_count == 1
    post.assert_not_called()


def test_read_all_sms_delete_flow():
    conn = _conn()
    _authenticate(conn)
    get_responses = [
        _sms_list(_READ),  # __get_sms_list
        MockResponse({"RD": "abc"}),  # __get_rd
    ]
    with (
        patch("zte.connection.requests.get", side_effect=get_responses),
        patch(
            "zte.connection.requests.post",
            return_value=MockResponse({"result": "success"}),
        ) as post,
    ):
        result = conn.read_all_sms(delete=True)
    assert [m["id"] for m in result] == ["1"]
    assert post.call_args.kwargs["data"]["goformId"] == "DELETE_SMS"


def test_read_all_sms_mark_read_flow():
    conn = _conn()
    _authenticate(conn)
    get_responses = [
        _sms_list(_READ),
        MockResponse({"RD": "abc"}),
    ]
    with (
        patch("zte.connection.requests.get", side_effect=get_responses),
        patch(
            "zte.connection.requests.post",
            return_value=MockResponse({"result": "success"}),
        ) as post,
    ):
        conn.read_all_sms(delete=False)
    assert post.call_args.kwargs["data"]["goformId"] == "SET_MSG_READ"


def test_read_all_sms_non_successful_result_raises():
    conn = _conn()
    _authenticate(conn)
    get_responses = [
        _sms_list(_READ),
        MockResponse({"RD": "abc"}),
    ]
    with (
        patch("zte.connection.requests.get", side_effect=get_responses),
        patch(
            "zte.connection.requests.post",
            return_value=MockResponse({"result": "error"}),
        ),
    ):
        with pytest.raises(ZteModemException):
            conn.read_all_sms(delete=True)
