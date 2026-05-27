from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..routes.common import row_dict
from ..services import audit, erpnext_pmo

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


def inflate(row: models.Requirement, db: Session) -> dict:
    item = row_dict(row)
    item["erpnext_links"] = [row_dict(l) for l in db.query(models.ERPNextLink).filter_by(requirement_id=row.id).all()]
    return item


@router.get("")
def list_requirements(project_id: str | None = None, status: str | None = None, needs_action: int | None = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.Requirement)
    if project_id:
        q = q.filter_by(project_id=project_id)
    if status:
        q = q.filter_by(status=status)
    if needs_action is not None:
        q = q.filter_by(needs_action=needs_action)
    return [inflate(r, db) for r in q.order_by(models.Requirement.id).all()]


@router.get("/{req_id}")
def get_requirement(req_id: str, db: Session = Depends(get_db)):
    row = db.get(models.Requirement, req_id)
    if not row:
        raise HTTPException(404, "Requirement not found")
    return inflate(row, db)


@router.post("")
def create_requirement(payload: schemas.RequirementIn, db: Session = Depends(get_db)):
    if db.get(models.Requirement, payload.id):
        raise HTTPException(409, "Requirement exists")
    row = models.Requirement(**payload.dict())
    db.add(row)
    db.commit()
    erpnext_pmo.try_upsert_requirement(row, db)
    audit.log(db, "tanuj", "create", f"requirement:{row.id}", payload.dict())
    return inflate(row, db)


@router.patch("/{req_id}")
def patch_requirement(req_id: str, payload: schemas.RequirementPatch, db: Session = Depends(get_db)):
    row = db.get(models.Requirement, req_id)
    if not row:
        raise HTTPException(404, "Requirement not found")
    diff = payload.dict(exclude_unset=True)
    for key, value in diff.items():
        setattr(row, key, value)
    if "status" in diff:
        row.needs_action = 1 if diff["status"] in {"Blocked", "In Review"} else row.needs_action
    row.updated_at = datetime.utcnow()
    db.commit()
    erpnext_pmo.try_upsert_requirement(row, db)
    audit.log(db, "tanuj", "update", f"requirement:{row.id}", diff)
    return inflate(row, db)


@router.get("/{req_id}/export")
def export_requirement(req_id: str, db: Session = Depends(get_db)):
    row = db.get(models.Requirement, req_id)
    if not row:
        raise HTTPException(404, "Requirement not found")
    project = db.get(models.Project, row.project_id)
    return {"requirement": inflate(row, db), "project": row_dict(project) if project else None}


@router.delete("/{req_id}")
def delete_requirement(req_id: str, db: Session = Depends(get_db)):
    row = db.get(models.Requirement, req_id)
    if not row:
        raise HTTPException(404, "Requirement not found")
    row.status = "Closed"
    row.note = ((row.note or "") + "\nSoft deleted").strip()
    db.commit()
    audit.log(db, "tanuj", "delete", f"requirement:{row.id}", {"soft": True})
    return {"ok": True}
