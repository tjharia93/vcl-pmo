import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..routes.common import row_dict
from ..services import audit, erpnext_client, erpnext_pmo, excel_sync, github_sync, telegram

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/complete")
def complete(payload: schemas.AgentCompleteIn, db: Session = Depends(get_db)):
    req = db.get(models.Requirement, payload.req_id)
    if not req:
        raise HTTPException(404, "Requirement not found")

    req.status = payload.status
    if payload.uat_result:
        req.uat_result = payload.uat_result
    req.note = payload.notes
    req.needs_action = 0
    db.commit()

    erp_doc = erpnext_pmo.try_upsert_requirement(req, db)
    if erp_doc is None:
        audit.log(db, "codex-cli", "erpnext_deferred", f"requirement:{req.id}", {"status": payload.status})

    files_json = json.dumps(payload.files_changed)
    log = models.AgentLog(req_id=req.id, project_id=req.project_id, agent=payload.agent, status=payload.status, notes=payload.notes, files=files_json)
    db.add(log)
    db.commit()
    erpnext_pmo.try_insert_agent_log(req, payload.agent, payload.status, payload.notes, files_json)

    for write in payload.erpnext_writes:
        try:
            erpnext_client.add_comment(write.get("doctype", ""), write.get("name", ""), f"PMO {payload.req_id}: {write.get('action', 'updated')} by {payload.agent}. {payload.notes}")
        except Exception as exc:
            audit.log(db, payload.agent, "comment_failed", f"{write.get('doctype')}:{write.get('name')}", str(exc))

    md_path = github_sync.append_context(req.project_id, req.id, payload.status, payload.agent, payload.notes, payload.files_changed)
    git_result = github_sync.commit_and_push(md_path, req.id, payload.status)
    if not git_result["ok"]:
        audit.log(db, payload.agent, "git_deferred", f"requirement:{req.id}", git_result)

    try:
        excel_sync.push_project(db, req.project_id)
    except Exception as exc:
        audit.log(db, payload.agent, "excel_deferred", f"requirement:{req.id}", str(exc))

    tg = telegram.send(f"{req.id} -> {payload.status} · {payload.notes[:120]}")
    if not tg["ok"]:
        audit.log(db, payload.agent, "telegram_deferred", f"requirement:{req.id}", tg)

    audit.log(db, payload.agent, "complete", f"requirement:{req.id}", payload.dict())
    return {"ok": True, "req_id": req.id, "status": payload.status, "erpnext_doc": (erp_doc or {}).get("name") if isinstance(erp_doc, dict) else None}


@router.get("/log")
def log(db: Session = Depends(get_db)):
    return [row_dict(r) for r in db.query(models.AgentLog).order_by(models.AgentLog.id.desc()).limit(100)]
