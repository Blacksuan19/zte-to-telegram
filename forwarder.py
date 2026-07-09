import time
from logging import Logger

from sms.parser import parse_sms


class Forwarder:
    """Reads SMS from the modem and forwards each to Telegram."""

    __logger: Logger

    def __init__(self, logger: Logger, connection, telegram, delete: bool):
        self.__logger = logger
        self.__connection = connection
        self.__telegram = telegram
        self.__delete = delete

    def run_once(self) -> int:
        """Read pending SMS once and forward them. Returns the count forwarded."""

        self.__connection.login()
        try:
            messages = self.__connection.read_all_sms(self.__delete)
        finally:
            self.__connection.logout()

        for message in messages:
            self.__telegram.send_message(parse_sms(message))

        self.__logger.info("Forwarded %d SMS", len(messages))
        return len(messages)

    def run_loop(self, interval: int) -> None:
        """Run ``run_once`` forever, sleeping ``interval`` seconds between cycles."""

        self.__logger.info("Starting loop mode (interval=%ds)", interval)
        while True:
            try:
                self.run_once()
            except Exception as e:
                self.__logger.error("Forward cycle failed: %s", e, exc_info=True)
            time.sleep(interval)
