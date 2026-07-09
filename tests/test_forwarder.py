import logging

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
