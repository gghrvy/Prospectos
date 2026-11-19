"""ProspectOS MCP server.

Lets Claude (Claude Desktop, Claude Code, or any MCP client) drive ProspectOS
through its existing REST API: find businesses, audit their sites, draft
outreach, approve and send emails, sync replies, and move leads through the
pipeline.

It talks to the running FastAPI backend over HTTP, so every rule the API
enforces (demo mode, dedup, approval before send, rate-limited batches)
still applies. Nothing here touches the database directly.

Run (stdio, for Claude Desktop / Claude Code):
    python -m mcp_server.prospectos_mcp

Env:
    PROSPECTOS_API_URL   default http://localhost:8000
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

API_URL = os.environ.get("PROSPECTOS_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = httpx.Timeout(120.0, connect=10.0)  # audits crawl live sites; give them room

LEAD_STATUSES = (
    "NEW", "AUDITED", "QUALIFIED", "OUTREACH_READY", "CONTACTED", "FOLLOW_UP", "REPLIED",
    "INTERESTED", "CONCEPT_SENT", "DISCUSSION", "DEMO_SENT", "CALL_BOOKED", "PROPOSAL",
    "WON", "LOST", "NOT_INTERESTED",
)

READ = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)
EXTERNAL = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
SENDS_EMAIL = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

server = MCPServer(
    name="prospectos",
    title="ProspectOS",
    instructions=(
        "ProspectOS finds local businesses, audits their websites, drafts outreach and sends "
        "approved emails through the user's Gmail. Typical flow: discover_businesses -> "
        "audit_prospect -> draft_outreach -> show the draft to the user -> approve_outreach -> "
        "send_outreach(confirm=True) only after the user explicitly says to send. Never send "
        "without the user's go-ahead in this conversation. Use sync_replies before reporting on "
        "replies, and set_lead_status to keep the pipeline current."
    ),
)

_client: httpx.Client | None = None


def _http() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(base_url=API_URL, timeout=TIMEOUT)
    return _client


def set_client(client: httpx.Client) -> None:
    """Test hook: swap in a client with a mock transport."""
    global _client
    _client = client


def _call(method: str, path: str, *, params: dict | None = None, json: Any = None) -> Any:
    params = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        response = _http().request(method, path, params=params, json=json)
    except httpx.ConnectError:
        return {"error": f"Can't reach the ProspectOS backend at {API_URL}. Start it (dev.ps1) and try again."}
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        return {"error": detail, "status_code": response.status_code}
    if response.status_code == 204 or not response.content:
        return {"ok": True}
    return response.json()


# --- Read -----------------------------------------------------------------

@server.tool(annotations=READ)
def list_prospects(
    search: str | None = None,
    city: str | None = None,
    category: str | None = None,
    sort_by: str = "created_at",
    limit: int = 25,
    offset: int = 0,
) -> Any:
    """List saved prospects, newest first. Filter by free-text search, city or category."""
    return _call("GET", "/api/businesses", params={
        "search": search, "city": city, "category": category,
        "sort_by": sort_by, "limit": max(1, min(limit, 200)), "offset": offset,
    })


@server.tool(annotations=READ)
def get_prospect(business_id: str) -> Any:
    """Full record for one prospect: contact details, latest audit, scores, drafts, notes, status history."""
    return _call("GET", f"/api/businesses/{business_id}")


@server.tool(annotations=READ)
def approval_queue() -> Any:
    """Current outreach drafts waiting for approval (one per prospect)."""
    return _call("GET", "/api/gmail/approval-queue")


@server.tool(annotations=READ)
def outreach_report() -> Any:
    """Sending and reply stats for outreach so far."""
    return _call("GET", "/api/gmail/report")


@server.tool(annotations=READ)
def gmail_status() -> Any:
    """Whether a Gmail account is connected for sending."""
    return _call("GET", "/api/gmail/status")


# --- Work on prospects ----------------------------------------------------

@server.tool(annotations=EXTERNAL)
def discover_businesses(
    category: str,
    city: str,
    country: str | None = None,
    radius_km: float = 5.0,
    limit: int = 25,
    save: bool = False,
    source: str = "openstreetmap",
) -> Any:
    """Find businesses of a category in a city (e.g. "plumber", "dentist").
    source="openstreetmap" (free, few emails) or "google_maps" (Apify Google Maps with
    website emails; uses the user's free Apify credit, max 50 per search, refused by the
    budget guard before it could exceed the monthly budget). Check apify_usage first.
    Set save=True to add the results to ProspectOS as prospects (duplicates are skipped).
    Google Maps runs can take a few minutes; if the call times out, wait and list_prospects."""
    return _call("POST", "/api/businesses/search", json={
        "category": category, "city": city, "country": country,
        "radius_km": radius_km, "limit": max(1, min(limit, 100)), "save": save, "source": source,
    })


@server.tool(annotations=READ)
def apify_usage() -> Any:
    """This month's Apify (Google Maps search) spend, budget and what's left."""
    return _call("GET", "/api/businesses/search/apify-usage")



@server.tool(annotations=EXTERNAL)
def audit_prospect(business_id: str) -> Any:
    """Crawl the prospect's website and score it: contact options, booking, chat, mobile,
    discovered email and opportunity types. Takes up to a minute per site."""
    return _call("POST", f"/api/businesses/{business_id}/audit")


@server.tool(annotations=WRITE)
def draft_outreach(business_id: str, angle: str | None = None, sender_id: str | None = None) -> Any:
    """Generate a new outreach email draft from the prospect's latest audit. Optional angle
    (e.g. BOOKING, AI_CHATBOT, WEBSITE_REDESIGN); otherwise the strongest opportunity is used.
    Drafts are never sent by this tool."""
    return _call("POST", f"/api/businesses/{business_id}/outreach", json={"angle": angle, "sender_id": sender_id})


@server.tool(annotations=WRITE)
def add_note(business_id: str, content: str, author: str | None = "Claude") -> Any:
    """Attach a note to a prospect (call outcomes, what they said, next steps)."""
    return _call("POST", f"/api/businesses/{business_id}/notes", json={"content": content, "author": author})


@server.tool(annotations=WRITE)
def set_lead_status(business_id: str, status: str, note: str | None = None) -> Any:
    """Move a prospect to a pipeline stage: NEW, AUDITED, QUALIFIED, OUTREACH_READY, CONTACTED,
    FOLLOW_UP, REPLIED, INTERESTED, CONCEPT_SENT, DISCUSSION, DEMO_SENT, CALL_BOOKED, PROPOSAL,
    WON, LOST, NOT_INTERESTED."""
    status = status.strip().upper()
    if status not in LEAD_STATUSES:
        return {"error": f"Unknown status {status!r}. Use one of: {', '.join(LEAD_STATUSES)}"}
    return _call("POST", f"/api/businesses/{business_id}/status",
                 json={"status": status, "note": note, "changed_by": "Claude"})


# --- Email ----------------------------------------------------------------

@server.tool(annotations=WRITE)
def approve_outreach(outreach_id: str) -> Any:
    """Mark a draft as approved by the user. Required before it can be sent."""
    return _call("POST", f"/api/gmail/outreach/{outreach_id}/approve")


@server.tool(annotations=SENDS_EMAIL)
def send_outreach(outreach_id: str, confirm: bool = False) -> Any:
    """Send one approved draft from the connected Gmail. Only call with confirm=True after the
    user has seen the draft and explicitly said to send it in this conversation."""
    if not confirm:
        return {"error": "Not sent. Show the user the draft and call again with confirm=True once they say send."}
    return _call("POST", f"/api/gmail/outreach/{outreach_id}/send")


@server.tool(annotations=EXTERNAL)
def sync_replies() -> Any:
    """Pull new replies to sent outreach from Gmail and update reply state on each prospect."""
    return _call("POST", "/api/gmail/sync-replies")


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
