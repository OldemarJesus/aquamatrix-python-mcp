# Docker Compose

The supplied `Dockerfile` builds a small Python 3.14 image, installs the published package metadata from the local source tree, runs as a non-root user, and starts the server using Streamable HTTP. The Compose file binds the application inside its container network but publishes the host port only on `127.0.0.1`.

## Start

Pass credentials via environment variables:

```shell
export SIMAR_NIF='your-nif'
export SIMAR_PASSWORD='your-password'
docker compose up --build -d
```

Alternatively, create a local `.env` file (ignored by `.dockerignore` and `.gitignore`) and restrict its filesystem permissions. Never commit it:

```dotenv
SIMAR_NIF=your-nif
SIMAR_PASSWORD=your-password
SIMAR_BASE_URL=https://www.aquamatrix.pt
MCP_PORT=8000
```

Then run:

```shell
docker compose up --build -d
docker compose logs --follow
```

The endpoint is `http://127.0.0.1:8000/mcp`. Stop the service with `docker compose down`.

## Environment variables

Compose reads `SIMAR_NIF` and `SIMAR_PASSWORD` as required variables. `SIMAR_BASE_URL` and `MCP_PORT` may be set in the shell or `.env`; the remaining HTTP settings are declared by Compose for container networking.

The container sets `MCP_ALLOW_NON_LOOPBACK=true` because its HTTP server must listen on the container interface. This opt-in is paired with host-only loopback port publishing. Do not change the published address to `0.0.0.0` or expose the container port to an untrusted network: this service has no HTTP authentication.

For production deployment, prefer your orchestrator's secret manager over a checked-in or broadly readable `.env` file.