# Aquamatrix SIMAR MCP Server

An async Model Context Protocol server exposing the read-only billing features of the [Aquamatrix SIMAR Python SDK](https://github.com/OldemarJesus/aquamatrix-python-sdk). Unofficial and not affiliated with SIMAR or Aquamatrix.

## Tools

- `get_billing_summary`: return the portal's invoice-to-pay and failed-invoice counts.
- `get_last_reading` and `get_next_readings`: return latest and scheduled meter-reading details.
- `get_water_shortages`: report the portal's water-shortage status.
- `get_last_invoice_graph` and `get_billed_values_graph`: return typed billing graph values.

Invoice history and pending-invoice tools are omitted because the SDK temporarily disables those operations while the portal's history request is investigated.

All tools are read-only. Invoice amounts are returned as decimal strings; dates use ISO `YYYY-MM-DD` strings. Credentials are supplied only through the server process environment, never through tool calls.

## Requirements and installation

- Python 3.14 or newer.
- A SIMAR portal account.

```shell
python -m pip install aquamatrix-simar-mcp
```

Set `SIMAR_NIF` and `SIMAR_PASSWORD` in the MCP server process environment. Optionally set `SIMAR_BASE_URL` when using a compatible portal host.

## Docker Compose

The Compose example runs Streamable HTTP inside a container and publishes it only on host loopback. Set credentials in the process environment or an ignored `.env` file; do not commit secrets.

```shell
export SIMAR_NIF='your-nif'
export SIMAR_PASSWORD='your-password'
docker compose up --build -d
```

The MCP endpoint is `http://127.0.0.1:8000/mcp`. Set `MCP_PORT` to change the port. The container opts into `0.0.0.0` only within its network namespace; Docker's host-side port binding remains `127.0.0.1`. See the [container guide](docs/guide/docker.md) before changing the network exposure.

## Run

For local MCP hosts, use stdio:

```shell
aquamatrix-simar-mcp
```

For a local HTTP client, use current Streamable HTTP:

```shell
MCP_TRANSPORT=streamable-http aquamatrix-simar-mcp
```

The HTTP server binds to `127.0.0.1:8000` by default. It has no HTTP authentication; do not expose it directly to an untrusted network. SSE is intentionally not provided because Streamable HTTP is the current standard transport.

Configuration:

| Variable | Default | Description |
| --- | --- | --- |
| `SIMAR_NIF` | Required | SIMAR account NIF |
| `SIMAR_PASSWORD` | Required | SIMAR account password |
| `SIMAR_BASE_URL` | `https://www.aquamatrix.pt` | Portal base URL |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HOST` | `127.0.0.1` | HTTP bind address; loopback only |
| `MCP_ALLOW_NON_LOOPBACK` | `false` | Explicit opt-in to a non-loopback bind, intended for container networking |
| `MCP_PORT` | `8000` | HTTP port |

## Development

```shell
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy src
```

See [PRD.md](PRD.md), [ARCH.md](ARCH.md), and [AGENTS.md](AGENTS.md) for scope, design, and contributor requirements.

## Documentation

The [documentation site](https://oldemarjesus.github.io/aquamatrix-python-mcp/) includes installation, Docker Compose, security, and publishing guidance. GitHub Pages is built and deployed by GitHub Actions.

## Author and license

Copyright (c) 2026 Oldemar Jesus <oldemego@gmail.com>. MIT licensed; see [LICENSE](LICENSE).