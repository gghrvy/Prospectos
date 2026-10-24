"""Shared helpers for ProspectOS Claude Code hooks (stdlib only)."""
import json
import os
import sys

STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")


def read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def project_root(data: dict) -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()


def rel_path(path: str, root: str) -> str:
    """Project-relative path with forward slashes, lowercase on Windows."""
    if not path:
        return ""
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    rel = os.path.relpath(os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(root)))
    return rel.replace("\\", "/")


def mark(side: str) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    open(os.path.join(STATE_DIR, f"dirty-{side}"), "w").close()


def is_marked(side: str) -> bool:
    return os.path.exists(os.path.join(STATE_DIR, f"dirty-{side}"))


def clear(side: str) -> None:
    try:
        os.remove(os.path.join(STATE_DIR, f"dirty-{side}"))
    except FileNotFoundError:
        pass


def block(message: str) -> None:
    """Exit code 2 feeds stderr back to Claude (blocks PreToolUse / Stop)."""
    print(message, file=sys.stderr)
    sys.exit(2)
