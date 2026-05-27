from typing import Any

from pydantic import BaseModel, Field


class ProjectIn(BaseModel):
    id: str
    name: str
    system: str | None = None
    requestor: str | None = None
    go_live: str | None = None
    status: str = "Active"
    priority: str = "High"
    progress: int = 0
    context: str | None = None
    excel_path: str | None = None
    erpnext_project: str | None = None


class ProjectPatch(BaseModel):
    name: str | None = None
    system: str | None = None
    requestor: str | None = None
    go_live: str | None = None
    status: str | None = None
    priority: str | None = None
    progress: int | None = None
    context: str | None = None
    excel_path: str | None = None
    erpnext_project: str | None = None


class RequirementIn(BaseModel):
    id: str
    project_id: str
    area: str | None = None
    requirement: str
    priority: str = "Must Have"
    status: str = "Not Started"
    owner: str | None = None
    uat_result: str = "Not Tested"
    needs_action: int = 0
    note: str | None = None
    md_path: str | None = None


class RequirementPatch(BaseModel):
    area: str | None = None
    requirement: str | None = None
    priority: str | None = None
    status: str | None = None
    owner: str | None = None
    uat_result: str | None = None
    needs_action: int | None = None
    note: str | None = None


class IssueIn(BaseModel):
    id: str
    project_id: str
    description: str
    raised_by: str | None = None
    owner: str | None = None
    status: str = "Open"


class UATIn(BaseModel):
    id: str
    project_id: str
    req_id: str
    description: str
    tester: str | None = None
    result: str = "Not Tested"
    notes: str | None = None


class ERPNextLinkIn(BaseModel):
    req_id: str
    doctype: str
    name: str
    label: str | None = None


class AgentCompleteIn(BaseModel):
    req_id: str
    status: str
    agent: str = "codex-cli"
    notes: str = ""
    uat_result: str | None = None
    files_changed: list[str] = Field(default_factory=list)
    erpnext_writes: list[dict[str, Any]] = Field(default_factory=list)
