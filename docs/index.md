# Aquamatrix SIMAR MCP Server

An async Model Context Protocol server for reading billing information from the SIMAR customer portal through the independent [Aquamatrix SIMAR Python SDK](https://github.com/OldemarJesus/aquamatrix-python-sdk).

The server is unofficial, read-only, and not affiliated with SIMAR or Aquamatrix.

## Tools

- `get_invoices`: retrieve one page of invoice history with optional date filters.
- `get_pending_invoices`: retrieve invoices the SDK recognizes as unpaid.
- `get_billing_summary`: retrieve the portal's invoice-to-pay and failed-invoice counts.

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