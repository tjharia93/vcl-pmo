from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def append_context(project_id: str, req_id: str, status: str, agent: str, notes: str, files: list[str]) -> Path:
    path = ROOT / "context" / "projects" / project_id / f"{req_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# {req_id}\n\nProject: `{project_id}`\n\n")
    with path.open("a") as fh:
        fh.write(f"## {status} by {agent}\n\n{notes}\n\n")
        if files:
            fh.write("Files changed:\n")
            for item in files:
                fh.write(f"- {item}\n")
            fh.write("\n")
    return path


def commit_and_push(path: Path, req_id: str, status: str) -> dict:
    try:
        subprocess.run(["git", "-C", str(ROOT), "add", str(path.relative_to(ROOT))], check=True, timeout=20)
        commit = subprocess.run(["git", "-C", str(ROOT), "commit", "-m", f"{req_id}: {status}"], capture_output=True, text=True, timeout=30)
        if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
            return {"ok": False, "error": (commit.stdout + commit.stderr)[-300:]}
        push = subprocess.run(["git", "-C", str(ROOT), "push", "origin", "main"], capture_output=True, text=True, timeout=60)
        return {"ok": push.returncode == 0, "error": (push.stdout + push.stderr)[-300:] if push.returncode else ""}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
