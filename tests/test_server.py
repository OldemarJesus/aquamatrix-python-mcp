from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import parse_qs

import httpx
import pytest
from aquamatrix_simar import (
    GraphValue,
    NextReadingsInfo,
    ReadingInfo,
    SimarClient,
)
from mcp import Client
from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent

from aquamatrix_simar_mcp.config import Settings
from aquamatrix_simar_mcp.server import AppContext, create_server

LOGIN_PAGE = '<input name="__RequestVerificationToken" value="login-token">'
BILLING_PAGE = '<input name="__RequestVerificationToken" value="billing-token">'
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
        if request.url.path.endswith("GetBillingInfo"):
            return httpx.Response(
                200,
                json={"InvoicesToPay": 1, "FailedInvoices": 2},
            )
        if request.url.path.endswith("GetLastReadingInfo"):
            return httpx.Response(
                200,
                json={"LastReadingDate": "2026-10-15", "Type": "SIMAR", "Value": "459,000"},
            )
        if request.url.path.endswith("GetNextReadingsInfo"):
            return httpx.Response(200, json={"Company": "2026-11-20", "Client": "2026-11-21"})
        if request.url.path.endswith("GetWaterShortagesInfo"):
            return httpx.Response(200, json=False)
        if request.url.path.endswith("GetLastInvoiceGraph"):
            return httpx.Response(
                200,
                json=[{"Label": "VAT", "Value": 10.1834, "ValueDisplay": "EUR 10.18"}],
            )
        if request.url.path.endswith("GetBilledValuesGraph"):
            return httpx.Response(200, json=[{"Label": "OCT-26", "Value": 54.77}])
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
async def test_tools_expose_supported_sdk_features_as_structured_output(
    server_and_requests: tuple[MCPServer[AppContext], list[httpx.Request]],
) -> None:
    server, requests = server_and_requests
    async with Client(server, raise_exceptions=True) as client:
        summary = await client.call_tool("get_billing_summary", {})
        reading = await client.call_tool("get_last_reading", {})
        next_readings = await client.call_tool("get_next_readings", {})
        water_shortages = await client.call_tool("get_water_shortages", {})
        last_invoice_graph = await client.call_tool("get_last_invoice_graph", {})
        billed_values_graph = await client.call_tool("get_billed_values_graph", {})

    assert isinstance(summary, CallToolResult)
    assert summary.structured_content == {"invoices_to_pay": 1, "failed_invoices": 2}
    assert isinstance(reading, CallToolResult)
    assert reading.structured_content == {
        "reading_date": "2026-10-15",
        "reading_type": "SIMAR",
        "value": "459,000",
    }
    assert next_readings.structured_content == {
        "company_date": "2026-11-20",
        "client_date": "2026-11-21",
    }
    assert water_shortages.structured_content == {"result": False}
    assert last_invoice_graph.structured_content == {
        "result": [{"label": "VAT", "value": "10.1834", "value_display": "EUR 10.18"}]
    }
    assert billed_values_graph.structured_content == {
        "result": [{"label": "OCT-26", "value": "54.77", "value_display": None}]
    }
    assert any(request.url.path.endswith("GetBillingInfo") for request in requests)
    assert not any("InvoiceHistory" in request.url.path for request in requests)


@pytest.mark.asyncio
async def test_sdk_exception_details_are_not_sent_to_client_or_logs(
    settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    sensitive_marker = "synthetic-private-invoice-and-password-marker"

    class FailingSimarClient:
        async def login(self) -> None:
            return

        async def get_billing_summary(self) -> dict[str, int]:
            raise RuntimeError(sensitive_marker)

        async def get_last_reading(self) -> ReadingInfo:
            raise RuntimeError(sensitive_marker)

        async def get_next_readings(self) -> NextReadingsInfo:
            raise RuntimeError(sensitive_marker)

        async def get_water_shortages(self) -> bool:
            raise RuntimeError(sensitive_marker)

        async def get_last_invoice_graph(self) -> list[GraphValue]:
            raise RuntimeError(sensitive_marker)

        async def get_billed_values_graph(self) -> list[GraphValue]:
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
    assert set(tools) == {
        "get_billing_summary",
        "get_last_reading",
        "get_next_readings",
        "get_water_shortages",
        "get_last_invoice_graph",
        "get_billed_values_graph",
    }
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in tools.values())