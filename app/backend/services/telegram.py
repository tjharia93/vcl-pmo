import subprocess


NOTIFY = "/home/tanujharia/projects/agent_inbox_bot/notify.sh"


def send(message: str) -> dict:
    try:
        r = subprocess.run([NOTIFY, message], capture_output=True, text=True, timeout=15)
        return {"ok": r.returncode == 0, "error": (r.stdout + r.stderr)[-300:]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
