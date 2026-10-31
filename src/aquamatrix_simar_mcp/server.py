"""MCP tools backed by the public Aquamatrix SIMAR SDK API."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Protocol, TypedDict

from aquamatrix_simar import (
    GraphValue,
    NextReadingsInfo,
    ReadingInfo,
    SimarClient,
)
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from aquamatrix_simar_mcp.config import Settings


class SimarApi(Protocol):
    """Public async operations required from the SDK client."""

    async def login(self) -> None: ...

    async def get_billing_summary(self) -> dict[str, int]: ...

    async def get_last_reading(self) -> ReadingInfo: ...

    async def get_next_readings(self) -> NextReadingsInfo: ...

    async def get_water_shortages(self) -> bool: ...

    async def get_last_invoice_graph(self) -> list[GraphValue]: ...

    async def get_billed_values_graph(self) -> list[GraphValue]: ...

    async def aclose(self) -> None: ...


class SimarClientFactory(Protocol):
    """Construct the SDK client; injectable for deterministic tests."""

    def __call__(self, nif: str, password: str, *, base_url: str) -> SimarApi: ...


@dataclass(frozen=True, slots=True)
class AppContext:
    """Authenticated SDK client shared by tools for one server lifecycle."""

    simar: SimarApi


class ReadingOutput(TypedDict):
    """JSON-safe latest meter-reading details."""

    reading_date: str
    reading_type: str
    value: str


class NextReadingsOutput(TypedDict):
    """JSON-safe scheduled reading dates."""

    company_date: str
    client_date: str


class GraphValueOutput(TypedDict):
    """JSON-safe graph value that preserves decimal precision."""

    label: str
    value: str
    value_display: str | None


class BillingSummaryOutput(TypedDict):
    """Invoice counts returned by the SIMAR portal."""

    invoices_to_pay: int
    failed_invoices: int


def _to_reading_output(reading: ReadingInfo) -> ReadingOutput:
    return ReadingOutput(
        reading_date=reading.reading_date.isoformat(),
        reading_type=reading.reading_type,
        value=reading.value,
    )


def _to_next_readings_output(readings: NextReadingsInfo) -> NextReadingsOutput:
    return NextReadingsOutput(
        company_date=readings.company_date.isoformat(),
        client_date=readings.client_date.isoformat(),
    )


def _to_graph_value_output(value: GraphValue) -> GraphValueOutput:
    return GraphValueOutput(
        label=value.label,
        value=str(value.value),
        value_display=value.value_display,
    )


def create_server(
    *,
    client_factory: SimarClientFactory = SimarClient,
    settings_factory: Callable[[], Settings] = Settings.from_env,
) -> MCPServer[AppContext]:
    """Create an MCP server with a lifecycle-owned authenticated SDK client."""

    @asynccontextmanager
    async def lifespan(_: MCPServer[AppContext]) -> AsyncGenerator[AppContext]:
        settings = settings_factory()
        simar = client_factory(settings.nif, settings.password, base_url=settings.base_url)
        try:
            try:
                await simar.login()
            except Exception:
                raise RuntimeError(
                    "SIMAR authentication failed; check configuration and availability"
                ) from None
            yield AppContext(simar=simar)
        finally:
            try:
                await simar.aclose()
            except Exception:
                raise RuntimeError("Could not close the SIMAR client cleanly") from None

    server = MCPServer(
        "Aquamatrix SIMAR",
        version="0.2.0",
        instructions=(
            "Read-only access to SIMAR billing summary, meter readings, water-shortage status, "
            "and billing graphs. Graph amounts are decimal strings and dates are "
            "ISO calendar dates. "
            "Invoice history is currently unavailable."
        ),
        lifespan=lifespan,
    )
    read_only = ToolAnnotations(read_only_hint=True, destructive_hint=False)

    @server.tool(
        title="Get billing summary",
        annotations=read_only,
    )
    async def get_billing_summary(
        ctx: Context[AppContext] | None = None,
    ) -> BillingSummaryOutput:
        """Return SIMAR's counts of invoices to pay and failed invoices."""
        try:
            summary = await _context(ctx).simar.get_billing_summary()
        except Exception:
            raise ToolError("Could not retrieve billing summary") from None
        return BillingSummaryOutput(
            invoices_to_pay=summary["invoices_to_pay"],
            failed_invoices=summary["failed_invoices"],
        )

    @server.tool(title="Get last reading", annotations=read_only)
    async def get_last_reading(ctx: Context[AppContext] | None = None) -> ReadingOutput:
        """Return the latest meter reading reported by SIMAR."""
        try:
            reading = await _context(ctx).simar.get_last_reading()
        except Exception:
            raise ToolError("Could not retrieve the latest reading") from None
        return _to_reading_output(reading)

    @server.tool(title="Get next readings", annotations=read_only)
    async def get_next_readings(ctx: Context[AppContext] | None = None) -> NextReadingsOutput:
        """Return the scheduled company and customer reading dates."""
        try:
            readings = await _context(ctx).simar.get_next_readings()
        except Exception:
            raise ToolError("Could not retrieve the next reading dates") from None
        return _to_next_readings_output(readings)

    @server.tool(title="Get water-shortage status", annotations=read_only)
    async def get_water_shortages(ctx: Context[AppContext] | None = None) -> bool:
        """Return whether SIMAR reports a water shortage."""
        try:
            return await _context(ctx).simar.get_water_shortages()
        except Exception:
            raise ToolError("Could not retrieve water-shortage status") from None

    @server.tool(title="Get latest invoice graph", annotations=read_only)
    async def get_last_invoice_graph(
        ctx: Context[AppContext] | None = None,
    ) -> list[GraphValueOutput]:
        """Return the component values in the latest invoice graph."""
        try:
            values = await _context(ctx).simar.get_last_invoice_graph()
        except Exception:
            raise ToolError("Could not retrieve the latest invoice graph") from None
        return [_to_graph_value_output(value) for value in values]

    @server.tool(title="Get billed-values graph", annotations=read_only)
    async def get_billed_values_graph(
        ctx: Context[AppContext] | None = None,
    ) -> list[GraphValueOutput]:
        """Return historical billed values from SIMAR's graph."""
        try:
            values = await _context(ctx).simar.get_billed_values_graph()
        except Exception:
            raise ToolError("Could not retrieve the billed-values graph") from None
        return [_to_graph_value_output(value) for value in values]

    return server


def _context(context: Context[AppContext] | None) -> AppContext:
    if context is None:
        raise RuntimeError("MCP request context is unavailable")
    return context.request_context.lifespan_context