# Tools and Transports

## Read-only tools

### `get_invoices`

Returns one page of invoices. `start` is a zero-based offset (`0` by default), and `limit` is between 1 and 500 (`100` by default). Optional `date_from` and `date_to` values use `YYYY-MM-DD` and are inclusive. A reversed date range is rejected.

Invoice output includes document number/type, year, issue and payment dates, exact amount as a decimal string, portal state, payment date, client code when available, and the SDK's pending classification.

### `get_pending_invoices`

Returns invoices the SDK classifies as pending. The SDK owns the portal-state mapping and payment-status logic.

### `get_billing_summary`

Returns `invoices_to_pay` and `failed_invoices` counts.

All three tools are annotated as read-only. No tool accepts credentials or performs account mutations or payments.

## stdio

stdio is the default for local MCP hosts that launch the server as a subprocess:

```shell
aquamatrix-simar-mcp
```

The host must provide `SIMAR_NIF` and `SIMAR_PASSWORD` in the server process environment. Do not print diagnostics to stdout; stdio carries MCP protocol messages.

## Streamable HTTP

For an HTTP MCP client, run:

```shell
MCP_TRANSPORT=streamable-http aquamatrix-simar-mcp
```

The endpoint defaults to `http://127.0.0.1:8000/mcp`. HTTP has no server authentication, so loopback is the supported default. SSE is not provided; Streamable HTTP is the current standard transport.