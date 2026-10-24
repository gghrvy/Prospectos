"""PreToolUse guard: enforce the CLAUDE.md hard rules that must never slip.

- No git commands (the owner runs all git operations).
- No edits to .env files (.env.example is fine).
- No edits to released (git-tracked) Alembic migrations; add a new one instead.
"""
import os
import re
import subprocess

from _common import block, project_root, read_input, rel_path

GIT_CMD = re.compile(r"(^|[\s;&|(`])git(\.exe)?\s", re.IGNORECASE)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def is_tracked(path: str, root: str) -> bool:
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", path], cwd=root,
                           capture_output=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return os.path.exists(os.path.join(root, path))  # no git: treat existing as released


def main() -> None:
    data = read_input()
    tool = data.get("tool_name", "")
    tin = data.get("tool_input", {}) or {}
    root = project_root(data)

    if tool in {"Bash", "PowerShell"}:
        if GIT_CMD.search(" " + (tin.get("command") or "")):
            block("Blocked by project rule: never run git commands. The owner does all git "
                  "operations. Finish the change and list the files you touched instead.")
        return

    if tool in EDIT_TOOLS:
        rel = rel_path(tin.get("file_path") or tin.get("notebook_path") or "", root)
        name = os.path.basename(rel)
        if name.startswith(".env") and name != ".env.example":
            block(f"Blocked: {rel} holds secrets and must not be edited. Document new "
                  "variables in .env.example and tell the owner what to add.")
        if re.match(r"backend/alembic/versions/[^/]+\.py$", rel) and is_tracked(rel, root):
            block(f"Blocked: {rel} is a released migration. Never edit released migrations; "
                  "create a new one with `alembic revision --autogenerate -m \"...\"`.")


if __name__ == "__main__":
    main()
