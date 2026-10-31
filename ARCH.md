# Architecture

## Boundary

`aquamatrix-simar` is the only component that communicates with the Aquamatrix portal. This project translates its public async API into MCP tools and structured JSON-compatible outputs.

```text
MCP host
   |
stdio or Streamable HTTP
   |
MCPServer -- typed tools and lifespan
   |
SimarClient -- authentication, HTTP, mapping, SDK errors
   |
Aquamatrix SIMAR portal
```

## Modules

- `server.py`: typed MCP output models, server factory, lifecycle, and SDK-backed tools.
- `config.py`: environment-backed credentials and transport configuration.
- `__main__.py`: executable entry point.
- `tests/`: in-memory MCP calls with a mock HTTP transport.

## Lifecycle and request flow

1. The MCP server starts and reads `SIMAR_NIF`, `SIMAR_PASSWORD`, and optional `SIMAR_BASE_URL` from its environment.
2. Its lifespan creates one `SimarClient`, calls `login()`, and yields the authenticated client as typed request context.
3. Tools call only public SDK methods: billing summary, latest reading, next reading dates, water-shortage status, latest-invoice graph, and billed-values graph. Invoice history and pending invoices are not exposed while the SDK disables those operations.
4. Graph amounts are serialized as decimal strings, while calendar dates are ISO-8601 strings, avoiding floating-point loss and timezone ambiguity.
5. Shutdown closes the SDK client in a `finally` block.

Credentials are never MCP tool arguments. SDK errors are returned as tool errors without adding account details or request/response content.

## Transports and security

- stdio is the default and is intended for a local MCP host.
- Streamable HTTP is available for local clients and binds to loopback by default.
- No HTTP authentication is implemented. Do not expose the server directly to an untrusted network; remote deployment requires a separately reviewed authentication, TLS, and access-control boundary.
- `MCP_ALLOW_NON_LOOPBACK=true` explicitly opts into container-interface binding; container examples must publish to host loopback unless an authenticated gateway is separately configured.
- TLS verification remains enabled in the SDK. The server is read-only and does not persist credentials or session cookies.

## Evolution

Expose new SDK capabilities as typed read-only tools only when they exist in the public SDK API. Keep portal-specific behavior in the SDK and update deterministic tests whenever the adapter contract changes.