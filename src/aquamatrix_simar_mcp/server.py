"""MCP tools backed by the public Aquamatrix SIMAR SDK API."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Protocol, TypedDict

from aquamatrix_simar import Invoice, SimarClient
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from aquamatrix_simar_mcp.config import Settings


class SimarApi(Protocol):
    """Public async operations required from the SDK client."""

    async def login(self) -> None: ...

    async def get_invoices(
        self,
        *,
        start: int = 0,
        limit: int = 100,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Invoice]: ...

    async def get_pending_invoices(self) -> list[Invoice]: ...

    async def get_billing_summary(self) -> dict[str, int]: ...

    async def aclose(self) -> None: ...


class SimarClientFactory(Protocol):
    """Construct the SDK client; injectable for deterministic tests."""

    def __call__(self, nif: str, password: str, *, base_url: str) -> SimarApi: ...


@dataclass(frozen=True, slots=True)
class AppContext:
    """Authenticated SDK client shared by tools for one server lifecycle."""

    simar: SimarApi


@dataclass(frozen=True, slots=True)
class InvoiceOutput:
    """JSON-safe invoice representation that preserves decimal precision."""

    document_number: str
    document_type: str
    year: int
    issue_date: str
    payment_until: str
    amount: str
    state: str
    payment_date: str | None
    client_code: str | None
    is_pending: bool


class BillingSummaryOutput(TypedDict):
    """Invoice counts returned by the SIMAR portal."""

    invoices_to_pay: int
    failed_invoices: int


def _to_invoice_output(invoice: Invoice) -> InvoiceOutput:
    return InvoiceOutput(
        document_number=invoice.document_number,
        document_type=invoice.document_type,
        year=invoice.year,
        issue_date=invoice.issue_date.isoformat(),
        payment_until=invoice.payment_until.isoformat(),
        amount=str(invoice.amount),
        state=invoice.state,
        payment_date=invoice.payment_date.isoformat() if invoice.payment_date else None,
        client_code=invoice.client_code,
        is_pending=invoice.is_pending,
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
        version="0.1.0",
        instructions=(
            "Read-only access to SIMAR invoice history, pending invoices, and billing summary. "
            "Amounts are decimal strings and dates are ISO calendar dates."
        ),
        lifespan=lifespan,
    )
    read_only = ToolAnnotations(read_only_hint=True, destructive_hint=False)

    @server.tool(
        title="Get invoice history",
        annotations=read_only,
    )
    async def get_invoices(
        start: Annotated[
            int,
            Field(ge=0, description="Zero-based offset into invoice history."),
        ] = 0,
        limit: Annotated[
            int,
            Field(ge=1, le=500, description="Maximum number of invoices."),
        ] = 100,
        date_from: Annotated[date | None, Field(description="Inclusive start date (YYYY-MM-DD).")]
        = None,
        date_to: Annotated[date | None, Field(description="Inclusive end date (YYYY-MM-DD).")]
        = None,
        ctx: Context[AppContext] | None = None,
    ) -> list[InvoiceOutput]:
        """Fetch a page of invoices, optionally filtered by an inclusive date range."""
        if date_from is not None and date_to is not None and date_from > date_to:
            raise ToolError("date_from must be on or before date_to")
        try:
            simar = _context(ctx).simar
            invoices = await simar.get_invoices(
                start=start,
                limit=limit,
                date_from=date_from,
                date_to=date_to,
            )
            return [_to_invoice_output(invoice) for invoice in invoices]
        except ToolError:
            raise
        except Exception:
            raise ToolError("Could not retrieve invoice history") from None

    @server.tool(
        title="Get pending invoices",
        annotations=read_only,
    )
    async def get_pending_invoices(ctx: Context[AppContext] | None = None) -> list[InvoiceOutput]:
        """Return invoices the SDK recognizes as unpaid."""
        try:
            invoices = await _context(ctx).simar.get_pending_invoices()
            return [_to_invoice_output(invoice) for invoice in invoices]
        except Exception:
            raise ToolError("Could not retrieve pending invoices") from None

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

    return server


def _context(context: Context[AppContext] | None) -> AppContext:
    if context is None:
        raise RuntimeError("MCP request context is unavailable")
    return context.request_context.lifespan_context