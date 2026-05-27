import json

import frappe


def _project_for_doc(doc):
    if doc.doctype == "PMO Project":
        return doc.name
    if doc.doctype == "PMO UAT Run" and getattr(doc, "uat_case", None):
        return frappe.db.get_value("PMO UAT Case", doc.uat_case, "project")
    if doc.doctype == "PMO OAT Run" and getattr(doc, "oat_check", None):
        return frappe.db.get_value("PMO OAT Check", doc.oat_check, "project")
    return getattr(doc, "project", None)


def enqueue_excel_sync(doc, method=None):
    """Record a sync request for n8n to pick up through Frappe webhooks/API."""
    if doc.doctype == "PMO Sync Log":
        return
    project = _project_for_doc(doc)
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


def _recompute_latest(case_doctype, run_doctype, parent_field, case_name):
    if not case_name:
        return
    rows = frappe.get_all(
        run_doctype,
        filters={parent_field: case_name},
        fields=["result", "run_date"],
        order_by="run_date desc",
        limit=1,
    )
    count = frappe.db.count(run_doctype, {parent_field: case_name})
    latest_result = rows[0].result if rows else "Not Yet Run"
    if latest_result == "Not Run":
        latest_result = "Not Yet Run"
    latest_run_date = rows[0].run_date if rows else None
    frappe.db.set_value(case_doctype, case_name, {
        "latest_result": latest_result,
        "latest_run_date": latest_run_date,
        "run_count": count,
    })


def recompute_uat_latest(doc, method=None):
    _recompute_latest("PMO UAT Case", "PMO UAT Run", "uat_case", doc.uat_case)


def recompute_oat_latest(doc, method=None):
    _recompute_latest("PMO OAT Check", "PMO OAT Run", "oat_check", doc.oat_check)
