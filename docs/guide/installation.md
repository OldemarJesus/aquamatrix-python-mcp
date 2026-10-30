# Installation and Configuration

## Requirements

- Python 3.14 or newer.
- An authorized SIMAR portal account.

Install from PyPI:

```shell
python -m pip install aquamatrix-simar-mcp
```

Provide credentials to the server process using environment variables:

```shell
export SIMAR_NIF='your-nif'
export SIMAR_PASSWORD='your-password'
aquamatrix-simar-mcp
```

The server does not persist credentials. Keep them out of source files, shell history where possible, tool arguments, logs, and issue reports. For managed deployment, use the platform's secret/environment facility.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `SIMAR_NIF` | Required | SIMAR account NIF |
| `SIMAR_PASSWORD` | Required | SIMAR account password |
| `SIMAR_BASE_URL` | `https://www.aquamatrix.pt` | HTTPS base URL for the portal |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HOST` | `127.0.0.1` | HTTP bind address; loopback by default |
| `MCP_ALLOW_NON_LOOPBACK` | `false` | Explicitly allows non-loopback binding |
| `MCP_PORT` | `8000` | HTTP port, from 1 to 65535 |

`MCP_ALLOW_NON_LOOPBACK=true` disables the loopback bind guard. It is intended for container network namespaces and is not an authentication mechanism. Keep the host-side port private, or provide a separately reviewed authenticated and encrypted proxy before remote access.