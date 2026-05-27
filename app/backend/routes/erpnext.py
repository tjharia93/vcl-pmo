import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..routes.common import row_dict
from ..services import audit, erpnext_client, erpnext_pmo

router = APIRouter(prefix="/api/erpnext", tags=["erpnext"])

PREVIEW_FIELDS = {
    "Sales Invoice": ["name", "customer", "posting_date", "grand_total", "outstanding_amount", "docstatus"],
    "Purchase Invoice": ["name", "supplier", "bill_no", "posting_date", "grand_total", "outstanding_amount", "docstatus"],
    "Customer": ["name", "customer_name", "tax_id", "default_sales_partner"],
    "Supplier": ["name", "supplier_name", "tax_id"],
    "Salary Structure": ["name", "company", "is_active", "docstatus"],
    "Payroll Entry": ["name", "posting_date", "total_salary", "number_of_employees", "docstatus"],
    "Project": ["name", "project_name", "status", "percent_complete", "expected_end_date"],
    "Task": ["name", "subject", "status", "progress", "exp_end_date"],
    "Issue": ["name", "subject", "status"],
}


@router.get("/preview")
def preview(doctype: str, name: str, db: Session = Depends(get_db)):
    key = f"{doctype}:{name}"
    cached = db.get(models.PreviewCache, key)
    try:
        doc = erpnext_client.get_doc(doctype, name)
        fields = PREVIEW_FIELDS.get(doctype, ["name"])
        payload = {field: doc.get(field) for field in fields}
        payload["doctype"] = doctype
        payload["name"] = doc.get("name", name)
        if doctype == "Salary Structure":
            payload["formula_check"] = "live"
        db.merge(models.PreviewCache(key=key, payload=json.dumps(payload), updated_at=datetime.utcnow()))
        db.commit()
        return payload
    except Exception as exc:
        if cached:
            payload = json.loads(cached.payload)
            payload["stale"] = True
            return payload
        return {"doctype": doctype, "name": name, "status": "offline", "error": str(exc)[:160], "formula_check": "offline" if doctype == "Salary Structure" else None}


@router.get("/search")
def search(q: str = "", doctypes: str = ""):
    names = [d.strip() for d in doctypes.split(",") if d.strip()] or list(PREVIEW_FIELDS)
    results = []
    for doctype in names:
        try:
            rows = erpnext_client.list_docs(doctype, fields=["name"], filters=[["name", "like", f"%{q}%"]], limit=8)
            results.extend({"doctype": doctype, "name": r["name"], "label": r["name"]} for r in rows)
        except Exception:
            continue
    if not results and q:
        results = [{"doctype": "Project", "name": q, "label": f"Offline result: {q}"}]
    return results[:30]


@router.post("/link")
def add_link(payload: schemas.ERPNextLinkIn, db: Session = Depends(get_db)):
    req = db.get(models.Requirement, payload.req_id)
    if not req:
        raise HTTPException(404, "Requirement not found")
    row = models.ERPNextLink(requirement_id=req.id, project_id=req.project_id, doctype=payload.doctype, name=payload.name, label=payload.label or payload.name)
    db.add(row)
    db.commit()
    erpnext_pmo.try_upsert_requirement(req, db)
    audit.log(db, "tanuj", "link", f"requirement:{req.id}", payload.dict())
    return row_dict(row)


@router.delete("/link/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    row = db.get(models.ERPNextLink, link_id)
    if not row:
        raise HTTPException(404, "Link not found")
    db.delete(row)
    db.commit()
    audit.log(db, "tanuj", "unlink", f"erpnext_link:{link_id}", {})
    return {"ok": True}
