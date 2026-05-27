from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Text, func

from .database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    system = Column(Text)
    requestor = Column(Text)
    go_live = Column(Date)
    status = Column(Text, default="Active")
    priority = Column(Text, default="High")
    progress = Column(Integer, default=0)
    context = Column(Text)
    excel_path = Column(Text)
    erpnext_project = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime)


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.id"))
    area = Column(Text)
    requirement = Column(Text, nullable=False)
    priority = Column(Text)
    status = Column(Text, default="Not Started")
    owner = Column(Text)
    uat_result = Column(Text, default="Not Tested")
    uat_tester = Column(Text)
    uat_date = Column(Date)
    needs_action = Column(Integer, default=0)
    note = Column(Text)
    md_path = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime)


class ERPNextLink(Base):
    __tablename__ = "erpnext_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_id = Column(Text, ForeignKey("requirements.id"))
    project_id = Column(Text, ForeignKey("projects.id"))
    doctype = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    label = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.id"))
    description = Column(Text)
    raised_by = Column(Text)
    date_raised = Column(Date)
    owner = Column(Text)
    status = Column(Text, default="Open")
    resolution = Column(Text)
    date_resolved = Column(Date)
    erpnext_issue = Column(Text)


class UATCase(Base):
    __tablename__ = "uat_cases"

    id = Column(Text, primary_key=True)
    project_id = Column(Text, ForeignKey("projects.id"))
    req_id = Column(Text, ForeignKey("requirements.id"))
    description = Column(Text)
    tester = Column(Text)
    result = Column(Text, default="Not Tested")
    date_tested = Column(Date)
    notes = Column(Text)


class AgentLog(Base):
    __tablename__ = "agent_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    req_id = Column(Text)
    project_id = Column(Text)
    agent = Column(Text)
    status = Column(Text)
    notes = Column(Text)
    files = Column(Text)
    ts = Column(DateTime, server_default=func.current_timestamp())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, server_default=func.current_timestamp())
    actor = Column(Text)
    verb = Column(Text)
    target = Column(Text)
    diff = Column(Text)


class SyncState(Base):
    __tablename__ = "sync_state"

    anchor = Column(Text, primary_key=True)
    last_pulled = Column(DateTime)
    last_pushed = Column(DateTime)
    last_error = Column(Text)
    status = Column(Text)


class PreviewCache(Base):
    __tablename__ = "preview_cache"

    key = Column(Text, primary_key=True)
    payload = Column(Text)
    updated_at = Column(DateTime, server_default=func.current_timestamp())
