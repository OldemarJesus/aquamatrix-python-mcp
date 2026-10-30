"""Command-line entry point."""

from aquamatrix_simar_mcp.config import Settings
from aquamatrix_simar_mcp.server import create_server


def main() -> None:
    """Run the configured MCP transport."""
    settings = Settings.from_env()
    server = create_server(settings_factory=lambda: settings)
    if settings.transport == "stdio":
        server.run()
    else:
        server.run(
            transport="streamable-http",
            host=settings.host,
            port=settings.port,
        )


if __name__ == "__main__":
    main()