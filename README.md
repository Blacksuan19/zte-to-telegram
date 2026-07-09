[![CI](https://github.com/Toshik1978/zte-to-telegram/actions/workflows/ci.yml/badge.svg)](https://github.com/Toshik1978/zte-to-telegram/actions)
![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Toshik1978/054d287f6fd9c1cf605957177c7106b2/raw/tests.json&maxAge=180)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Toshik1978/054d287f6fd9c1cf605957177c7106b2/raw/coverage.json&maxAge=180)

# ZTE MC888 → Telegram SMS forwarder

A small CLI that logs in to a ZTE MC888 5G modem/router, reads pending SMS messages, and
forwards each one to a Telegram chat via a bot — running once (e.g. from cron) or continuously
as a daemon.

## Install

```bash
uv sync
```

## Usage

Run once, passing everything on the command line:

```bash
uv run zte-to-telegram --password <modem-password> --bot <telegram-bot-token> --chat <telegram-chat-id>
```

### Environment variables / `.env` file

Every option can be supplied as an environment variable instead, using the `ZTE_` prefix
(e.g. `--password` becomes `ZTE_PASSWORD`). Copy `.env.dist` to `.env` and fill it in:

```bash
cp .env.dist .env
```

```dotenv
# ZTE MC888 modem
ZTE_HOST=192.168.0.1
ZTE_PASSWORD=

# Telegram
ZTE_BOT=
ZTE_CHAT=
```

`.env` is loaded automatically, so once it's filled in you can just run:

```bash
uv run zte-to-telegram
```

### Marking messages read instead of deleting

By default, forwarded SMS are deleted from the modem. Use `--mark-read` (or `ZTE_DELETE=false`)
to leave them on the device, marked as read, instead:

```bash
uv run zte-to-telegram --mark-read
```

### Loop (daemon) mode

Pass `--loop` to keep running, polling the modem on an interval (seconds, default `60`):

```bash
uv run zte-to-telegram --loop --interval 60
```

### Running one-shot from cron

If you'd rather not run a daemon, schedule the one-shot command instead, e.g. every minute:

```cron
* * * * * cd /path/to/zte-to-telegram && uv run zte-to-telegram
```

## Docker

Build the image:

```bash
docker build -t zte-to-telegram .
```

Run it, supplying configuration via an env file (never bake secrets into the image):

```bash
docker run --env-file .env zte-to-telegram
```

The container's default command runs in loop mode (`zte-to-telegram --loop`), so it keeps
polling and forwarding SMS for as long as it runs.

## Configuration

| CLI flag             | Environment variable | Default       | Description                               |
|-----------------------|-----------------------|---------------|-------------------------------------------|
| `--host`              | `ZTE_HOST`            | `192.168.0.1` | IP address of the ZTE MC888 modem         |
| `--password`          | `ZTE_PASSWORD`        | *(required)*  | Password for the ZTE MC888 modem          |
| `--bot`               | `ZTE_BOT`              | *(required)*  | Telegram bot token                        |
| `--chat`              | `ZTE_CHAT`             | *(required)*  | Telegram chat id                          |
| `--delete/--mark-read` | `ZTE_DELETE`          | `--delete`    | Delete SMS after forwarding, or mark read |
| `--loop`              | `ZTE_LOOP`             | off           | Run continuously, polling on an interval  |
| `--interval`          | `ZTE_INTERVAL`         | `60`          | Seconds between polls (loop mode only)    |
| `-v`                  | —                      | off           | Verbose (debug) logging                   |

## Special thanks

The modem login/session logic is based on https://github.com/teixeluis/zte-lte-modem/.
