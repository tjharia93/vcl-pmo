from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

try:
    from _shell.helpers import PrefixRedirectMiddleware
except Exception:
    PrefixRedirectMiddleware = None

from . import models
from .database import Base, engine, get_db, SessionLocal
from .seed import seed
from .routes import agent, erpnext, issues, pages, projects, requirements, sync, uat
from .routes.common import row_dict
from .services import erpnext_client, excel_sync


Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed(db)

app = FastAPI(title="VCL PMO", version="0.1.0")
if PrefixRedirectMiddleware:
    app.add_middleware(PrefixRedirectMiddleware)

STATIC = Path(__file__).resolve().parents[1] / "static"
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

app.include_router(projects.router)
app.include_router(requirements.router)
app.include_router(issues.router)
app.include_router(uat.router)
app.include_router(erpnext.router)
app.include_router(sync.router)
app.include_router(agent.router)


@app.get("/api/health")
def api_health():
    frappe = erpnext_client.status()
    return {"ok": True, "app": "vcl_pmo", "db": "ok", "frappe": frappe, "erpnext_status": frappe, "excel": excel_sync.excel_status(), "excel_status": excel_sync.excel_status()}


@app.get("/healthz")
def healthz():
    return {"ok": True, "app": "vcl_pmo"}


@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    reqs = db.query(models.Requirement).all()
    projects_count = db.query(models.Project).count()
    done = sum(1 for r in reqs if r.status == "Done")
    blocked = sum(1 for r in reqs if r.status == "Blocked")
    review = sum(1 for r in reqs if r.status == "In Review")
    inbox = sum(1 for r in reqs if r.needs_action or r.status in {"Blocked", "In Review"})
    return {"projects": projects_count, "requirements": len(reqs), "done": done, "blocked": blocked, "in_review": review, "inbox": inbox}


@app.get("/api/feed")
def feed(db: Session = Depends(get_db)):
    audit_rows = [{"kind": "audit", **row_dict(r)} for r in db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).limit(50)]
    agent_rows = [{"kind": "agent", **row_dict(r)} for r in db.query(models.AgentLog).order_by(models.AgentLog.id.desc()).limit(50)]
    return sorted(audit_rows + agent_rows, key=lambda x: x.get("ts") or "", reverse=True)[:80]


app.include_router(pages.router)
