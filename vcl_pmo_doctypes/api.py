import json

import frappe
from frappe.utils import now_datetime


PMO_DOCTYPES = {
    "PMO Project",
    "PMO Requirement",
    "PMO UAT Case",
    "PMO OAT Check",
    "PMO Agent Log",
    "PMO Sync Log",
}


def _require_pmo_user():
    if frappe.session.user == "Administrator":
        return
    roles = set(frappe.get_roles(frappe.session.user))
    if not ({"System Manager", "PMO User"} & roles):
        frappe.throw("Not authorised for PMO", frappe.PermissionError)


@frappe.whitelist()
def summary():
    _require_pmo_user()
    reqs = frappe.get_all("PMO Requirement", fields=["status", "needs_action"])
    return {
        "projects": frappe.db.count("PMO Project"),
        "requirements": len(reqs),
        "done": sum(1 for row in reqs if row.status == "Done"),
        "blocked": sum(1 for row in reqs if row.status == "Blocked"),
        "in_review": sum(1 for row in reqs if row.status == "In Review"),
        "inbox": sum(1 for row in reqs if row.needs_action or row.status in {"Blocked", "In Review"}),
    }


@frappe.whitelist()
def project_packet(project_id):
    _require_pmo_user()
    project = frappe.get_doc("PMO Project", project_id)
    requirements = frappe.get_all(
        "PMO Requirement",
        filters={"project": project.name},
        fields=["*"],
        order_by="requirement_id asc",
    )
    uat_cases = frappe.get_all(
        "PMO UAT Case",
        filters={"project": project.name},
        fields=["*"],
        order_by="uat_case_id asc",
    )
    oat_checks = frappe.get_all(
        "PMO OAT Check",
        filters={"project": project.name},
        fields=["*"],
        order_by="check_id asc",
    )
    return {
        "project": project.as_dict(),
        "requirements": requirements,
        "uat_cases": uat_cases,
        "oat_checks": oat_checks,
    }


@frappe.whitelist()
def agent_complete(req_id, status, agent="codex-cli", notes="", uat_result=None, files_changed=None, erpnext_writes=None):
    _require_pmo_user()
    req_name = frappe.db.get_value("PMO Requirement", {"requirement_id": req_id}, "name")
    if not req_name:
        frappe.throw(f"PMO Requirement not found: {req_id}", frappe.DoesNotExistError)

    req = frappe.get_doc("PMO Requirement", req_name)
    req.status = status
    if uat_result:
        req.uat_result = uat_result
    req.note = notes
    req.needs_action = 0
    req.save(ignore_permissions=False)

    if isinstance(files_changed, str):
        try:
            files_changed = json.loads(files_changed)
        except Exception:
            files_changed = [files_changed]
    if isinstance(erpnext_writes, str):
        try:
            erpnext_writes = json.loads(erpnext_writes)
        except Exception:
            erpnext_writes = []

    log = frappe.get_doc({
        "doctype": "PMO Agent Log",
        "requirement": req.name,
        "project": req.project,
        "agent": agent,
        "status": status.lower() if status == "Done" else status,
        "notes": notes,
        "files_changed": json.dumps(files_changed or []),
        "ts": now_datetime(),
    })
    log.insert(ignore_permissions=False)

    for write in erpnext_writes or []:
        doctype = write.get("doctype")
        name = write.get("name")
        action = write.get("action", "updated")
        if doctype and name:
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": doctype,
                "reference_name": name,
                "content": f"PMO {req_id}: {action} by {agent}. {notes}",
            }).insert(ignore_permissions=True)

    return {"ok": True, "req_id": req_id, "status": status, "erpnext_doc": req.name}


@frappe.whitelist()
def oat_run(project=None):
    _require_pmo_user()
    filters = {"project": project} if project else {}
    checks = frappe.get_all("PMO OAT Check", filters=filters, fields=["name", "check_id", "area", "check", "status"])
    passed = sum(1 for row in checks if row.status == "Pass")
    failed = sum(1 for row in checks if row.status == "Fail")
    return {
        "ok": bool(checks) and failed == 0,
        "total": len(checks),
        "passed": passed,
        "failed": failed,
        "checks": checks,
    }


@frappe.whitelist()
def log_sync(anchor, direction, status, detail="", project=None):
    _require_pmo_user()
    doc = frappe.get_doc({
        "doctype": "PMO Sync Log",
        "anchor": anchor,
        "direction": direction,
        "status": status,
        "detail": detail,
        "project": project,
        "ts": now_datetime(),
    })
    doc.insert(ignore_permissions=False)
    return {"ok": True, "name": doc.name}
