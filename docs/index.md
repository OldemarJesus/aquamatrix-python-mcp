# Aquamatrix SIMAR MCP Server

An async Model Context Protocol server for reading billing information from the SIMAR customer portal through the independent [Aquamatrix SIMAR Python SDK](https://github.com/OldemarJesus/aquamatrix-python-sdk).

The server is unofficial, read-only, and not affiliated with SIMAR or Aquamatrix.

## Tools

- `get_billing_summary`: retrieve the portal's invoice-to-pay and failed-invoice counts.
- `get_last_reading` and `get_next_readings`: retrieve latest and scheduled meter-reading details.
- `get_water_shortages`: retrieve the portal's water-shortage status.
- `get_last_invoice_graph` and `get_billed_values_graph`: retrieve billing graph values.

Invoice history and pending-invoice tools are omitted while the SDK temporarily disables those operations.

Money values are decimal strings and calendar dates use ISO `YYYY-MM-DD` format. Credentials are configured through the server environment, not exposed as tool inputs.

## Start here

- [Install and configure](guide/installation.md)
- [Explore tools and transports](guide/tools.md)
- [Run with Docker Compose](guide/docker.md)
- [Review security guidance](guide/security.md)

## Project

- [Product requirements](https://github.com/OldemarJesus/aquamatrix-python-mcp/blob/main/PRD.md)
- [Architecture](https://github.com/OldemarJesus/aquamatrix-python-mcp/blob/main/ARCH.md)
- [MIT License](https://github.com/OldemarJesus/aquamatrix-python-mcp/blob/main/LICENSE)
- [Release and publishing](guide/releasing.md)