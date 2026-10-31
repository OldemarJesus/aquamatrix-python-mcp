# Tools and Transports

## Read-only tools

### `get_billing_summary`

Returns `invoices_to_pay` and `failed_invoices` counts.

### `get_last_reading` and `get_next_readings`

Return the latest meter reading, or the scheduled company and customer reading dates. Dates use ISO `YYYY-MM-DD` strings.

### `get_water_shortages`

Returns whether the portal reports a water shortage.

### `get_last_invoice_graph` and `get_billed_values_graph`

Return labeled graph values. Amounts are decimal strings to preserve precision; the portal's display string is included when available.

Invoice history and pending-invoice tools are not exposed because the SDK temporarily disables those operations while the portal history request is investigated. All available tools are annotated as read-only; no tool accepts credentials or performs account mutations or payments.

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