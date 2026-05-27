from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import httpx


class ERPNextNotConfigured(RuntimeError):
    pass


class ERPNextError(RuntimeError):
    pass


_CACHE: dict[str, tuple[float, Any]] = {}


def _load_env_file() -> None:
    env_path = Path("/opt/vcl/config/.env")
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text().splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))
    except PermissionError:
        return


def _config() -> tuple[str, str]:
    _load_env_file()
    url = (os.environ.get("ERPNEXT_URL") or os.environ.get("FRAPPE_URL") or "").rstrip("/")
    key = os.environ.get("ERPNEXT_API_KEY") or os.environ.get("FRAPPE_API_KEY") or ""
    sec = os.environ.get("ERPNEXT_API_SECRET") or os.environ.get("FRAPPE_API_SECRET") or ""
    if not (url and key and sec):
        raise ERPNextNotConfigured("Set ERPNEXT_URL, ERPNEXT_API_KEY, ERPNEXT_API_SECRET in /opt/vcl/config/.env")
    return url, f"token {key}:{sec}"


def _request(method: str, path: str, *, params: dict | None = None, json_body: dict | None = None) -> Any:
    base, auth = _config()
    headers = {"Authorization": auth, "Accept": "application/json"}
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    last = ""
    for attempt in range(3):
        try:
            with httpx.Client(timeout=20.0) as client:
                r = client.request(method, base + path, headers=headers, params=params, json=json_body)
            if r.status_code < 500:
                if r.status_code >= 400:
                    raise ERPNextError(f"ERPNext {r.status_code}: {r.text[:400]}")
                body = r.json() if r.text else {}
                return body.get("data") if "data" in body else body.get("message", body)
            last = r.text[:400]
        except httpx.HTTPError as exc:
            last = str(exc)
        time.sleep(0.4 * (2 ** attempt))
    raise ERPNextError(f"ERPNext request failed: {last}")


def _cached(key: str, loader):
    now = time.time()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < 60:
        return hit[1]
    value = loader()
    _CACHE[key] = (now, value)
    return value


def get_doc(doctype: str, name: str) -> dict:
    return _cached(f"doc:{doctype}:{name}", lambda: _request("GET", f"/api/resource/{doctype}/{name}"))


def list_docs(doctype: str, *, fields: list[str] | None = None, filters: list | dict | None = None, limit: int = 0) -> list[dict]:
    params: dict[str, Any] = {"limit_page_length": limit}
    if fields:
        params["fields"] = json.dumps(fields)
    if filters:
        params["filters"] = json.dumps(filters)
    return _cached(f"list:{doctype}:{json.dumps(params, sort_keys=True)}", lambda: _request("GET", f"/api/resource/{doctype}", params=params) or [])


def insert_doc(doc: dict) -> dict:
    _CACHE.clear()
    return _request("POST", f"/api/resource/{doc['doctype']}", json_body=doc)


def update_doc(doctype: str, name: str, payload: dict) -> dict:
    _CACHE.clear()
    return _request("PUT", f"/api/resource/{doctype}/{name}", json_body=payload)


def add_comment(doctype: str, name: str, text: str) -> dict:
    return _request("POST", "/api/method/frappe.desk.form.utils.add_comment", json_body={
        "reference_doctype": doctype,
        "reference_name": name,
        "content": text,
        "comment_email": "codex-cli@vcl.local",
        "comment_by": "codex-cli",
    })


def status() -> str:
    try:
        _request("GET", "/api/method/frappe.auth.get_logged_user")
        return "ok"
    except Exception as exc:
        return f"error: {str(exc)[:120]}"
