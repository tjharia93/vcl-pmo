import json
from collections import defaultdict

import frappe
from frappe.utils import now_datetime, today


PMO_DOCTYPES = {
    "PMO Project",
    "PMO Requirement",
    "PMO Milestone",
    "PMO Task",
    "PMO RAID Item",
    "PMO UAT Case",
    "PMO UAT Run",
    "PMO OAT Check",
    "PMO OAT Run",
    "PMO Document",
    "PMO Agent Log",
    "PMO Sync Log",
}

ALLOWED_COMMENT_DOCTYPES = {
    "Project",
    "Task",
    "Issue",
    "Sales Invoice",
    "Purchase Invoice",
    "Payroll Entry",
    "Salary Slip",
    "Journal Entry",
    "Salary Structure",
    "Customer",
    "Supplier",
}


def _require_pmo_user():
    if frappe.session.user == "Administrator":
        return
    roles = set(frappe.get_roles(frappe.session.user))
    if not ({"System Manager", "PMO User"} & roles):
        frappe.throw("Not authorised for PMO", frappe.PermissionError)


def _project_name(project_id):
    return frappe.db.get_value("PMO Project", {"project_id": project_id}, "name") or project_id


def _next_run_id(kind):
    prefix = "UAT-RUN" if kind == "uat" else "OAT-RUN"
    count = frappe.db.count("PMO UAT Run" if kind == "uat" else "PMO OAT Run") + 1
    return f"{prefix}-{count:04d}"


def _run_doctype(kind):
    return "PMO UAT Run" if kind == "uat" else "PMO OAT Run"


def _case_doctype(kind):
    return "PMO UAT Case" if kind == "uat" else "PMO OAT Check"


def _case_key(kind):
    return "uat_case" if kind == "uat" else "oat_check"


def _case_id_field(kind):
    return "uat_case_id" if kind == "uat" else "check_id"


def _latest_result_value(result):
    return result if result in {"Pass", "Fail", "Blocked"} else "Not Yet Run"


def _group_count(rows, *fields):
    out = defaultdict(int)
    for row in rows:
        key = tuple(row.get(f) for f in fields)
        out[key] += 1
    return dict(out)


@frappe.whitelist()
def summary():
    _require_pmo_user()
    reqs = frappe.get_all("PMO Requirement", fields=["status", "needs_action"])
    raid = frappe.get_all("PMO RAID Item", fields=["type", "severity", "status"])
    milestones = frappe.get_all("PMO Milestone", fields=["status", "project", "weight"])
    return {
        "projects": frappe.db.count("PMO Project"),
        "requirements": len(reqs),
        "done": sum(1 for row in reqs if row.status == "Done"),
        "blocked": sum(1 for row in reqs if row.status == "Blocked"),
        "in_review": sum(1 for row in reqs if row.status == "In Review"),
        "inbox": sum(1 for row in reqs if row.needs_action or row.status in {"Blocked", "In Review"}),
        "raid_open": sum(1 for row in raid if row.status in {"Open", "Mitigating"}),
        "raid_by_type": {"|".join(k): v for k, v in _group_count(raid, "type", "status").items()},
        "milestones": len(milestones),
        "milestones_achieved": sum(1 for row in milestones if row.status == "Achieved"),
    }


@frappe.whitelist()
def project_packet(project_id):
    _require_pmo_user()
    project_name = _project_name(project_id)
    project = frappe.get_doc("PMO Project", project_name)
    return {
        "project": project.as_dict(),
        "requirements": frappe.get_all("PMO Requirement", filters={"project": project.name}, fields=["*"], order_by="requirement_id asc"),
        "milestones": frappe.get_all("PMO Milestone", filters={"project": project.name}, fields=["*"], order_by="target_date asc"),
        "tasks": frappe.get_all("PMO Task", filters={"project": project.name}, fields=["*"], order_by="start_date asc"),
        "raid": frappe.get_all("PMO RAID Item", filters={"project": project.name}, fields=["*"], order_by="raised_date desc"),
        "uat_cases": frappe.get_all("PMO UAT Case", filters={"project": project.name}, fields=["*"], order_by="uat_case_id asc"),
        "oat_checks": frappe.get_all("PMO OAT Check", filters={"project": project.name}, fields=["*"], order_by="check_id asc"),
        "documents": frappe.get_all("PMO Document", filters={"project": ["in", [project.name, ""]]}, fields=["*"], order_by="doc_type asc, title asc"),
    }


@frappe.whitelist()
def project_overview(project_id):
    _require_pmo_user()
    project_name = _project_name(project_id)
    project = frappe.get_doc("PMO Project", project_name)
    milestones = frappe.get_all("PMO Milestone", filters={"project": project.name}, fields=["name", "milestone_id", "milestone_name", "status", "target_date", "actual_date", "weight"], order_by="target_date asc")
    raid = frappe.get_all("PMO RAID Item", filters={"project": project.name}, fields=["type", "severity", "status"])
    uat = frappe.get_all("PMO UAT Case", filters={"project": project.name}, fields=["latest_result"])
    oat = frappe.get_all("PMO OAT Check", filters={"project": project.name}, fields=["latest_result"])
    agent = frappe.get_all("PMO Agent Log", filters={"project": project.name}, fields=["name", "agent", "status", "notes", "ts"], order_by="ts desc", limit=10)
    sync = frappe.get_all("PMO Sync Log", filters={"project": project.name}, fields=["name", "anchor", "direction", "status", "detail", "ts"], order_by="ts desc", limit=10)
    return {
        "project": project.as_dict(),
        "milestones": milestones,
        "raid_counts": {"|".join(k): v for k, v in _group_count(raid, "type", "severity", "status").items()},
        "test_status": {
            "uat": {"|".join(k): v for k, v in _group_count(uat, "latest_result").items()},
            "oat": {"|".join(k): v for k, v in _group_count(oat, "latest_result").items()},
        },
        "recent_activity": sorted(agent + sync, key=lambda row: row.get("ts") or "", reverse=True)[:10],
    }


@frappe.whitelist()
def project_gantt(project_id):
    _require_pmo_user()
    project_name = _project_name(project_id)
    milestones = frappe.get_all("PMO Milestone", filters={"project": project_name}, fields=["name", "milestone_id", "milestone_name", "target_date", "actual_date", "status"], order_by="target_date asc")
    tasks = frappe.get_all("PMO Task", filters={"project": project_name}, fields=["name", "task_id", "title", "milestone", "requirement", "start_date", "end_date", "status", "percent_complete"], order_by="start_date asc")
    deps = []
    for task in tasks:
        doc = frappe.get_doc("PMO Task", task.name)
        for pred in doc.get("predecessors") or []:
            deps.append({"task": task.task_id, "predecessor": pred.predecessor_task, "type": pred.dependency_type, "lag_days": pred.lag_days})
    return {"milestones": milestones, "tasks": tasks, "dependencies": deps}


@frappe.whitelist()
def case_history(case_id, kind="uat"):
    _require_pmo_user()
    kind = kind.lower()
    dt = _run_doctype(kind)
    key = _case_key(kind)
    case_name = frappe.db.get_value(_case_doctype(kind), {_case_id_field(kind): case_id}, "name") or case_id
    return frappe.get_all(dt, filters={key: case_name}, fields=["*"], order_by="run_date desc")


@frappe.whitelist()
def new_run(case_id, kind="uat", result="Not Run", tester=None, evidence="", notes="", environment="Frappe Cloud production"):
    _require_pmo_user()
    kind = kind.lower()
    if kind not in {"uat", "oat"}:
        frappe.throw("kind must be uat or oat")
    case_dt = _case_doctype(kind)
    run_dt = _run_doctype(kind)
    key = _case_key(kind)
    case_name = frappe.db.get_value(case_dt, {_case_id_field(kind): case_id}, "name") or case_id
    if not frappe.db.exists(case_dt, case_name):
        frappe.throw(f"{case_dt} not found: {case_id}")
    run_number = frappe.db.count(run_dt, {key: case_name}) + 1
    doc = frappe.get_doc({
        "doctype": run_dt,
        "run_id": _next_run_id(kind),
        key: case_name,
        "run_number": run_number,
        "run_date": now_datetime(),
        "tester": tester or frappe.session.user,
        "result": result,
        "evidence": evidence,
        "notes": notes,
        "environment": environment,
    })
    doc.insert(ignore_permissions=False)
    latest = recompute_latest(case_name, kind)
    return {"ok": True, "run_id": doc.run_id, "name": doc.name, "latest": latest}


@frappe.whitelist()
def recompute_latest(case_id, kind="uat"):
    _require_pmo_user()
    kind = kind.lower()
    case_dt = _case_doctype(kind)
    run_dt = _run_doctype(kind)
    key = _case_key(kind)
    case_name = frappe.db.get_value(case_dt, {_case_id_field(kind): case_id}, "name") or case_id
    rows = frappe.get_all(run_dt, filters={key: case_name}, fields=["name", "result", "run_date"], order_by="run_date desc", limit=1)
    count = frappe.db.count(run_dt, {key: case_name})
    latest_result = _latest_result_value(rows[0].result) if rows else "Not Yet Run"
    latest_run_date = rows[0].run_date if rows else None
    frappe.db.set_value(case_dt, case_name, {"latest_result": latest_result, "latest_run_date": latest_run_date, "run_count": count})
    return {"case": case_name, "latest_result": latest_result, "latest_run_date": latest_run_date, "run_count": count}


@frappe.whitelist()
def raid_register(project_id=None, type=None):
    _require_pmo_user()
    filters = {}
    if project_id:
        filters["project"] = _project_name(project_id)
    if type:
        filters["type"] = type
    return frappe.get_all("PMO RAID Item", filters=filters, fields=["*"], order_by="severity asc, due_date asc")


@frappe.whitelist()
def documents_for(project_id=None):
    _require_pmo_user()
    filters = {}
    if project_id:
        filters["project"] = ["in", [_project_name(project_id), ""]]
    rows = frappe.get_all("PMO Document", filters=filters, fields=["*"], order_by="doc_type asc, title asc")
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.doc_type or "Other"].append(row)
    return dict(grouped)


@frappe.whitelist()
def mark_milestone(milestone_id, status, actual_date=None):
    _require_pmo_user()
    name = frappe.db.get_value("PMO Milestone", {"milestone_id": milestone_id}, "name") or milestone_id
    updates = {"status": status}
    if actual_date:
        updates["actual_date"] = actual_date
    elif status == "Achieved":
        updates["actual_date"] = today()
    frappe.db.set_value("PMO Milestone", name, updates)
    doc = frappe.get_doc("PMO Milestone", name)
    _recompute_project_progress(doc.project)
    return {"ok": True, "milestone": name, "status": status}


@frappe.whitelist()
def link_task(task_id, predecessor_task_id, type="FS", lag_days=0):
    _require_pmo_user()
    task_name = frappe.db.get_value("PMO Task", {"task_id": task_id}, "name") or task_id
    pred_name = frappe.db.get_value("PMO Task", {"task_id": predecessor_task_id}, "name") or predecessor_task_id
    doc = frappe.get_doc("PMO Task", task_name)
    doc.append("predecessors", {"predecessor_task": pred_name, "dependency_type": type, "lag_days": lag_days})
    doc.save(ignore_permissions=False)
    return {"ok": True, "task": task_name, "predecessor": pred_name}


def _recompute_project_progress(project_name):
    milestones = frappe.get_all("PMO Milestone", filters={"project": project_name}, fields=["status", "weight"])
    if not milestones:
        return
    total_weight = sum((row.weight or 0) for row in milestones) or len(milestones)
    achieved = sum((row.weight or 1) for row in milestones if row.status == "Achieved")
    frappe.db.set_value("PMO Project", project_name, "progress", round((achieved / total_weight) * 100))


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
        if doctype and name and doctype in ALLOWED_COMMENT_DOCTYPES:
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": doctype,
                "reference_name": name,
                "content": f"PMO {req_id}: {action} by {agent}. {notes}",
            }).insert(ignore_permissions=False)

    return {"ok": True, "req_id": req_id, "status": status, "erpnext_doc": req.name}


@frappe.whitelist()
def oat_run(project=None):
    _require_pmo_user()
    filters = {"project": _project_name(project)} if project else {}
    checks = frappe.get_all("PMO OAT Check", filters=filters, fields=["name", "check_id", "area", "check", "latest_result", "latest_run_date", "run_count"])
    passed = sum(1 for row in checks if row.latest_result == "Pass")
    failed = sum(1 for row in checks if row.latest_result == "Fail")
    return {"ok": bool(checks) and failed == 0, "total": len(checks), "passed": passed, "failed": failed, "checks": checks}


@frappe.whitelist()
def log_sync(anchor, direction, status, detail="", project=None):
    _require_pmo_user()
    doc = frappe.get_doc({
        "doctype": "PMO Sync Log",
        "anchor": anchor,
        "direction": direction,
        "status": status,
        "detail": detail,
        "project": _project_name(project) if project else None,
        "ts": now_datetime(),
    })
    doc.insert(ignore_permissions=False)
    return {"ok": True, "name": doc.name}
