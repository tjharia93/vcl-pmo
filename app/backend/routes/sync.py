from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..routes.common import row_dict
from ..services import erpnext_client, excel_sync

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.get("/status")
def status(db: Session = Depends(get_db)):
    return [row_dict(r) for r in db.query(models.SyncState).order_by(models.SyncState.anchor).all()]


@router.post("/excel/push")
def excel_push(db: Session = Depends(get_db)):
    return {"ok": True, "paths": excel_sync.push_all(db)}


@router.post("/excel/pull")
def excel_pull(db: Session = Depends(get_db)):
    return excel_sync.pull_all(db)


@router.post("/erpnext/push")
def erpnext_push():
    return {"ok": True, "mode": "pmo-cache", "status": erpnext_client.status()}


@router.post("/erpnext/pull")
def erpnext_pull():
    return {"ok": True, "mode": "read-through-cache", "status": erpnext_client.status()}
