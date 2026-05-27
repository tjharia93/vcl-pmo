from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..routes.common import row_dict

router = APIRouter(prefix="/api/issues", tags=["issues"])


@router.get("")
def list_issues(db: Session = Depends(get_db)):
    return [row_dict(r) for r in db.query(models.Issue).order_by(models.Issue.id).all()]


@router.post("")
def create_issue(payload: schemas.IssueIn, db: Session = Depends(get_db)):
    row = models.Issue(**payload.dict())
    db.add(row)
    db.commit()
    return row_dict(row)


@router.patch("/{issue_id}")
def patch_issue(issue_id: str, payload: dict, db: Session = Depends(get_db)):
    row = db.get(models.Issue, issue_id)
    if not row:
        raise HTTPException(404, "Issue not found")
    for key, value in payload.items():
        if hasattr(row, key):
            setattr(row, key, value)
    db.commit()
    return row_dict(row)
