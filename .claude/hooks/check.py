"""PostToolUse check: fast feedback right after an edit.

Python files under backend/ are syntax-checked immediately. Each edit also marks
which side of the stack changed so the Stop gate knows what to verify.
"""
import py_compile

from _common import block, mark, project_root, read_input, rel_path


def main() -> None:
    data = read_input()
    tin = data.get("tool_input", {}) or {}
    root = project_root(data)
    raw = tin.get("file_path") or ""
    rel = rel_path(raw, root)

    if rel.startswith("backend/"):
        mark("backend")
        if rel.endswith(".py"):
            try:
                py_compile.compile(raw if raw else rel, doraise=True)
            except py_compile.PyCompileError as e:
                block(f"Syntax error in {rel}:\n{e.msg}")
    elif rel.startswith("frontend/") and rel.endswith((".ts", ".tsx")):
        mark("frontend")


if __name__ == "__main__":
    main()
