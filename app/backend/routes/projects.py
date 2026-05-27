from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..routes.common import row_dict
from ..services import audit, erpnext_pmo

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    rows = []
    for p in db.query(models.Project).order_by(models.Project.id).all():
        item = row_dict(p)
        total = db.query(models.Requirement).filter_by(project_id=p.id).count()
        done = db.query(models.Requirement).filter_by(project_id=p.id, status="Done").count()
        item["req_count"] = total
        item["done_count"] = done
        rows.append(item)
    return rows


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    row = db.get(models.Project, project_id)
    if not row:
        raise HTTPException(404, "Project not found")
    return row_dict(row)


@router.post("")
def create_project(payload: schemas.ProjectIn, db: Session = Depends(get_db)):
    if db.get(models.Project, payload.id):
        raise HTTPException(409, "Project exists")
    row = models.Project(**payload.dict())
    db.add(row)
    db.commit()
    erpnext_pmo.try_upsert_project(row)
    audit.log(db, "tanuj", "create", f"project:{row.id}", payload.dict())
    return row_dict(row)


@router.patch("/{project_id}")
def patch_project(project_id: str, payload: schemas.ProjectPatch, db: Session = Depends(get_db)):
    row = db.get(models.Project, project_id)
    if not row:
        raise HTTPException(404, "Project not found")
    diff = payload.dict(exclude_unset=True)
    for key, value in diff.items():
        setattr(row, key, value)
    row.updated_at = datetime.utcnow()
    db.commit()
    erpnext_pmo.try_upsert_project(row)
    audit.log(db, "tanuj", "update", f"project:{row.id}", diff)
    return row_dict(row)
