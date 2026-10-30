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

### CLI environment variables / `.env` file

Every option can be supplied as an environment variable instead, using the `ZTE_` prefix
(e.g. `--password` becomes `ZTE_PASSWORD`). For local CLI usage, you can optionally copy
`.env.dist` to `.env` and fill it in:

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

### Deploy with Compose

Only `compose.yaml` is needed on the server. It pulls the published image and supplies
configuration through the service's `environment:` block—no `.env` file, source checkout,
volumes, or port mappings are required.

In your private deployment copy, set `ZTE_HOST` to the modem's IP address and fill in
`ZTE_PASSWORD`, `ZTE_BOT`, and `ZTE_CHAT`. The checked-in credentials are deliberately blank.
Adjust `ZTE_INTERVAL` and `ZTE_DELETE` there as needed; keep all values quoted as strings.
When editing credentials directly in Compose YAML, escape literal `$` characters as `$$`.
Keep the configured copy private: credentials are stored in the deployment configuration
and are visible to Docker administrators, not baked into the image.

```bash
docker compose pull
docker compose up -d
docker compose logs -f
```

The image supports Linux AMD64 and ARM64, runs as UID/GID `10001:10001`, and starts in loop
mode by default. Compose enables an init process and restarts the service unless stopped.
The container must be able to reach the modem's IP address and `api.telegram.org`.

For updates, repeat the `pull` and `up -d` commands above. Restart policies do not pull updates.

### Import into ZimaOS

Use [ZimaOS's custom-app Compose import](https://www.zimaspace.com/docs/zimaos/app-store/paperless-ai-install):

1. On the dashboard, choose **+ → Install a customized app → Import → Docker Compose**.
2. Paste `compose.yaml` and select **Submit**.
3. Set the modem address and credentials under **Environment Variables** before installing.

There is no web UI to expose and no folder to mount. Credentials are normal container
environment variables managed in ZimaOS; you do not need to upload a `.env` file.

### Build locally

```bash
docker build -t zte-to-telegram .
docker run --rm --network none --read-only zte-to-telegram --help
```

To deploy a local build, change the service's `image` in your private `compose.yaml` copy to
`zte-to-telegram`, then run `docker compose up -d` without pulling from GHCR.

### GitHub Actions publishing

`.github/workflows/docker-publish.yml` follows the native AMD64/ARM64 build and manifest-merge
pattern from the sibling big-AGI project. Each architecture's installed CLI is smoke-checked
before publication. Pull requests build and check both architectures without publishing.
Images are pushed to `ghcr.io/<owner>/<repository>` (lowercase) using `GITHUB_TOKEN`:

- Pushes to `main` publish `latest`, `main`, and `sha-<short-commit>` tags.
- Git tags publish the tag name and `sha-<short-commit>`; they do not move `latest`.
- **Actions → Build and publish Docker image → Run workflow** publishes the selected ref.

The workflow retains build caches per architecture and attests the combined image digest.
No registry password secret is needed. Repository or organization policy must allow the
workflow's package-write and attestation permissions. After the first publish, set the GHCR
package visibility to **Public** for unauthenticated pulls. For a private package, run
`docker login ghcr.io` with a token that has `read:packages` access before pulling.

Publishing does not restart containers on a deployment host; use the update procedure above.

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
