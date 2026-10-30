# TL;DR PRD: Aquamatrix SIMAR MCP Server

## Product

An async MCP server that makes the read-only billing capabilities of the independent `aquamatrix-simar` Python SDK available to MCP hosts using structured tools and current protocol transports.

## Users and problem

SIMAR account holders and maintainers of AI-enabled integrations need a standard, host-independent way to retrieve their invoice history, pending invoices, and billing summary without duplicating portal authentication or HTML/form handling.

## MVP outcomes

- Authenticate once per server lifecycle using `SIMAR_NIF` and `SIMAR_PASSWORD` environment variables.
- Expose invoice history, pending invoices, and billing summary as read-only MCP tools.
- Preserve typed outputs, money precision, and ISO date semantics in structured tool results.
- Support stdio for local MCP hosts and Streamable HTTP for local HTTP clients.
- Include deterministic offline tests for MCP tool calls and SDK protocol behavior.

## Out of scope

- Initiating payments or mutating customer/account data.
- Exposing credentials as tool parameters or storing them persistently.
- Browser automation, CAPTCHA/MFA bypass, or direct implementation of the portal protocol.
- Public unauthenticated network hosting or a host-specific configuration bundle.

## Constraints and success criteria

- Python 3.14+, asyncio, the official MCP Python SDK, and `aquamatrix-simar`.
- The SDK owns portal requests, cookies, anti-forgery tokens, response mapping, and stable exceptions.
- Tests use synthetic data and mocks only; no live credentials or personal information are committed.
- MIT project authored by Oldemar Jesus.

## Risks

The upstream portal is undocumented and may change. The MCP endpoint can reveal billing data to any connected client, so Streamable HTTP must remain on loopback unless a separately reviewed authentication and network boundary is provided.