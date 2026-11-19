import asyncio
import json

import httpx
import pytest

mcp_mod = pytest.importorskip("mcp_server.prospectos_mcp")


def _mock(handler):
    mcp_mod.set_client(httpx.Client(base_url="http://test", transport=httpx.MockTransport(handler)))


def test_tools_are_registered():
    names = {t.name for t in asyncio.run(mcp_mod.server.list_tools())}
    assert {
        "list_prospects", "get_prospect", "discover_businesses", "audit_prospect", "draft_outreach",
        "approval_queue", "approve_outreach", "send_outreach", "sync_replies", "set_lead_status", "add_note",
    } <= names


def test_list_prospects_passes_filters_and_drops_empty_ones():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"items": [], "total": 0})

    _mock(handler)
    assert mcp_mod.list_prospects(city="Lakeland", limit=500) == {"items": [], "total": 0}
    assert "city=Lakeland" in seen["url"] and "limit=200" in seen["url"] and "search=" not in seen["url"]


def test_send_requires_confirmation():
    calls = []
    _mock(lambda r: calls.append(r) or httpx.Response(200, json={"id": "x"}))
    assert "error" in mcp_mod.send_outreach("abc")
    assert calls == []
    assert mcp_mod.send_outreach("abc", confirm=True) == {"id": "x"}
    assert calls[0].url.path == "/api/gmail/outreach/abc/send"


def test_bad_status_is_rejected_before_calling_api():
    calls = []
    _mock(lambda r: calls.append(r) or httpx.Response(201, json={}))
    assert "error" in mcp_mod.set_lead_status("b1", "maybe")
    assert calls == []
    mcp_mod.set_lead_status("b1", "interested", note="Asked for a call")
    assert json.loads(calls[0].content)["status"] == "INTERESTED"


def test_api_errors_come_back_readable():
    _mock(lambda r: httpx.Response(404, json={"detail": "Business not found"}))
    assert mcp_mod.get_prospect("nope") == {"error": "Business not found", "status_code": 404}
