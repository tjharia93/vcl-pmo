from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..routes.common import row_dict

router = APIRouter(prefix="/api/uat", tags=["uat"])


@router.get("")
def list_uat(db: Session = Depends(get_db)):
    return [row_dict(r) for r in db.query(models.UATCase).order_by(models.UATCase.id).all()]


@router.post("")
def create_uat(payload: schemas.UATIn, db: Session = Depends(get_db)):
    row = models.UATCase(**payload.dict())
    db.add(row)
    db.commit()
    return row_dict(row)


@router.patch("/{case_id}")
def patch_uat(case_id: str, payload: dict, db: Session = Depends(get_db)):
    row = db.get(models.UATCase, case_id)
    if not row:
        raise HTTPException(404, "UAT case not found")
    for key, value in payload.items():
        if hasattr(row, key):
            setattr(row, key, value)
    db.commit()
    return row_dict(row)
