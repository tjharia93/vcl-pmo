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
    "PMO Note",
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
def notes_for(project_id=None, include_inbox=1):
    _require_pmo_user()
    filters = {"status": ["!=", "Archived"]}
    if project_id:
        project_name = _project_name(project_id)
        if int(include_inbox or 0):
            filters["project"] = ["in", [project_name, ""]]
        else:
            filters["project"] = project_name
    return frappe.get_all("PMO Note", filters=filters, fields=["*"], order_by="modified desc", limit=500)


@frappe.whitelist()
def create_note(title, content_md, project_id=None, note_type="General", source="PMO Notes"):
    _require_pmo_user()
    project_name = _project_name(project_id) if project_id else None
    doc = frappe.get_doc({
        "doctype": "PMO Note",
        "title": title,
        "project": project_name,
        "note_type": note_type or "General",
        "status": "Sorted" if project_name else "Inbox",
        "content_md": content_md,
        "source": source or "PMO Notes",
    })
    doc.insert(ignore_permissions=False)
    return {"ok": True, "name": doc.name, "status": doc.status, "project": doc.project}


@frappe.whitelist()
def assign_note(note_id, project_id=None, status=None):
    _require_pmo_user()
    if not frappe.db.exists("PMO Note", note_id):
        frappe.throw(f"PMO Note not found: {note_id}")
    values = {}
    if project_id is not None:
        values["project"] = _project_name(project_id) if project_id else None
    if status:
        values["status"] = status
    elif values.get("project"):
        values["status"] = "Sorted"
    frappe.db.set_value("PMO Note", note_id, values)
    return {"ok": True, "name": note_id, **values}


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

@frappe.whitelist()
def seed_phase2():
    _require_pmo_user()

    def upsert(dt, key_field, doc):
        name = frappe.db.get_value(dt, {key_field: doc[key_field]}, "name")
        payload = dict(doc)
        payload["doctype"] = dt
        if name:
            target = frappe.get_doc(dt, name)
            target.update(payload)
            target.save(ignore_permissions=False)
            return {"doctype": dt, "key": doc[key_field], "action": "updated", "name": target.name}
        target = frappe.get_doc(payload)
        target.insert(ignore_permissions=False)
        return {"doctype": dt, "key": doc[key_field], "action": "created", "name": target.name}

    results = []
    project_meta = [
        {"project_id": "VCL-DEV-PMO-002", "project_short": "PMO", "sponsor": frappe.session.user, "project_manager": frappe.session.user, "kickoff_date": "2026-05-27", "target_completion": "2026-06-07", "current_phase": "Phase 2 Build", "charter": "# VCL PMO System\n\nBuild the Frappe-native project management system for VCL development work. Excel remains a mirror through n8n."},
        {"project_id": "VCL-DEV-HR-001", "project_short": "HR", "current_phase": "Live"},
        {"project_id": "VCL-DEV-IMP-001", "project_short": "IMP", "current_phase": "Active"},
        {"project_id": "VCL-DEV-AR-001", "project_short": "AR", "current_phase": "Active"},
    ]
    for meta in project_meta:
        name = _project_name(meta["project_id"])
        if frappe.db.exists("PMO Project", name):
            frappe.db.set_value("PMO Project", name, {k: v for k, v in meta.items() if k != "project_id"})
            results.append({"doctype": "PMO Project", "key": meta["project_id"], "action": "updated", "name": name})

    results.append(upsert("PMO Milestone", "milestone_id", {
        "milestone_id": "MS-PMO-001",
        "project": "VCL-DEV-PMO-002",
        "milestone_name": "Phase 2 PM System Foundation",
        "description": "Schema, project workspace, UAT/OAT run history, RAID and documentation foundation.",
        "target_date": "2026-06-02",
        "status": "In Progress",
        "milestone_owner": frappe.session.user,
        "weight": 40,
    }))
    task_rows = [
        ("T-PMO-001", "Phase 2 schema", "PMO-002-02", "2026-05-27", "2026-05-28", "Done", 100),
        ("T-PMO-002", "Project workspace UI", "PMO-002-03", "2026-05-28", "2026-06-01", "In Progress", 55),
        ("T-PMO-003", "Run UAT/OAT from PMO page", "PMO-002-09", "2026-06-01", "2026-06-02", "Not Started", 0),
    ]
    for task_id, title, req, start, end, status, pct in task_rows:
        results.append(upsert("PMO Task", "task_id", {
            "task_id": task_id,
            "project": "VCL-DEV-PMO-002",
            "milestone": "MS-PMO-001",
            "requirement": req,
            "title": title,
            "start_date": start,
            "end_date": end,
            "status": status,
            "assignee": frappe.session.user,
            "percent_complete": pct,
        }))
    results.append(upsert("PMO RAID Item", "raid_id", {
        "raid_id": "RAID-PMO-0001",
        "project": "VCL-DEV-PMO-002",
        "type": "Dependency",
        "title": "n8n Excel mirror workstream",
        "description": "Excel mirror is out of Phase 2 scope but required before local FastAPI PMO retirement.",
        "severity": "High",
        "probability": "Medium",
        "impact": "Cutover cannot complete until Frappe to Excel and Excel to Frappe flows pass OAT.",
        "mitigation": "Track as PMO-002-04 and OAT-PMO-006/007/008/011/012.",
        "status": "Open",
        "raid_owner": frappe.session.user,
        "raised_date": today(),
        "due_date": "2026-06-07",
    }))
    docs = [
        ("DOC-PMO-0001", "How-to", "How to record a UAT Run", "# How to record a UAT Run\n\n1. Open `/app/pmo`.\n2. Open the project workspace.\n3. Go to UAT.\n4. Open the Case.\n5. Click New Run and capture result, evidence, notes and environment."),
        ("DOC-PMO-0002", "Workflow", "PMO weekly cadence workflow", "# PMO weekly cadence\n\nReview Inbox, Roadmap, RAID, Test Status and Sync Log. Update risks, add test runs, and confirm documentation is current."),
    ]
    for doc_id, doc_type, title, content in docs:
        results.append(upsert("PMO Document", "document_id", {
            "document_id": doc_id,
            "project": "VCL-DEV-PMO-002",
            "doc_type": doc_type,
            "title": title,
            "content_md": content,
            "version": "1.0",
            "status": "Live",
            "document_owner": frappe.session.user,
            "last_reviewed": today(),
        }))
    return {"ok": True, "results": results}


# ============================================================================
# Plan & Shift APIs
# ============================================================================

ALLOWED_ASSIGNEES = {"claude", "codex", "human"}


def _next_id(prefix, doctype, width=4):
    count = frappe.db.count(doctype) + 1
    return f"{prefix}-{count:0{width}d}"


def _parse_metadata(raw):
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}


@frappe.whitelist()
def create_plan(project_id, title, description="", items=None):
    _require_pmo_user()
    project_name = _project_name(project_id)
    if not frappe.db.exists("PMO Project", project_name):
        frappe.throw(f"PMO Project not found: {project_id}")
    if isinstance(items, str):
        items = json.loads(items)
    items = items or []
    plan_id = _next_id("PLAN", "PMO Plan")
    doc = frappe.get_doc({
        "doctype": "PMO Plan",
        "plan_id": plan_id,
        "project": project_name,
        "title": title,
        "description": description,
        "planner": frappe.session.user,
        "status": "Draft",
        "proposed_items": [
            {
                "item_type": it.get("item_type", "Shift"),
                "title": it.get("title", ""),
                "description": it.get("description", ""),
                "metadata": json.dumps(it.get("metadata", {})) if isinstance(it.get("metadata"), dict) else (it.get("metadata") or ""),
                "needs_uat": 1 if it.get("needs_uat") else 0,
                "needs_oat": 1 if it.get("needs_oat") else 0,
                "assignee_hint": it.get("assignee_hint", "unassigned"),
            }
            for it in items
        ],
    })
    doc.insert(ignore_permissions=False)
    return {"ok": True, "plan_id": doc.plan_id, "name": doc.name}


@frappe.whitelist()
def add_plan_items(plan_id, items=None):
    """Append additional proposed items to an existing plan."""
    _require_pmo_user()
    if isinstance(items, str):
        items = json.loads(items)
    items = items or []
    plan_name = frappe.db.get_value("PMO Plan", {"plan_id": plan_id}, "name") or plan_id
    plan = frappe.get_doc("PMO Plan", plan_name)
    for it in items:
        plan.append("proposed_items", {
            "item_type": it.get("item_type", "Shift"),
            "title": it.get("title", ""),
            "description": it.get("description", ""),
            "metadata": json.dumps(it.get("metadata", {})) if isinstance(it.get("metadata"), dict) else (it.get("metadata") or ""),
            "needs_uat": 1 if it.get("needs_uat") else 0,
            "needs_oat": 1 if it.get("needs_oat") else 0,
            "assignee_hint": it.get("assignee_hint", "unassigned"),
        })
    plan.save(ignore_permissions=False)
    return {"ok": True, "plan": plan.name, "item_count": len(plan.proposed_items)}


@frappe.whitelist()
def create_plan_from_notes(note_ids, project_id, title=None, description="", post_to_slack=0, channel=None):
    """Create one proposed Codex plan from one or more PMO Notes.

    Notes stay as the intake audit trail. Each selected note becomes a Shift
    proposal; shifts are only created later by allocate_plan_items after an
    explicit approve_plan call.
    """
    _require_pmo_user()
    if isinstance(note_ids, str):
        note_ids = json.loads(note_ids)
    note_ids = list(dict.fromkeys(note_ids or []))
    if not note_ids:
        frappe.throw("Select at least one PMO Note")
    project_name = _project_name(project_id)
    if not frappe.db.exists("PMO Project", project_name):
        frappe.throw(f"PMO Project not found: {project_id}")
    notes = []
    for note_id in note_ids:
        if not frappe.db.exists("PMO Note", note_id):
            frappe.throw(f"PMO Note not found: {note_id}")
        notes.append(frappe.get_doc("PMO Note", note_id))
    plan_title = title or (notes[0].title if len(notes) == 1 else f"Codex intake: {len(notes)} grouped notes")
    note_summary = "\n\n".join(f"## {note.name} - {note.title}\n{note.content_md}" for note in notes)
    plan_description = (description or "Grouped PMO Note intake for Codex planning.").rstrip()
    plan_description += f"\n\n# Source notes\n{note_summary}"
    result = create_plan(project_name, plan_title, plan_description, [
        {
            "item_type": "Shift",
            "title": note.title,
            "description": note.content_md,
            "metadata": {"source_note": note.name, "source": "PMO Notes"},
            "needs_uat": 1,
            "needs_oat": 1,
            "assignee_hint": "codex",
        }
        for note in notes
    ])
    plan = frappe.get_doc("PMO Plan", result["name"])
    plan.status = "Proposed"
    plan.save(ignore_permissions=False)
    for note in notes:
        note.project = project_name
        note.status = "Converted"
        note.content_md = (note.content_md or "").rstrip() + f"\n\nConverted to Codex plan `{plan.plan_id}`."
        note.save(ignore_permissions=False)
    slack = None
    if int(post_to_slack or 0):
        slack = send_plan_to_slack(plan.plan_id, channel=channel)
    return {"ok": True, "plan_id": plan.plan_id, "name": plan.name, "notes": note_ids, "slack": slack}


@frappe.whitelist()
def approve_plan(plan_id):
    """Record explicit human approval. Allocation into shifts is gated on this."""
    _require_pmo_user()
    plan_name = frappe.db.get_value("PMO Plan", {"plan_id": plan_id}, "name") or plan_id
    plan = frappe.get_doc("PMO Plan", plan_name)
    if plan.approved_at:
        return {"ok": True, "plan": plan.name, "plan_id": plan.plan_id, "status": plan.status, "already_approved": True}
    plan.approved_by = frappe.session.user
    plan.approved_at = now_datetime()
    plan.status = "Approved"
    plan.save(ignore_permissions=False)
    return {"ok": True, "plan": plan.name, "plan_id": plan.plan_id, "status": plan.status, "approved_by": plan.approved_by, "approved_at": plan.approved_at}


@frappe.whitelist()
def allocate_plan_items(plan_id, item_indices=None, assignee=None, planned_start=None, planned_end=None):
    _require_pmo_user()
    if isinstance(item_indices, str):
        item_indices = json.loads(item_indices)
    plan_name = frappe.db.get_value("PMO Plan", {"plan_id": plan_id}, "name") or plan_id
    plan = frappe.get_doc("PMO Plan", plan_name)
    if not plan.approved_at:
        frappe.throw(f"Plan {plan.plan_id} must be explicitly approved before shifts or other implementation records can be created.")
    project_name = plan.project
    indices = set(int(i) for i in (item_indices or []))
    created = []
    for i, item in enumerate(plan.proposed_items):
        if indices and i not in indices:
            continue
        if item.promoted_to_doctype:
            continue  # already allocated
        effective_assignee = assignee or (item.assignee_hint if item.assignee_hint in ALLOWED_ASSIGNEES else None)
        metadata = _parse_metadata(item.metadata)
        if planned_start and "planned_start" not in metadata:
            metadata["planned_start"] = planned_start
        if planned_end and "planned_end" not in metadata:
            metadata["planned_end"] = planned_end
        spawned = _spawn_from_plan_item(plan, item, project_name, metadata, effective_assignee)
        if not spawned:
            continue
        item.promoted_to_doctype = spawned["doctype"]
        item.promoted_to_name = spawned["name"]
        item.promoted_at = now_datetime()
        uat_case = None
        oat_check = None
        if item.needs_uat:
            uat_case = _autocreate_uat_for_promoted(spawned, item, plan)
        if item.needs_oat:
            oat_check = _autocreate_oat_for_promoted(spawned, item, plan)
        if spawned["doctype"] == "PMO Shift" and (uat_case or oat_check):
            updates = {}
            if uat_case:
                updates["uat_case"] = uat_case
            if oat_check:
                updates["oat_check"] = oat_check
            frappe.db.set_value("PMO Shift", spawned["name"], updates)
        created.append({**spawned, "uat_case": uat_case, "oat_check": oat_check})
    if created and plan.status in {"Draft", "Proposed", "Approved"}:
        plan.status = "Allocated"
    plan.save(ignore_permissions=False)
    return {"ok": True, "plan": plan.name, "created": created}


def _spawn_from_plan_item(plan, item, project_name, metadata, assignee):
    if item.item_type == "Milestone":
        ms_id = _next_id("MS-AUTO", "PMO Milestone")
        doc = frappe.get_doc({
            "doctype": "PMO Milestone",
            "milestone_id": ms_id,
            "project": project_name,
            "milestone_name": item.title,
            "description": item.description or "",
            "target_date": metadata.get("target_date") or today(),
            "status": metadata.get("status", "Not Started"),
            "weight": metadata.get("weight", 0),
            "milestone_owner": frappe.session.user,
        })
        doc.insert(ignore_permissions=False)
        return {"doctype": "PMO Milestone", "name": doc.name}
    if item.item_type == "Requirement":
        prefix = (frappe.db.get_value("PMO Project", project_name, "project_short") or "X").upper()
        req_id = _next_id(f"REQ-{prefix}", "PMO Requirement")
        doc = frappe.get_doc({
            "doctype": "PMO Requirement",
            "requirement_id": req_id,
            "project": project_name,
            "area": metadata.get("area", "Plan"),
            "requirement": item.title,
            "priority": metadata.get("priority", "Should"),
            "status": "Not Started",
            "needs_action": 1,
            "note": item.description or "",
        })
        doc.insert(ignore_permissions=False)
        return {"doctype": "PMO Requirement", "name": doc.name}
    if item.item_type == "Task":
        task_id = _next_id("T-AUTO", "PMO Task")
        doc = frappe.get_doc({
            "doctype": "PMO Task",
            "task_id": task_id,
            "project": project_name,
            "title": item.title,
            "description": item.description or "",
            "start_date": metadata.get("start_date") or today(),
            "end_date": metadata.get("end_date") or today(),
            "status": "Not Started",
            "assignee": frappe.session.user,
            "percent_complete": 0,
        })
        doc.insert(ignore_permissions=False)
        return {"doctype": "PMO Task", "name": doc.name}
    if item.item_type == "RAID":
        raid_id = _next_id("RAID-AUTO", "PMO RAID Item")
        doc = frappe.get_doc({
            "doctype": "PMO RAID Item",
            "raid_id": raid_id,
            "project": project_name,
            "type": metadata.get("raid_type", "Risk"),
            "title": item.title,
            "description": item.description or "",
            "severity": metadata.get("severity", "Medium"),
            "probability": metadata.get("probability", "Medium"),
            "status": "Open",
            "raid_owner": frappe.session.user,
            "raised_date": today(),
        })
        doc.insert(ignore_permissions=False)
        return {"doctype": "PMO RAID Item", "name": doc.name}
    if item.item_type == "Shift":
        if not assignee:
            frappe.throw(f"Shift item '{item.title}' requires an assignee (claude/codex/human). Pass assignee= or set assignee_hint on the plan item.")
        shift_id = _next_id("SHIFT", "PMO Shift")
        doc = frappe.get_doc({
            "doctype": "PMO Shift",
            "shift_id": shift_id,
            "project": project_name,
            "title": item.title,
            "description": item.description or "",
            "shift_type": metadata.get("shift_type", "Execution"),
            "assigned_to": assignee,
            "status": "Allocated",
            "planned_start": metadata.get("planned_start") or None,
            "planned_end": metadata.get("planned_end") or None,
            "requires_uat": 1 if item.needs_uat else 0,
            "requires_oat": 1 if item.needs_oat else 0,
            "linked_plan": plan.name,
        })
        doc.insert(ignore_permissions=False)
        return {"doctype": "PMO Shift", "name": doc.name}
    return None


def _autocreate_uat_for_promoted(spawned, item, plan):
    if spawned["doctype"] == "PMO Shift":
        return None  # handled by PMOShift.before_save controller
    prefix = (frappe.db.get_value("PMO Project", plan.project, "project_short") or "X").upper()
    case_id = _next_id(f"UAT-{prefix}-PLAN", "PMO UAT Case")
    payload = {
        "doctype": "PMO UAT Case",
        "uat_case_id": case_id,
        "project": plan.project,
        "bucket": plan.plan_id,
        "linked_plan": plan.name,
        "description": f"UAT for {spawned['doctype']} {spawned['name']}: {item.title}",
        "acceptance_criteria": item.description or "",
    }
    if spawned["doctype"] == "PMO Task":
        payload["linked_task"] = spawned["name"]
    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=False)
    return doc.name


def _autocreate_oat_for_promoted(spawned, item, plan):
    if spawned["doctype"] == "PMO Shift":
        return None  # handled by PMOShift.before_save controller
    prefix = (frappe.db.get_value("PMO Project", plan.project, "project_short") or "X").upper()
    check_id = _next_id(f"OAT-{prefix}-PLAN", "PMO OAT Check")
    payload = {
        "doctype": "PMO OAT Check",
        "check_id": check_id,
        "project": plan.project,
        "area": item.item_type,
        "bucket": plan.plan_id,
        "linked_plan": plan.name,
        "check": f"OAT for {spawned['doctype']} {spawned['name']}: {item.title}",
        "acceptance_criteria": item.description or "",
    }
    if spawned["doctype"] == "PMO Task":
        payload["linked_task"] = spawned["name"]
    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=False)
    return doc.name


@frappe.whitelist()
def agent_shift_queue(agent, project_id=None, status_filter=None):
    """Read the shift queue for an agent. Returns Allocated + In Progress by default."""
    _require_pmo_user()
    if agent not in ALLOWED_ASSIGNEES:
        frappe.throw(f"agent must be one of {sorted(ALLOWED_ASSIGNEES)}")
    if isinstance(status_filter, str):
        try:
            status_filter = json.loads(status_filter)
        except Exception:
            status_filter = [status_filter]
    filters = {"assigned_to": agent}
    if project_id:
        filters["project"] = _project_name(project_id)
    if status_filter:
        filters["status"] = ["in", status_filter]
    else:
        filters["status"] = ["in", ["Allocated", "In Progress"]]
    return frappe.get_all("PMO Shift", filters=filters, fields=["*"], order_by="planned_start asc, creation asc")


@frappe.whitelist()
def start_shift(shift_id):
    _require_pmo_user()
    name = frappe.db.get_value("PMO Shift", {"shift_id": shift_id}, "name") or shift_id
    frappe.db.set_value("PMO Shift", name, {"status": "In Progress", "actual_start": now_datetime()})
    return {"ok": True, "shift": name, "status": "In Progress"}


@frappe.whitelist()
def complete_shift(shift_id, output_notes="", uat_result=None, oat_result=None):
    """Mark a shift Done. Optionally log a UAT/OAT Run for the linked case/check."""
    _require_pmo_user()
    name = frappe.db.get_value("PMO Shift", {"shift_id": shift_id}, "name") or shift_id
    shift = frappe.get_doc("PMO Shift", name)
    shift.status = "Done"
    shift.actual_end = now_datetime()
    if output_notes:
        shift.output_notes = output_notes
    shift.save(ignore_permissions=False)
    runs = []
    if uat_result and shift.uat_case:
        case_id = frappe.db.get_value("PMO UAT Case", shift.uat_case, "uat_case_id") or shift.uat_case
        runs.append({"kind": "uat", **new_run(case_id=case_id, kind="uat", result=uat_result, evidence=output_notes, notes=f"Auto-logged via complete_shift({shift_id})", environment="Frappe Cloud production")})
    if oat_result and shift.oat_check:
        check_id = frappe.db.get_value("PMO OAT Check", shift.oat_check, "check_id") or shift.oat_check
        runs.append({"kind": "oat", **new_run(case_id=check_id, kind="oat", result=oat_result, evidence=output_notes, notes=f"Auto-logged via complete_shift({shift_id})", environment="Frappe Cloud production")})
    return {"ok": True, "shift": name, "status": "Done", "runs": runs}


@frappe.whitelist()
def block_shift(shift_id, reason=""):
    _require_pmo_user()
    name = frappe.db.get_value("PMO Shift", {"shift_id": shift_id}, "name") or shift_id
    shift = frappe.get_doc("PMO Shift", name)
    shift.status = "Blocked"
    if reason:
        shift.output_notes = (shift.output_notes or "") + f"\n\n[Blocked {now_datetime()}] {reason}"
    shift.save(ignore_permissions=False)
    return {"ok": True, "shift": name, "status": "Blocked"}


@frappe.whitelist()
def project_shifts(project_id, assignee=None, status_filter=None):
    _require_pmo_user()
    filters = {"project": _project_name(project_id)}
    if assignee and assignee in ALLOWED_ASSIGNEES:
        filters["assigned_to"] = assignee
    if isinstance(status_filter, str):
        try:
            status_filter = json.loads(status_filter)
        except Exception:
            status_filter = [status_filter]
    if status_filter:
        filters["status"] = ["in", status_filter]
    return frappe.get_all("PMO Shift", filters=filters, fields=["*"], order_by="planned_start asc, creation asc")


@frappe.whitelist()
def project_plans(project_id):
    _require_pmo_user()
    return frappe.get_all("PMO Plan", filters={"project": _project_name(project_id)}, fields=["*"], order_by="created_at desc")


@frappe.whitelist()
def dispatch_shift(shift_id, set_in_progress=True):
    """Fire an outbound webhook to n8n with the shift payload so an agent (claude/codex) can pick it up.

    Reads the webhook URL from site_config.json key `pmo_n8n_dispatch_url`. n8n is expected to:
    1. Receive this payload.
    2. Route by `assigned_to` (claude / codex / human).
    3. Trigger the local agent on the developer machine (SSH, HTTP to runner, or queue).
    4. When done, POST back to /api/method/vcl_pmo_doctypes.api.complete_shift with shift_id + output_notes + optional uat_result/oat_result.
    """
    _require_pmo_user()
    import requests

    name = frappe.db.get_value("PMO Shift", {"shift_id": shift_id}, "name") or shift_id
    shift = frappe.get_doc("PMO Shift", name)
    if shift.linked_plan:
        plan = frappe.get_doc("PMO Plan", shift.linked_plan)
        if not plan.approved_at:
            frappe.throw(f"Plan {plan.plan_id} must be explicitly approved before a linked shift can be dispatched.")
    url = frappe.conf.get("pmo_n8n_dispatch_url")
    if not url:
        frappe.throw("pmo_n8n_dispatch_url not configured in site_config.json. Set it to the n8n webhook URL that should receive shift dispatches.")
    payload = {
        "event": "pmo.shift.dispatch",
        "shift_id": shift.shift_id,
        "shift_name": shift.name,
        "title": shift.title,
        "description": shift.description,
        "assigned_to": shift.assigned_to,
        "shift_type": shift.shift_type,
        "project": shift.project,
        "requires_uat": int(shift.requires_uat or 0),
        "requires_oat": int(shift.requires_oat or 0),
        "uat_case": shift.uat_case,
        "oat_check": shift.oat_check,
        "linked_plan": shift.linked_plan,
        "linked_requirement": shift.linked_requirement,
        "linked_milestone": shift.linked_milestone,
        "linked_task": shift.linked_task,
        "complete_shift_callback": "/api/method/vcl_pmo_doctypes.api.complete_shift",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        if set_in_progress and shift.status in {"Allocated", "Proposed"}:
            shift.status = "In Progress"
            shift.actual_start = now_datetime()
            shift.save(ignore_permissions=False)
        return {"ok": True, "shift": name, "n8n_status": resp.status_code, "n8n_response": (resp.text or "")[:500]}
    except Exception as e:
        return {"ok": False, "shift": name, "error": str(e)}


@frappe.whitelist()
def plan_detail(plan_id):
    _require_pmo_user()
    name = frappe.db.get_value("PMO Plan", {"plan_id": plan_id}, "name") or plan_id
    doc = frappe.get_doc("PMO Plan", name)
    items = []
    for i, it in enumerate(doc.proposed_items):
        items.append({
            "index": i,
            "name": it.name,
            "item_type": it.item_type,
            "title": it.title,
            "description": it.description,
            "metadata": _parse_metadata(it.metadata),
            "needs_uat": int(it.needs_uat or 0),
            "needs_oat": int(it.needs_oat or 0),
            "assignee_hint": it.assignee_hint,
            "promoted_to_doctype": it.promoted_to_doctype,
            "promoted_to_name": it.promoted_to_name,
            "promoted_at": it.promoted_at,
        })
    return {"plan": doc.as_dict(), "items": items}


# ---------------------------------------------------------------------------
# Slack integration — push PMO Plans to Slack as VCL-branded PDFs
# Channel and bot token come from site_config.json keys:
#   pmo_slack_bot_token         (required) - xoxb-* with chat:write + files:write
#   pmo_slack_plans_channel     (default C0B5DA141MM) - target channel id
# ---------------------------------------------------------------------------

PMO_SLACK_DEFAULT_CHANNEL = "C0B5DA141MM"  # #ai-pmo-plans on Vimit Converters workspace


def _vcl_brand_html(plan, items, project):
    """Render a single PMO Plan as a VCL-branded HTML page sized for A4 / Boox / reMarkable.

    Body font is 14pt for high-contrast e-ink reading. Primary blue is VCL Brand v1.0 #1F4E79.
    """
    from frappe.utils import format_datetime

    def esc(value):
        if value is None:
            return ""
        return frappe.utils.escape_html(str(value))

    status_color = {
        "Draft": "#6C7A89",
        "Proposed": "#8C6D1F",
        "Allocated": "#1F4E79",
        "Executed": "#2E7D32",
        "Closed": "#3B3B3B",
    }.get(plan.status or "", "#3B3B3B")

    item_rows = []
    for i, it in enumerate(items, start=1):
        uat_oat = ", ".join([t for t in (("UAT" if it.needs_uat else None), ("OAT" if it.needs_oat else None)) if t]) or "—"
        promoted = f"{it.promoted_to_doctype} {it.promoted_to_name}" if it.promoted_to_name else "Not yet promoted"
        item_rows.append(f"""
          <tr>
            <td class="num">{i}</td>
            <td class="type">{esc(it.item_type)}</td>
            <td class="title"><b>{esc(it.title)}</b><div class="desc">{esc(it.description or "")}</div></td>
            <td class="hint">{esc(it.assignee_hint or "—")}</td>
            <td class="tests">{uat_oat}</td>
            <td class="promoted">{esc(promoted)}</td>
          </tr>
        """)

    description_html = (esc(plan.description or "")).replace("\n\n", "</p><p>").replace("\n", "<br/>")
    if description_html:
        description_html = f"<p>{description_html}</p>"

    return f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<title>{esc(plan.plan_id)} — {esc(plan.title)}</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm 18mm 16mm; }}
  body {{ font-family: 'Helvetica', 'Arial', sans-serif; font-size: 14pt; color: #1A1A1A; line-height: 1.45; }}
  .stripe {{ height: 6px; background: #1F4E79; margin: 0 0 14px 0; }}
  .masthead {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }}
  .masthead .brand {{ font-size: 11pt; letter-spacing: 1.5px; color: #1F4E79; font-weight: 700; }}
  .masthead .id {{ font-size: 11pt; color: #6C7A89; font-family: 'Menlo', 'Consolas', monospace; }}
  h1 {{ font-size: 24pt; margin: 0 0 4px 0; color: #1F4E79; line-height: 1.1; }}
  .subtitle {{ color: #6C7A89; font-size: 11pt; margin-bottom: 18px; }}
  .meta {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px 18px; padding: 12px 14px; background: #F4F6F9; border-left: 4px solid #1F4E79; border-radius: 4px; margin-bottom: 18px; }}
  .meta div span {{ display: block; font-size: 9pt; color: #6C7A89; text-transform: uppercase; letter-spacing: 0.5px; }}
  .meta div b {{ font-size: 12pt; color: #1A1A1A; }}
  .status-pill {{ display: inline-block; padding: 3px 10px; border-radius: 999px; background: {status_color}; color: white; font-size: 10pt; font-weight: 600; letter-spacing: 0.4px; }}
  h2 {{ font-size: 14pt; color: #1F4E79; border-bottom: 1px solid #1F4E79; padding-bottom: 4px; margin: 24px 0 10px 0; }}
  .desc-block p {{ margin: 6px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 11pt; }}
  th {{ background: #1F4E79; color: white; text-align: left; padding: 7px 9px; font-size: 10pt; font-weight: 600; letter-spacing: 0.4px; }}
  td {{ padding: 8px 9px; border-bottom: 1px solid #E1E5EA; vertical-align: top; }}
  td.num {{ width: 22px; color: #6C7A89; font-family: 'Menlo', 'Consolas', monospace; }}
  td.type {{ width: 88px; color: #1F4E79; font-weight: 600; }}
  td.hint {{ width: 70px; font-style: italic; color: #555C66; }}
  td.tests {{ width: 70px; font-size: 10pt; color: #2E7D32; font-weight: 600; }}
  td.promoted {{ width: 130px; font-size: 9pt; color: #6C7A89; font-family: 'Menlo', 'Consolas', monospace; }}
  td .desc {{ color: #555C66; font-size: 10pt; margin-top: 3px; }}
  .footer {{ position: fixed; bottom: 8mm; left: 16mm; right: 16mm; border-top: 1px solid #E1E5EA; padding-top: 4mm; font-size: 9pt; color: #6C7A89; display: flex; justify-content: space-between; }}
</style>
</head>
<body>
  <div class="stripe"></div>
  <div class="masthead">
    <div>
      <div class="brand">VIMIT CONVERTERS · PMO</div>
      <h1>{esc(plan.title or plan.plan_id)}</h1>
      <div class="subtitle">Project: <b>{esc(project.project_name)}</b> ({esc(project.project_id)})</div>
    </div>
    <div class="id">{esc(plan.plan_id)}</div>
  </div>

  <div class="meta">
    <div><span>Status</span><b><span class="status-pill">{esc(plan.status)}</span></b></div>
    <div><span>Planner</span><b>{esc(plan.planner or '—')}</b></div>
    <div><span>Created</span><b>{esc(format_datetime(plan.created_at) if plan.created_at else '—')}</b></div>
    <div><span>Proposed Items</span><b>{len(items)}</b></div>
    <div><span>Approved By</span><b>{esc(plan.approved_by or '—')}</b></div>
    <div><span>Approved At</span><b>{esc(format_datetime(plan.approved_at) if plan.approved_at else '—')}</b></div>
  </div>

  <h2>Plan Description</h2>
  <div class="desc-block">{description_html or '<p><i>No description provided.</i></p>'}</div>

  <h2>Proposed Items</h2>
  <table>
    <thead><tr><th>#</th><th>Type</th><th>Title &amp; Description</th><th>Hint</th><th>Tests</th><th>Promoted</th></tr></thead>
    <tbody>
      {''.join(item_rows) or '<tr><td colspan="6" style="color:#6C7A89; font-style:italic;">No items proposed yet.</td></tr>'}
    </tbody>
  </table>

  <div class="footer">
    <span>VCL PMO · {esc(plan.plan_id)}</span>
    <span>Generated {esc(format_datetime(now_datetime()))}</span>
  </div>
</body></html>
"""


def _render_plan_pdf(plan_id):
    """Build the VCL-branded plan PDF and return (filename, pdf_bytes)."""
    from frappe.utils.pdf import get_pdf

    name = frappe.db.get_value("PMO Plan", {"plan_id": plan_id}, "name") or plan_id
    plan = frappe.get_doc("PMO Plan", name)
    project = frappe.get_doc("PMO Project", plan.project)
    items = list(plan.proposed_items or [])
    html = _vcl_brand_html(plan, items, project)
    pdf = get_pdf(html, {
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "10mm",
        "margin-bottom": "14mm",
        "margin-left": "10mm",
        "margin-right": "10mm",
        "print-media-type": None,
    })
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in (plan.title or "plan"))[:60]
    filename = f"{plan.plan_id}_{safe_title}.pdf"
    return filename, pdf


@frappe.whitelist()
def send_plan_to_slack(plan_id, channel=None, comment=None):
    """Render a PMO Plan as a VCL-branded PDF and upload it to Slack.

    site_config keys:
      pmo_slack_bot_token       (required)  xoxb token
      pmo_slack_plans_channel   (optional)  defaults to PMO_SLACK_DEFAULT_CHANNEL
    """
    _require_pmo_user()
    import requests

    token = frappe.conf.get("pmo_slack_bot_token")
    if not token:
        frappe.throw("pmo_slack_bot_token not set in site_config.json. Add an xoxb bot token with chat:write and files:write scopes.")
    channel_id = channel or frappe.conf.get("pmo_slack_plans_channel") or PMO_SLACK_DEFAULT_CHANNEL

    filename, pdf_bytes = _render_plan_pdf(plan_id)
    name = frappe.db.get_value("PMO Plan", {"plan_id": plan_id}, "name") or plan_id
    plan = frappe.get_doc("PMO Plan", name)
    title = f"{plan.plan_id} — {plan.title}"

    # Step 1: request upload URL.
    r1 = requests.post(
        "https://slack.com/api/files.getUploadURLExternal",
        headers={"Authorization": f"Bearer {token}"},
        data={"filename": filename, "length": len(pdf_bytes)},
        timeout=15,
    )
    j1 = r1.json()
    if not j1.get("ok"):
        return {"ok": False, "step": "getUploadURL", "error": j1.get("error"), "raw": j1}
    upload_url = j1["upload_url"]
    file_id = j1["file_id"]

    # Step 2: PUT the PDF bytes to the upload URL.
    r2 = requests.post(upload_url, data=pdf_bytes, headers={"Content-Type": "application/octet-stream"}, timeout=30)
    if r2.status_code >= 400:
        return {"ok": False, "step": "upload", "status": r2.status_code, "body": (r2.text or "")[:500]}

    # Step 3: complete upload + share to channel with a caption.
    initial_comment = comment or f":memo: New PMO Plan ready — *{plan.title}* ({plan.plan_id}) for project {plan.project}.\nStatus: {plan.status}. Open it in PMO: https://vimitconverters.frappe.cloud/app/pmo"
    payload = {
        "files": json.dumps([{"id": file_id, "title": title}]),
        "channel_id": channel_id,
        "initial_comment": initial_comment,
    }
    r3 = requests.post(
        "https://slack.com/api/files.completeUploadExternal",
        headers={"Authorization": f"Bearer {token}"},
        data=payload,
        timeout=15,
    )
    j3 = r3.json()
    if not j3.get("ok"):
        return {"ok": False, "step": "completeUpload", "error": j3.get("error"), "raw": j3}

    permalink = None
    files = j3.get("files") or []
    if files:
        permalink = files[0].get("permalink")
    return {"ok": True, "plan": plan.plan_id, "channel": channel_id, "file_id": file_id, "permalink": permalink, "filename": filename}
