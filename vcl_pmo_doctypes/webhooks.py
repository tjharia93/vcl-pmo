import json

import frappe


def enqueue_excel_sync(doc, method=None):
    """Record a sync request for n8n to pick up through Frappe webhooks/API."""
    project = getattr(doc, "project", None)
    if doc.doctype == "PMO Project":
        project = doc.name
    detail = {
        "event": method or "on_update",
        "doctype": doc.doctype,
        "name": doc.name,
        "project": project,
        "modified": str(getattr(doc, "modified", "")),
    }
    frappe.get_doc({
        "doctype": "PMO Sync Log",
        "anchor": f"excel:{project or 'portfolio'}",
        "direction": "Frappe to Excel",
        "status": "stale",
        "project": project,
        "detail": json.dumps(detail),
    }).insert(ignore_permissions=True)
