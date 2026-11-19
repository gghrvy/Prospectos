# Using ProspectOS from Claude (MCP)

`backend/mcp_server/prospectos_mcp.py` exposes ProspectOS to Claude as 13 tools:
list/get prospects, discover businesses, audit a site, draft outreach, approval queue,
approve, send (needs `confirm=True`), sync replies, set lead status, add notes, report.

It calls the running FastAPI backend over HTTP, so the backend must be running (`dev.ps1`).

## 1. Separate virtual environment (required)

The MCP SDK (v2) needs a newer Starlette than the backend's pinned FastAPI, so keep it in its
own venv. From `backend\` in PowerShell:

```powershell
python -m venv .venv-mcp
.\.venv-mcp\Scripts\pip install -r requirements-mcp.txt httpx
```

## 2. Connect Claude Desktop

Open the config file at `%APPDATA%\Claude\claude_desktop_config.json` (create it if missing) and add:

```json
{
  "mcpServers": {
    "prospectos": {
      "command": "C:\\Codes\\ProspectAi\\backend\\.venv-mcp\\Scripts\\python.exe",
      "args": ["C:\\Codes\\ProspectAi\\backend\\mcp_server\\prospectos_mcp.py"],
      "env": { "PROSPECTOS_API_URL": "http://localhost:8000" }
    }
  }
}
```

Fully quit Claude Desktop (tray icon -> Quit) and reopen it. ProspectOS appears in the tools menu.

## 3. Claude Code (optional)

```powershell
claude mcp add prospectos -- C:\Codes\ProspectAi\backend\.venv-mcp\Scripts\python.exe C:\Codes\ProspectAi\backend\mcp_server\prospectos_mcp.py
```

## Try it

- "Find 20 HVAC companies in Lakeland, FL and save them."
- "Audit the ones with websites and show me the 5 with the biggest gaps."
- "Draft outreach for those 5." (review, then) "Approve and send the first two."
- "Sync replies and tell me who answered."

## Tests

```powershell
.\.venv-mcp\Scripts\pip install pytest
.\.venv-mcp\Scripts\python -m pytest tests\test_mcp_server.py
```
The main test suite skips this file when the MCP SDK isn't installed.
