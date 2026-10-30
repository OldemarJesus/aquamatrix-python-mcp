# Agent Guide

## Project intent

This repository provides an MCP adapter for the independent async Aquamatrix SIMAR SDK. Keep it typed, read-only, privacy-conscious, and independent from specific MCP hosts.

## Required practices

- Read `PRD.md` and `ARCH.md` before changing scope or architecture.
- Keep portal HTTP paths, HTML parsing, form fields, and response mapping inside the SDK dependency; do not duplicate portal protocol code here.
- Expose SDK operations as deterministic async MCP tools and test them with `httpx.MockTransport` or an injected fake. Never contact real accounts or the live portal in tests.
- Use typed models for MCP output. Preserve invoice amounts as decimal strings and dates as ISO calendar-date strings.
- Keep credentials in environment variables and out of tool arguments, output, logs, fixtures, and exception messages.
- Keep the server read-only. Do not add payments, account mutation, browser automation, CAPTCHA/MFA bypass, or credential persistence.
- Use the official MCP Python SDK and its current protocol transports. Prefer stdio for local hosts and Streamable HTTP for local HTTP clients; do not add legacy SSE.
- Bind HTTP to loopback by default and do not expose the unauthenticated billing server directly to an untrusted network.
- Keep Docker host port publishing on loopback; `MCP_ALLOW_NON_LOOPBACK=true` is only an explicit in-container bind override, not network authentication.
- Keep GitHub Pages and PyPI release workflows least-privileged; use PyPI trusted publishing/OIDC, never a committed or workflow-stored API token.
- Preserve async operation, explicit SDK client shutdown, TLS verification, and attribution to Oldemar Jesus (`oldemego@gmail.com`).

## Validation

Run the focused tests first, then the complete checks:

```shell
pytest
ruff check .
mypy src
mkdocs build --strict
```

Use the project's declared minimum Python version for syntax and typing decisions.

## Upstream uncertainty

Aquamatrix's portal endpoints are undocumented and may change. Keep protocol handling in the SDK, preserve its stable typed errors, and fail clearly if the upstream response changes.