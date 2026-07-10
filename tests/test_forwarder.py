import logging
from unittest.mock import patch

from forwarder import Forwarder


class FakeConnection:
    def __init__(self, messages, raise_on_login=False):
        self._messages = messages
        self._raise_on_login = raise_on_login
        self.logged_in = False
        self.logged_out = False
        self.delete_arg = None

    def login(self):
        if self._raise_on_login:
            raise RuntimeError("boom")
        self.logged_in = True

    def read_all_sms(self, delete):
        self.delete_arg = delete
        return self._messages

    def logout(self):
        self.logged_out = True


class FakeTelegram:
    def __init__(self):
        self.sent = []

    def send_message(self, sms):
        self.sent.append(sms)


class FailingMiddleTelegram:
    """Raises when forwarding the second SMS it sees; otherwise records it."""

    def __init__(self):
        self.sent = []
        self._calls = 0

    def send_message(self, sms):
        self._calls += 1
        if self._calls == 2:
            raise RuntimeError("boom")
        self.sent.append(sms)


def _raw(i):
    return {"id": str(i), "number": "+1555000000" + str(i), "content": "D4F29C0E", "date": "24,03,07,14,30,05,8"}


def test_run_once_forwards_each_sms_and_logs_out():
    conn = FakeConnection([_raw(1), _raw(2)])
    tg = FakeTelegram()
    fwd = Forwarder(logging.getLogger("test"), conn, tg, delete=True)

    count = fwd.run_once()

    assert count == 2
    assert len(tg.sent) == 2
    assert conn.logged_in and conn.logged_out
    assert conn.delete_arg is True


def test_run_once_honors_mark_read():
    conn = FakeConnection([])
    fwd = Forwarder(logging.getLogger("test"), conn, FakeTelegram(), delete=False)
    fwd.run_once()
    assert conn.delete_arg is False


def test_run_once_logs_out_even_on_error():
    conn = FakeConnection([], raise_on_login=True)
    fwd = Forwarder(logging.getLogger("test"), conn, FakeTelegram(), delete=True)
    try:
        fwd.run_once()
    except RuntimeError:
        pass
    # login failed before a session existed; logout must not be attempted.
    assert conn.logged_out is False


def test_run_once_isolates_single_message_forward_failure():
    conn = FakeConnection([_raw(1), _raw(2), _raw(3)])
    tg = FailingMiddleTelegram()
    fwd = Forwarder(logging.getLogger("test"), conn, tg, delete=True)

    count = fwd.run_once()

    assert count == 2
    assert len(tg.sent) == 2


class _StopLoop(Exception):
    pass


def test_run_loop_swallows_cycle_errors_and_sleeps():
    conn = FakeConnection([], raise_on_login=True)  # each run_once raises
    fwd = Forwarder(logging.getLogger("test"), conn, FakeTelegram(), delete=True)

    calls = []

    def fake_sleep(interval):
        calls.append(interval)
        # Break out after the loop has run one full cycle.
        raise _StopLoop

    with patch("forwarder.time.sleep", side_effect=fake_sleep):
        try:
            fwd.run_loop(5)
        except _StopLoop:
            pass

    # The failing cycle was swallowed and the loop still reached the sleep call.
    assert calls == [5]
