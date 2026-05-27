// Shared seed data for VCL PMO prototypes
// Used by mix-a/b/c/d. Brand v1.1 colours assumed.

window.VCL = window.VCL || {};

VCL.PROJECTS = [
  {
    id: "VCL-DEV-HR-001",
    name: "HR & Payroll Module",
    system: "ERPNext v16 + FastAPI Intranet",
    requestor: "Head of HR / CFO",
    go_live: "2026-05-27",
    status: "Live",
    priority: "High",
    progress: 100,
    color: "green"
  },
  {
    id: "VCL-DEV-PMO-002",
    name: "VCL PMO System",
    system: "FastAPI + SQLite + ERPNext links",
    requestor: "CFO",
    go_live: "2026-06-03",
    status: "In Build",
    priority: "Critical",
    progress: 15,
    color: "amber"
  },
  {
    id: "VCL-DEV-IMP-001",
    name: "Imports Portal",
    system: "Frappe custom app",
    requestor: "CFO",
    go_live: "2026-07-15",
    status: "Active",
    priority: "High",
    progress: 25,
    color: "blue"
  },
  {
    id: "VCL-DEV-AR-001",
    name: "ERP↔QBO AR Alignment",
    system: "Finance reconciliation",
    requestor: "CFO",
    go_live: "2026-06-30",
    status: "Active",
    priority: "High",
    progress: 60,
    color: "blue"
  }
];

VCL.REQUIREMENTS = [
  { id: "HR-001", project: "VCL-DEV-HR-001", area: "Setup",         requirement: "ERPNext company / Holiday / Income Tax Slab for VCL/BIL/BVL",   priority: "Must Have", status: "Done",        owner: "codex-cli", uat: "Pass" },
  { id: "HR-002", project: "VCL-DEV-HR-001", area: "Payroll",       requirement: "Kenya statutory Salary Components + Structures",                 priority: "Must Have", status: "In Review",   owner: "codex-cli", uat: "Pass", needs_action: true, note: "Fix formulas on VCL/BIL/BVL before June cycle" },
  { id: "HR-003", project: "VCL-DEV-HR-001", area: "Master",        requirement: "Employee master — 96 perm + 12 casuals + 3 leavers",             priority: "Must Have", status: "Done",        owner: "codex-cli", uat: "Pass" },
  { id: "HR-009", project: "VCL-DEV-HR-001", area: "Payroll",       requirement: "Payroll Entry + Salary Slip generation",                         priority: "Must Have", status: "Done",        owner: "codex-cli", uat: "Pass", needs_action: true, note: "97 May slips ready for sign-off" },
  { id: "HR-010", project: "VCL-DEV-HR-001", area: "Compliance",    requirement: "Statutory compliance — NSSF/SHIF/EHL/PAYE",                      priority: "Must Have", status: "Done",        owner: "codex-cli", uat: "Pass", note: "0.49% variance vs Jitu BB" },
  { id: "HR-011", project: "VCL-DEV-HR-001", area: "Print",         requirement: "VCL-branded Salary Slip print format",                           priority: "Must Have", status: "Done",        owner: "codex-cli", uat: "Pass" },
  { id: "HR-013", project: "VCL-DEV-HR-001", area: "Leave",         requirement: "LWP / Leave Application integration",                            priority: "Should",    status: "Done",        owner: "codex-cli", uat: "Pass" },
  { id: "IMP-001", project: "VCL-DEV-IMP-001", area: "Mirror",       requirement: "SUPP → ERP daily mirror",                                        priority: "Must Have", status: "Done",        owner: "claude-code", uat: "Pass" },
  { id: "IMP-002", project: "VCL-DEV-IMP-001", area: "Workflow",     requirement: "PR / approval workflow",                                         priority: "Must Have", status: "In Progress", owner: "claude-code", uat: "Not Tested" },
  { id: "IMP-003", project: "VCL-DEV-IMP-001", area: "Portal",       requirement: "Frappe custom app scaffold",                                     priority: "Should",    status: "Not Started", owner: "—",         uat: "Not Tested" },
  { id: "AR-001",  project: "VCL-DEV-AR-001",  area: "Reconciliation",requirement: "All 4,646 2025 invoices submitted",                              priority: "Must Have", status: "Done",        owner: "claude-code", uat: "Pass" },
  { id: "AR-002",  project: "VCL-DEV-AR-001",  area: "Reconciliation",requirement: "194 WHT JEs mirrored",                                           priority: "Must Have", status: "Done",        owner: "claude-code", uat: "Pass" },
  { id: "AR-003",  project: "VCL-DEV-AR-001",  area: "Reconciliation",requirement: "1,233 payments mirrored",                                        priority: "Must Have", status: "Done",        owner: "claude-code", uat: "Pass" },
  { id: "AR-005",  project: "VCL-DEV-AR-001",  area: "Linking",       requirement: "SI↔SO link-and-close matcher",                                   priority: "Must Have", status: "Blocked",     owner: "claude-code", uat: "Not Tested", needs_action: true, note: "Waiting on 5 CFO decisions" },
  { id: "PMO-001", project: "VCL-DEV-PMO-001", area: "Build",         requirement: "FastAPI + SQLite + vanilla SPA",                                 priority: "Critical",  status: "In Progress", owner: "codex-cli",  uat: "Not Tested" }
];

VCL.ISSUES = [
  { id: "ISS-001", project: "VCL-DEV-HR-001", description: "PAYE rounding mismatch on Joan trial run", raised_by: "Joan", date: "2026-05-26", status: "Open" },
  { id: "ISS-002", project: "VCL-DEV-AR-001", description: "Afapack 715K QBO gap not yet reconciled", raised_by: "CFO", date: "2026-05-22", status: "Open" }
];

VCL.FEED = [
  { ts: "07:45", actor: "codex-cli", verb: "marked", target: "HR-002", to: "In Review" },
  { ts: "06:30", actor: "system",    verb: "dispatched", target: "HR-002", to: "agent" },
  { ts: "06:12", actor: "codex-cli", verb: "marked", target: "HR-009", to: "Done" },
  { ts: "Yesterday 17:00", actor: "tanuj", verb: "approved", target: "HR-011", to: "" },
  { ts: "Yesterday 16:20", actor: "claude-code", verb: "marked", target: "IMP-001", to: "Done" }
];

VCL.STATUS_ORDER = ["Not Started", "In Progress", "In Review", "Blocked", "Done"];

VCL.STATUS_COLOUR = {
  "Not Started": "muted",
  "In Progress": "blue",
  "In Review":   "amber",
  "Blocked":     "red",
  "Done":        "green"
};

// load + persist mutations across reloads, per-mix
VCL.loadState = function(mix){
  const raw = localStorage.getItem("vcl_pmo_state_" + mix);
  if(!raw) return null;
  try { return JSON.parse(raw); } catch(e){ return null; }
};
VCL.saveState = function(mix, reqs){
  localStorage.setItem("vcl_pmo_state_" + mix, JSON.stringify(reqs));
};
VCL.getReqs = function(mix){
  const saved = VCL.loadState(mix);
  return saved || JSON.parse(JSON.stringify(VCL.REQUIREMENTS));
};
