from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import parse_qs

import httpx
import pytest
from aquamatrix_simar import Invoice, SimarClient
from mcp import Client
from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent

from aquamatrix_simar_mcp.config import Settings
from aquamatrix_simar_mcp.server import AppContext, create_server

LOGIN_PAGE = '<input name="__RequestVerificationToken" value="login-token">'
BILLING_PAGE = '<input name="__RequestVerificationToken" value="billing-token">'
INVOICE_ROW = {
    "ClientCode": "fixture-client",
    "DocumentTypeDisplay": "Fatura",
    "DocumentNumber": "fixture-invoice",
    "Year": 2026,
    "IssueDateDisplay": "2026-10-22",
    "PaymentUntilDisplay": "2026-11-11",
    "Value": 10.39,
    "StateDisplay": "Em Cobrança",
    "PaymentDate": None,
}


@pytest.fixture
def settings() -> Settings:
    return Settings(
        nif="synthetic-nif",
        password="synthetic-password",
        base_url="https://portal.invalid",
        transport="stdio",
        host="127.0.0.1",
        port=8000,
    )


def test_settings_reject_non_loopback_bind_without_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMAR_NIF", "synthetic-nif")
    monkeypatch.setenv("SIMAR_PASSWORD", "synthetic-password")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.delenv("MCP_ALLOW_NON_LOOPBACK", raising=False)

    with pytest.raises(RuntimeError, match="MCP_ALLOW_NON_LOOPBACK=true"):
        Settings.from_env()


def test_settings_allow_container_bind_with_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMAR_NIF", "synthetic-nif")
    monkeypatch.setenv("SIMAR_PASSWORD", "synthetic-password")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_ALLOW_NON_LOOPBACK", "true")

    assert Settings.from_env().host == "0.0.0.0"


@pytest.fixture
async def server_and_requests(
    settings: Settings,
) -> AsyncIterator[tuple[MCPServer[AppContext], list[httpx.Request]]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/Account/Login") and request.method == "GET":
            return httpx.Response(200, text=LOGIN_PAGE)
        if request.url.path.endswith("/Account/Login") and request.method == "POST":
            fields = parse_qs(request.content.decode())
            assert fields["UserCode"] == ["synthetic-nif"]
            assert fields["Password"] == ["synthetic-password"]
            return httpx.Response(302, headers={"Location": "/SIMARnet/"})
        if request.url.path.endswith("/Billing"):
            return httpx.Response(200, text=BILLING_PAGE)
        if request.url.path.endswith("GetInvoicesHistory"):
            fields = parse_qs(request.content.decode())
            assert fields["start"] == ["5"] or fields["start"] == ["0"]
            if fields["start"] == ["5"]:
                assert fields["length"] == ["10"]
                assert fields["dateFrom"] == ["2026-01-01"]
                assert fields["dateTo"] == ["2026-12-31"]
            return httpx.Response(200, json={"data": [INVOICE_ROW]})
        if request.url.path.endswith("GetBillingInfo"):
            return httpx.Response(
                200,
                json={"InvoicesToPay": 1, "FailedInvoices": 2},
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.url.path}")

    def client_factory(nif: str, password: str, *, base_url: str) -> SimarClient:
        return SimarClient(
            nif,
            password,
            base_url=base_url,
            transport=httpx.MockTransport(handler),
        )

    server = create_server(
        client_factory=client_factory,
        settings_factory=lambda: settings,
    )
    yield server, requests


@pytest.mark.asyncio
async def test_tools_expose_sdk_data_as_structured_output(
    server_and_requests: tuple[MCPServer[AppContext], list[httpx.Request]],
) -> None:
    server, requests = server_and_requests
    async with Client(server, raise_exceptions=True) as client:
        invoices = await client.call_tool(
            "get_invoices",
            {
                "start": 5,
                "limit": 10,
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
            },
        )
        pending = await client.call_tool("get_pending_invoices", {})
        summary = await client.call_tool("get_billing_summary", {})

    assert isinstance(invoices, CallToolResult)
    assert invoices.structured_content == {
        "result": [
            {
                "client_code": "fixture-client",
                "document_number": "fixture-invoice",
                "document_type": "Fatura",
                "year": 2026,
                "issue_date": "2026-10-22",
                "payment_until": "2026-11-11",
                "amount": "10.39",
                "state": "Em Cobrança",
                "payment_date": None,
                "is_pending": True,
            }
        ]
    }
    assert isinstance(pending, CallToolResult)
    assert pending.structured_content == invoices.structured_content
    assert isinstance(summary, CallToolResult)
    assert summary.structured_content == {"invoices_to_pay": 1, "failed_invoices": 2}
    assert any(request.url.path.endswith("GetInvoicesHistory") for request in requests)
    assert any(request.url.path.endswith("GetBillingInfo") for request in requests)


@pytest.mark.asyncio
async def test_invoice_history_rejects_reversed_dates(
    server_and_requests: tuple[MCPServer[AppContext], list[httpx.Request]],
) -> None:
    server, _ = server_and_requests
    async with Client(server) as client:
        result = await client.call_tool(
            "get_invoices",
            {"date_from": "2026-12-31", "date_to": "2026-01-01"},
        )
    assert result.is_error


@pytest.mark.asyncio
async def test_sdk_exception_details_are_not_sent_to_client_or_logs(
    settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    sensitive_marker = "synthetic-private-invoice-and-password-marker"

    class FailingSimarClient:
        async def login(self) -> None:
            return

        async def get_invoices(self, **_: object) -> list[Invoice]:
            raise RuntimeError(sensitive_marker)

        async def get_pending_invoices(self) -> list[Invoice]:
            raise RuntimeError(sensitive_marker)

        async def get_billing_summary(self) -> dict[str, int]:
            raise RuntimeError(sensitive_marker)

        async def aclose(self) -> None:
            return

    server = create_server(
        client_factory=lambda *_args, **_kwargs: FailingSimarClient(),
        settings_factory=lambda: settings,
    )
    async with Client(server) as client:
        result = await client.call_tool("get_billing_summary", {})

    assert result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    assert "Could not retrieve billing summary" in content.text
    assert sensitive_marker not in content.text
    assert sensitive_marker not in caplog.text


@pytest.mark.asyncio
async def test_server_declares_only_read_only_tools() -> None:
    server = create_server()
    tools = {tool.name: tool for tool in await server.list_tools()}
    assert set(tools) == {"get_invoices", "get_pending_invoices", "get_billing_summary"}
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in tools.values())