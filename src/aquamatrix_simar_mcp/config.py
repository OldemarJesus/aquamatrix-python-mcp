"""Environment-backed server settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Literal, cast
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings without exposing credentials as MCP inputs."""

    nif: str
    password: str
    base_url: str
    transport: Literal["stdio", "streamable-http"]
    host: str
    port: int

    @classmethod
    def from_env(cls) -> Settings:
        """Read and validate configuration from the server process environment."""
        nif = os.environ.get("SIMAR_NIF", "").strip()
        password = os.environ.get("SIMAR_PASSWORD", "")
        if not nif or not password:
            raise RuntimeError("Set SIMAR_NIF and SIMAR_PASSWORD in the MCP server environment")

        base_url = os.environ.get("SIMAR_BASE_URL", "https://www.aquamatrix.pt").rstrip("/")
        parsed_url = urlsplit(base_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise RuntimeError("SIMAR_BASE_URL must be an absolute HTTPS URL")

        transport = os.environ.get("MCP_TRANSPORT", "stdio")
        if transport not in {"stdio", "streamable-http"}:
            raise RuntimeError("MCP_TRANSPORT must be 'stdio' or 'streamable-http'")
        transport = cast(Literal["stdio", "streamable-http"], transport)

        host = os.environ.get("MCP_HOST", "127.0.0.1")
        allow_non_loopback = os.environ.get("MCP_ALLOW_NON_LOOPBACK", "false").casefold()
        if allow_non_loopback not in {"true", "false"}:
            raise RuntimeError("MCP_ALLOW_NON_LOOPBACK must be 'true' or 'false'")
        if not _is_loopback(host) and allow_non_loopback != "true":
            raise RuntimeError(
                "MCP_HOST must be a loopback address unless MCP_ALLOW_NON_LOOPBACK=true"
            )

        try:
            port = int(os.environ.get("MCP_PORT", "8000"))
        except ValueError as exc:
            raise RuntimeError("MCP_PORT must be an integer between 1 and 65535") from exc
        if not 1 <= port <= 65535:
            raise RuntimeError("MCP_PORT must be an integer between 1 and 65535")

        return cls(
            nif=nif,
            password=password,
            base_url=base_url,
            transport=transport,
            host=host,
            port=port,
        )


def _is_loopback(host: str) -> bool:
    if host.casefold() == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False