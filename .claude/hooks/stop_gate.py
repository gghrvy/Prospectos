"""Stop gate: "don't claim done without running it", enforced.

If backend code changed this session, run pytest. If frontend TypeScript changed,
run tsc --noEmit. A failure blocks the turn from ending and sends the output back to
Claude to fix. Capped at 3 consecutive blocks so a stuck run can still end.
"""
import os
import subprocess

from _common import STATE_DIR, block, clear, is_marked, project_root, read_input

MAX_BLOCKS = 3
TAIL = 3000


def tail(text: str) -> str:
    return text[-TAIL:] if len(text) > TAIL else text


def backend_python(root: str) -> str:
    for p in ("backend/.venv/Scripts/python.exe", "backend/.venv/bin/python"):
        full = os.path.join(root, p)
        if os.path.exists(full):
            return full
    return "python"


def bump_attempts(reset: bool = False) -> int:
    os.makedirs(STATE_DIR, exist_ok=True)
    path = os.path.join(STATE_DIR, "stop-attempts")
    if reset:
        if os.path.exists(path):
            os.remove(path)
        return 0
    n = int(open(path).read() or 0) + 1 if os.path.exists(path) else 1
    open(path, "w").write(str(n))
    return n


def main() -> None:
    data = read_input()
    root = project_root(data)
    failures = []

    if is_marked("backend"):
        r = subprocess.run([backend_python(root), "-m", "pytest", "-q", "-x"],
                           cwd=os.path.join(root, "backend"), capture_output=True, text=True, timeout=600)
        if r.returncode == 0:
            clear("backend")
        else:
            failures.append("Backend tests failed (pytest -q -x):\n" + tail(r.stdout + r.stderr))

    if is_marked("frontend"):
        r = subprocess.run("npx tsc --noEmit", cwd=os.path.join(root, "frontend"),
                           capture_output=True, text=True, timeout=300, shell=True)
        if r.returncode == 0:
            clear("frontend")
        else:
            failures.append("Frontend typecheck failed (tsc --noEmit):\n" + tail(r.stdout + r.stderr))

    if not failures:
        bump_attempts(reset=True)
        return
    if bump_attempts() > MAX_BLOCKS:
        bump_attempts(reset=True)
        print("Stop gate: checks still failing after 3 attempts. Report the failures honestly.")
        return
    block("\n\n".join(failures) + "\n\nFix these before reporting the task as done.")


if __name__ == "__main__":
    main()
