from __future__ import annotations

from sqlalchemy.orm import Session

from .. import models
from . import erpnext_client


PROJECT_DT = "PMO Project"
REQ_DT = "PMO Requirement"
AGENT_DT = "PMO Agent Log"


def project_to_doc(row: models.Project) -> dict:
    return {
        "doctype": PROJECT_DT,
        "project_id": row.id,
        "project_name": row.name,
        "system": row.system,
        "requestor": row.requestor,
        "status": row.status,
        "priority": row.priority,
        "progress": row.progress or 0,
        "context": row.context,
        "excel_path": row.excel_path,
        "linked_erpnext_project": row.erpnext_project,
    }


def requirement_to_doc(row: models.Requirement, db: Session) -> dict:
    links = db.query(models.ERPNextLink).filter_by(requirement_id=row.id).all()
    return {
        "doctype": REQ_DT,
        "requirement_id": row.id,
        "project": row.project_id,
        "area": row.area,
        "requirement": row.requirement,
        "priority": row.priority,
        "status": row.status,
        "owner": row.owner,
        "uat_result": row.uat_result,
        "needs_action": row.needs_action or 0,
        "note": row.note,
        "md_path": row.md_path,
        "erpnext_links": [{"link_doctype": l.doctype, "link_name": l.name, "link_label": l.label} for l in links],
    }


def try_upsert_project(row: models.Project) -> dict | None:
    doc = project_to_doc(row)
    try:
        existing = erpnext_client.list_docs(PROJECT_DT, fields=["name", "project_id"], filters=[["project_id", "=", row.id]], limit=1)
        if existing:
            return erpnext_client.update_doc(PROJECT_DT, existing[0]["name"], doc)
        return erpnext_client.insert_doc(doc)
    except Exception:
        return None


def try_upsert_requirement(row: models.Requirement, db: Session) -> dict | None:
    doc = requirement_to_doc(row, db)
    try:
        existing = erpnext_client.list_docs(REQ_DT, fields=["name", "requirement_id"], filters=[["requirement_id", "=", row.id]], limit=1)
        if existing:
            return erpnext_client.update_doc(REQ_DT, existing[0]["name"], doc)
        return erpnext_client.insert_doc(doc)
    except Exception:
        return None


def try_insert_agent_log(req: models.Requirement | None, agent: str, status: str, notes: str, files: str) -> dict | None:
    try:
        return erpnext_client.insert_doc({
            "doctype": AGENT_DT,
            "requirement": req.id if req else None,
            "project": req.project_id if req else None,
            "agent": agent,
            "status": status.lower() if status == "Done" else status,
            "notes": notes,
            "files_changed": files,
        })
    except Exception:
        return None
