from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from . import models


EXCEL_ROOT = Path("/mnt/vimit/apps/14. AI PMO/projects")

PROJECTS = [
    ("VCL-DEV-PMO-002", "VCL PMO System", "FastAPI + SQLite + ERPNext links", "Tanuj", "In Build", "Critical", 20),
    ("VCL-DEV-HR-001", "HR Payroll", "ERPNext payroll controls", "Tanuj", "Live", "Critical", 92),
    ("VCL-DEV-IMP-001", "Imports Control", "Frappe imports workflow", "Tanuj", "Active", "High", 55),
    ("VCL-DEV-AR-001", "AR Collections", "Receivables control", "Tanuj", "Active", "High", 35),
]

SEED_REQS_PMO = [
    ("PMO-002-01", "VCL-DEV-PMO-002", "Scaffold", "FastAPI app + intranet mount + health route", "Must Have", "Done", "codex-cli", "Pass"),
    ("PMO-002-02", "VCL-DEV-PMO-002", "Database", "SQLite schema (projects, requirements, erpnext_links...)", "Must Have", "In Progress", "codex-cli", "Not Tested"),
    ("PMO-002-03", "VCL-DEV-PMO-002", "Frontend", "Steel+Pulse fusion - Inbox default landing", "Must Have", "Not Started", "codex-cli", "Not Tested"),
    ("PMO-002-04", "VCL-DEV-PMO-002", "Excel sync", "Read/write per-project xlsx + inotify watcher", "Must Have", "Not Started", "codex-cli", "Not Tested"),
    ("PMO-002-05", "VCL-DEV-PMO-002", "ERPNext read", "REST wrapper + /api/erpnext/{preview,search}", "Must Have", "Not Started", "codex-cli", "Not Tested"),
    ("PMO-002-06", "VCL-DEV-PMO-002", "Agent webhook", "POST /agent/complete - MD + git + Telegram", "Must Have", "Not Started", "codex-cli", "Not Tested"),
    ("PMO-002-07", "VCL-DEV-PMO-002", "ERPNext write", "Task mirror only - no financial doctype writes", "Should", "Not Started", "codex-cli", "Not Tested"),
    ("PMO-002-08", "VCL-DEV-PMO-002", "Command palette", "Cmd/Ctrl+K - search + actions + ERPNext doc lookup", "Must Have", "Not Started", "codex-cli", "Not Tested"),
    ("PMO-002-09", "VCL-DEV-PMO-002", "UAT + Issues", "UAT tab in drawer - sign-off banner - issues view", "Should", "Not Started", "codex-cli", "Not Tested"),
    ("PMO-002-10", "VCL-DEV-PMO-002", "Polish", "Live ticker - sparklines - Render to PDF - Telegram", "Should", "Not Started", "codex-cli", "Not Tested"),
]

SEED_REQS_HR = [
    ("HR-001", "VCL-DEV-HR-001", "Employees", "Employee master import and company filters", "Must Have", "Done", "codex-cli", "Pass"),
    ("HR-002", "VCL-DEV-HR-001", "Payroll", "Salary Structure formulas", "Must Have", "In Review", "codex-cli", "Not Tested"),
    ("HR-003", "VCL-DEV-HR-001", "LWP", "Leave without pay entry flow", "Must Have", "Done", "codex-cli", "Pass"),
    ("HR-004", "VCL-DEV-HR-001", "Casuals", "Casual worker weekly upload", "Must Have", "Done", "codex-cli", "Pass"),
    ("HR-005", "VCL-DEV-HR-001", "Piecework", "Piece-work daily capture", "Must Have", "Done", "codex-cli", "Pass"),
    ("HR-006", "VCL-DEV-HR-001", "Overtime", "Permanent employee overtime capture", "Must Have", "Done", "codex-cli", "Pass"),
    ("HR-007", "VCL-DEV-HR-001", "Inputs", "Monthly input reconciliation", "Must Have", "Done", "codex-cli", "Pass"),
    ("HR-008", "VCL-DEV-HR-001", "Slips", "Salary slip read-only view", "Must Have", "Done", "codex-cli", "Pass"),
    ("HR-009", "VCL-DEV-HR-001", "Recon", "ERPNext vs import reconciliation", "Should", "Done", "codex-cli", "Pass"),
    ("HR-010", "VCL-DEV-HR-001", "PDF", "Payslip PDF download", "Should", "Done", "codex-cli", "Pass"),
    ("HR-011", "VCL-DEV-HR-001", "Security", "System-user guarded module", "Must Have", "Done", "codex-cli", "Pass"),
    ("HR-012", "VCL-DEV-HR-001", "Audit", "Payroll action audit trail", "Should", "Done", "codex-cli", "Pass"),
    ("HR-013", "VCL-DEV-HR-001", "Brand", "VCL brand v1.1 styling", "Should", "Done", "codex-cli", "Pass"),
    ("HR-014", "VCL-DEV-HR-001", "Handoff", "Operational handoff and fixes", "Should", "Done", "codex-cli", "Pass"),
]

OTHER_REQS = [
    ("IMP-001", "VCL-DEV-IMP-001", "Imports", "Import shipment dashboard", "Must Have", "In Progress", "codex-cli", "Not Tested"),
    ("AR-005", "VCL-DEV-AR-001", "Collections", "CFO decision queue for blocked accounts", "Must Have", "Blocked", "tanuj", "Not Tested"),
]


def seed(db: Session) -> None:
    for pid, name, system, requestor, status, priority, progress in PROJECTS:
        if not db.get(models.Project, pid):
            db.add(models.Project(
                id=pid,
                name=name,
                system=system,
                requestor=requestor,
                status=status,
                priority=priority,
                progress=progress,
                excel_path=str(EXCEL_ROOT / name / f"{name} PMO.xlsx"),
                erpnext_project=name,
            ))
    for row in SEED_REQS_PMO + SEED_REQS_HR + OTHER_REQS:
        rid, pid, area, text, priority, status, owner, uat = row
        if not db.get(models.Requirement, rid):
            db.add(models.Requirement(
                id=rid,
                project_id=pid,
                area=area,
                requirement=text,
                priority=priority,
                status=status,
                owner=owner,
                uat_result=uat,
                needs_action=1 if status in {"Blocked", "In Review"} else 0,
                md_path=f"context/projects/{pid}/{rid}.md",
            ))
    if not db.query(models.ERPNextLink).filter_by(requirement_id="HR-002").first():
        for name in ("VCL Salary Structure", "BIL Salary Structure", "BVL Salary Structure"):
            db.add(models.ERPNextLink(requirement_id="HR-002", project_id="VCL-DEV-HR-001", doctype="Salary Structure", name=name, label=name))
    for anchor in ("erpnext", "excel:master"):
        if not db.get(models.SyncState, anchor):
            db.add(models.SyncState(anchor=anchor, status="stale"))
    db.commit()
