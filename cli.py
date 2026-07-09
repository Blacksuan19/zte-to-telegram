import logging
import sys

import click
from dotenv import load_dotenv

from forwarder import Forwarder
from telegram.client import TelegramClient
from zte.connection import ZteConnection
from zte.exception import ZteModemException


@click.command()
@click.option("--host", default="192.168.0.1", help="IP address of the ZTE MC888")
@click.option("--password", required=True, help="Password for the ZTE MC888")
@click.option("--bot", required=True, help="Telegram bot token")
@click.option("--chat", required=True, help="Telegram chat id")
@click.option("--delete/--mark-read", default=True, help="Delete SMS after forwarding (default) or mark them read")
@click.option("--loop", is_flag=True, default=False, help="Run continuously, polling on an interval")
@click.option("--interval", default=60, type=int, help="Seconds between polls in loop mode")
@click.option("-v", is_flag=True, default=False, help="Verbose logging")
def cli(host, password, bot, chat, delete, loop, interval, v):
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG if v else logging.INFO)
    logger = logging.getLogger(__name__)

    connection = ZteConnection(logger, host, password)
    telegram = TelegramClient(logger, bot, chat)
    forwarder = Forwarder(logger, connection, telegram, delete)

    if loop:
        forwarder.run_loop(interval)
        return

    try:
        forwarder.run_once()
    except ZteModemException as e:
        logger.error("Failed to process SMS: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to process SMS: %s", e, exc_info=True)
        sys.exit(2)


def main() -> None:
    """Console-script entry point."""

    load_dotenv()
    cli(auto_envvar_prefix="ZTE")


if __name__ == "__main__":
    main()
