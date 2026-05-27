# VCL PMO — Phase 2: Real Project Management System

**Date:** 2026-05-27
**From:** Tanuj (via Claude testing pass)
**To:** Codex
**Project:** VCL-DEV-PMO-002 — VCL PMO System
**Repo:** github.com/tjharia93/vcl-pmo
**Status going in:** Phase 1 (today's build) ships a task-tracker. Phase 2 turns it into a project management system.

**Supersedes:**

- `briefs/2026-05-27_FRAPPE_NATIVE_PMO_MIGRATION.md` — original migration brief (Phase 1 spec; data model + page inventory too narrow)
- `briefs/2026-05-27_CODEX_REWORK_BRIEF.md` — UI rework (branding + no-route-out + project-scoped). Still valid for UI direction; folded into this brief.

**Keeps from Phase 1:**

- PMO Project, PMO Requirement, PMO Agent Log, PMO Sync Log doctypes
- `agent_complete`, `summary`, `oat_run`, `project_packet`, `log_sync` API methods
- The `/app/pmo` Page registration

**Drops or restructures from Phase 1:**

- PMO UAT Case → keep as the case definition; **strip out the result/tester/date/evidence fields** (those move to PMO UAT Run)
- PMO OAT Check → same pattern: definition only, runs move to PMO OAT Run
- All `frappe.set_route` link-outs in `pmo.js` (per UI rework)
- The off-brand CSS palette (per UI rework)

---

## Why a Phase 2

Phase 1 shipped six doctypes that capture *what needs to be done* and *whether a test passed once*. A project management system needs to capture:

- **What the project is** (charter, sponsor, current phase, target completion)
- **When things happen** (milestones, tasks with dates, dependencies, critical path)
- **What's at risk** (RAID — risks, assumptions, issues, dependencies)
- **How testing evolves over time** (a test isn't Pass/Fail forever — it's Pass/Fail at points in time, with evidence per run)
- **How to use the system and run the workflow** (how-to guides, workflow docs)
- **A project-scoped workspace** where all of the above are filtered to one project (Phase 1's flat UAT/OAT lists collapse everything together)

The user pattern is: open `/app/pmo` → see the portfolio → drill into a project → land in a workspace with Overview, Timeline, Open Items, Milestones, RAID, UAT, OAT, Test History, Documentation, Activity sub-pages. Each UAT/OAT Case has its own sub-page showing the run history; each Run has its own sub-page with evidence and attachments.

---

## Locked design choices (from Tanuj 2026-05-27)

1. **Timeline:** Full Gantt with dependencies — predecessors, critical path, drag-to-reschedule.
2. **Documentation storage:** PMO Document doctype in Frappe (markdown content stored in the doctype, not linked .md files in the repo).
3. **Test history:** PMO UAT Run + PMO OAT Run doctypes (one Run per execution, attached to its parent Case/Check). Recommended by Claude; locked.
4. **Work entities:** 3 levels — Milestone → Requirement → Task.

---

## Data model

### New doctypes

#### PMO Milestone

| Field | Type | Notes |
|---|---|---|
| milestone_id | Data | autoname `field:milestone_id` |
| project | Link → PMO Project | required |
| name | Data | required |
| description | Long Text | |
| target_date | Date | required |
| actual_date | Date | populated when status flips to Achieved |
| status | Select | Not Started / In Progress / At Risk / Achieved / Missed |
| owner | Link → User | rename to avoid Frappe `owner` shadow |
| weight | Percent | weighting for project progress roll-up |
| dependencies | Table → PMO Milestone Dependency | predecessor milestones |

#### PMO Milestone Dependency (child)

| Field | Type | Notes |
|---|---|---|
| predecessor_milestone | Link → PMO Milestone | required |
| dependency_type | Select | FS / SS / FF / SF (finish-start etc.) |
| lag_days | Int | positive = lag, negative = lead |

#### PMO Task

| Field | Type | Notes |
|---|---|---|
| task_id | Data | autoname `field:task_id` (e.g. T-PMO-001) |
| project | Link → PMO Project | required |
| milestone | Link → PMO Milestone | optional (loose tasks allowed) |
| requirement | Link → PMO Requirement | optional |
| title | Data | required |
| description | Long Text | |
| start_date | Date | required |
| end_date | Date | required |
| status | Select | Not Started / In Progress / Blocked / Done / Cancelled |
| owner | Link → User | rename to avoid Frappe `owner` shadow (`assignee`) |
| percent_complete | Percent | rolls up to Requirement/Milestone |
| predecessors | Table → PMO Task Dependency | |

#### PMO Task Dependency (child)

| Field | Type | Notes |
|---|---|---|
| predecessor_task | Link → PMO Task | required |
| dependency_type | Select | FS / SS / FF / SF |
| lag_days | Int | |

#### PMO RAID Item

| Field | Type | Notes |
|---|---|---|
| raid_id | Data | autoname `format:RAID-{project_short}-{####}` |
| project | Link → PMO Project | required |
| type | Select | Risk / Assumption / Issue / Dependency |
| title | Data | required |
| description | Long Text | |
| severity | Select | Critical / High / Medium / Low (risks/issues) |
| probability | Select | High / Medium / Low (risks only) |
| impact | Long Text | |
| mitigation | Long Text | |
| status | Select | Open / Mitigating / Closed / Accepted |
| owner | Link → User | named `raid_owner` |
| raised_date | Date | default Now |
| due_date | Date | review-by date |
| resolved_date | Date | populated on Closed |

#### PMO UAT Run

| Field | Type | Notes |
|---|---|---|
| run_id | Data | autoname `format:UAT-RUN-{####}` |
| uat_case | Link → PMO UAT Case | required |
| run_number | Int | auto-incremented per case (1, 2, 3 ...) |
| run_date | Datetime | default Now |
| tester | Link → User | required |
| result | Select | Pass / Fail / Blocked / Not Run |
| evidence | Long Text | markdown, screenshots embedded as attachments |
| notes | Long Text | |
| environment | Data | "Frappe Cloud production" / "local FastAPI fallback" |

Each Run record is its own sub-page in Frappe. Attachments use Frappe's per-doc attach system.

#### PMO OAT Run

Same shape as PMO UAT Run, but parent link is `oat_check` → PMO OAT Check.

#### PMO Document

| Field | Type | Notes |
|---|---|---|
| document_id | Data | autoname `format:DOC-{project_short}-{####}` |
| project | Link → PMO Project | optional — portfolio-level docs allowed |
| doc_type | Select | How-to / Workflow / SOP / Spec / Brief / Decision Log |
| title | Data | required |
| content_md | Long Text | markdown source |
| version | Data | semver-ish (1.0, 1.1, 2.0) |
| status | Select | Draft / Live / Archived |
| owner | Link → User | named `document_owner` |
| last_reviewed | Date | |

Render `content_md` server-side or via `marked.js` client-side.

### Existing doctypes — changes

#### PMO Project — add

- `charter` (Long Text, markdown) — project charter
- `kickoff_date` (Date)
- `target_completion` (Date)
- `current_phase` (Data) — "Discovery" / "Build" / "UAT" / "Live" etc.
- `sponsor` (Link → User)
- `project_manager` (Link → User)
- `project_short` (Data, unique) — used in autoname formats (e.g. "PMO", "AR", "HR", "IMP")

#### PMO Requirement — keep

No schema changes. Keep its current fields (requirement_id, project, area, requirement, priority, status, uat_result, uat_tester, uat_date, needs_action, note, md_path, erpnext_links). Role: a Requirement is a scope item that contains one or more Tasks.

**Rename** `owner` field to `requirement_owner` to stop shadowing Frappe's built-in `owner` (creator).

#### PMO UAT Case — strip down

Keep: uat_case_id, project, requirement, description.

**Remove from the Case (move to PMO UAT Run):** tester, result, date_tested, evidence, notes.

**Add to the Case:**

- `acceptance_criteria` (Long Text, markdown) — what "Pass" looks like
- `latest_result` (Select, read-only) — computed from the most recent Run (Pass / Fail / Blocked / Not Yet Run)
- `latest_run_date` (Datetime, read-only) — computed
- `run_count` (Int, read-only) — computed

#### PMO OAT Check — strip down (same pattern as UAT Case)

Keep: check_id, project, area, check.

**Remove (move to PMO OAT Run):** status, last_run, evidence, notes.

**Add to the Check:**

- `acceptance_criteria` (Long Text)
- `latest_result` (Select, read-only)
- `latest_run_date` (Datetime, read-only)
- `run_count` (Int, read-only)

#### PMO Agent Log — keep

No changes.

#### PMO Sync Log — autoname fix

Change autoname from `hash` → `format:PMO-SYNC-{YYYY}-{MM}-{####}`. Delete the junk seed row `PMO-SYNC-.#####`.

#### PMO Requirement Link — keep

No changes.

---

## Page architecture

The `/app/pmo` Page is the single product surface. Everything renders inside `.pmo-shell`. Frappe Desk forms are only an "Open in Desk" overflow — never the primary path.

### Portfolio view (default)

Top-level tabs:

- **Inbox** — cross-project open items: Tasks/Requirements/UAT Runs needing action, RAID items overdue, milestones at risk. Filter by `needs_action=1` OR status in ("Blocked", "In Review", "At Risk", "Open").
- **Projects** — card grid of all PMO Projects with status, % progress, current phase, next milestone, RAID hot count.
- **Roadmap** — portfolio-level Gantt: all projects' milestones on one timeline, swimlanes per project.
- **RAID** — portfolio-level RAID register: all open Risks/Issues across projects, sorted by severity.
- **Documentation** — portfolio-level doc library (project=null docs + cross-project SOPs).
- **Test Status** — heatmap of UAT/OAT latest results across projects.

Clicking a project card → enters the **Project Workspace** for that project. Breadcrumb at top: `Portfolio → <Project Name>` returns to portfolio.

### Project Workspace (inside the page)

Sub-tabs scoped to the selected project:

- **Overview** — charter (rendered markdown), sponsor, PM, kickoff/target dates, current phase, status, % progress (rolled up from milestones), RAID summary chips, recent activity feed (last 10 Agent Log + Sync Log entries).
- **Timeline (Gantt)** — milestones + tasks + dependencies, critical path highlighted, drag-to-reschedule, click a bar → opens a drawer with the task/milestone detail and inline edit.
- **Open Items** — Requirements (cards) + Tasks (kanban or list), grouped by status. Inline edit status / assignee / dates via drawer.
- **Milestones** — list view: name, target_date, actual_date, status, % complete (computed from child tasks), weight. Click → drawer.
- **RAID** — sub-sub-tabs Risk / Assumption / Issue / Dependency, each with its own filtered list. New-item button → modal. Click row → drawer.
- **UAT** — list of UAT Cases for this project. Each row shows: case_id, description, latest_result, latest_run_date, run_count. **Click a row → opens the Case sub-page.**
  - **UAT Case sub-page** — definition (description, acceptance_criteria) + Runs history table (run_number, run_date, tester, result, evidence-preview) + "New Run" button. Click a Run → Run sub-page.
    - **UAT Run sub-page** — full run detail, evidence markdown editor, attachments grid, tester/result/date editable.
- **OAT** — same three-level structure as UAT (Check → Check sub-page with Runs → Run sub-page).
- **Test History** — combined roll-up: all UAT Runs + OAT Runs for this project, filterable by date / tester / result.
- **Documentation** — PMO Documents scoped to this project, grouped by doc_type. Click → renders markdown in-page with TOC, "Edit" toggles into a markdown editor.
- **Activity** — Agent Log + Sync Log for this project, chronological.

### Sub-page model

A "sub-page" inside the PMO Page is a `this.view = "project:<id>:uat:<case_id>"` (etc.) state in the JS shell. No Frappe route change. Breadcrumbs render the path: `Portfolio → <Project> → UAT → UAT-PMO-001 → Run #3`. Browser back button works via `history.pushState`.

The "Open in Desk" overflow on any record opens the standard Frappe form in a new tab as an escape hatch for power edits — but the default flow stays inside the PMO Page.

---

## API additions

New whitelisted methods in `vcl_pmo_doctypes/api.py`:

| Method | Inputs | Returns |
|---|---|---|
| `project_overview(project_id)` | project id | Project meta + milestones (with % complete) + RAID counts by type/severity + UAT/OAT latest-result roll-up + recent activity |
| `project_gantt(project_id)` | project id | Tasks + milestones + dependencies in Gantt-renderable shape |
| `case_history(case_id, kind)` | case/check id, kind=uat/oat | All Runs for a case, ordered by run_date desc |
| `new_run(case_id, kind, result, tester, evidence, notes, environment)` | as named | Inserts PMO UAT Run / PMO OAT Run, returns new run_id and updated latest_result on the Case |
| `recompute_latest(case_id, kind)` | case/check id, kind | Reads runs, updates latest_result/latest_run_date/run_count on the Case |
| `raid_register(project_id, type)` | project id, type filter (optional) | Filtered RAID items |
| `documents_for(project_id)` | project id (nullable for portfolio) | PMO Documents grouped by doc_type |
| `mark_milestone(milestone_id, status, actual_date)` | as named | Updates milestone, recomputes project % progress |
| `link_task(task_id, predecessor_task_id, type, lag_days)` | as named | Adds a PMO Task Dependency row |

Permissions: all behind `_require_pmo_user()`. Keep the existing `agent_complete`, `summary`, `oat_run`, `project_packet`, `log_sync` — but extend `summary` to also return RAID counts and milestone roll-ups.

### Hooks

`vcl_pmo_doctypes/hooks.py` — wire `on_update` on PMO UAT Run / PMO OAT Run to call `recompute_latest` for the parent Case/Check, so `latest_result` always reflects the most recent Run without manual maintenance.

---

## UI rework (folded in from the earlier rework brief)

The three reworks from `briefs/2026-05-27_CODEX_REWORK_BRIEF.md` still apply to Phase 2 — read that brief as authoritative for:

- **Branding:** VCL Brand v1.1 tokens (Navy `#1D2766`, Sage `#5A9367`, Green `#1B7A45`, Amber `#B86B00`, restricted Red, Calibri for body, Courier New for code). Full token table in that brief.
- **No route-outs:** every interaction stays in `.pmo-shell` via drawer/modal/inline edit. `frappe.set_route` allowed only on the "Open in Desk" overflow and the admin-only Sync Log drilldown.
- **Project-scoped pages:** confirmed and expanded in this Phase 2 brief (full project workspace, not just per-project UAT/OAT).

---

## Migration plan (from Phase 1 to Phase 2)

Order matters. Do in branches with separate PRs so each can be reviewed:

**PR 1 — Schema additions (additive only, no data loss):**

- Add new doctypes: PMO Milestone (+ Dependency), PMO Task (+ Dependency), PMO RAID Item, PMO UAT Run, PMO OAT Run, PMO Document
- Add new fields to PMO Project (charter, kickoff_date, target_completion, current_phase, sponsor, project_manager, project_short)
- Rename `PMO Requirement.owner` → `requirement_owner`, `PMO OAT Check.owner` → `oat_owner` (use Property Setter pattern per memory)
- Fix PMO Sync Log autoname to `format:PMO-SYNC-{YYYY}-{MM}-{####}`; delete the junk seed row
- Migrate existing UAT/OAT records: for each PMO UAT Case with a non-Not-Tested result, create a corresponding PMO UAT Run and clear the result fields on the Case. Same for OAT Checks.
- Add new API methods (above)

**PR 2 — Page restructure (replaces pmo.js + pmo.css):**

- Apply VCL Brand v1.1 in `pmo.css`
- Rewrite `pmo.js` shell with: portfolio view + project workspace + sub-page routing via `this.view` state + breadcrumbs
- Build Gantt component (consider DHTMLX Gantt, Frappe Gantt, or vanilla SVG — Frappe Gantt is the Frappe-native option and matches the stack)
- Build drawer + modal patterns for in-page edits
- Wire every former `frappe.set_route` to its in-page equivalent
- Build Documentation render path (use `marked.js` via Frappe's existing inclusion or load from CDN)

**PR 3 — Seed data for Phase 2:**

- Seed PMO Project meta (sponsor, PM, dates, current_phase) for the 4 existing projects
- Seed a sample Milestone + 2-3 Tasks + 1 RAID Item for VCL-DEV-PMO-002 so the Gantt and RAID pages aren't empty on first load
- Seed 1-2 PMO Documents (e.g. "How to mark a UAT Run", "PMO weekly cadence workflow")

**PR 4 — Cleanup (after Tanuj signs off):**

- Delete the outer duplicated `vcl_pmo_doctypes/doctype/` directory
- Tighten `agent_complete` Comment insert: drop `ignore_permissions=True` or whitelist allowed reference doctypes
- De-duplicate PMO Agent Log status Select options (pick lowercase OR Title Case, not both)

---

## Acceptance criteria for Phase 2

The Phase 2 build passes when, against a freshly-pulled branch on Frappe Cloud:

1. `/app/pmo` paints with VCL Brand v1.1 — no off-brand hexes, Calibri body, brand-token chips.
2. Portfolio tabs include: Inbox, Projects, Roadmap, RAID, Documentation, Test Status. Each renders without route changes.
3. Clicking a project card opens a project workspace inside the page with sub-tabs: Overview, Timeline, Open Items, Milestones, RAID, UAT, OAT, Test History, Documentation, Activity.
4. The Timeline tab renders a Gantt with milestones + tasks + dependencies. Critical path is visible. Drag-to-reschedule updates the task end_date via API.
5. The UAT tab lists Cases. Click a Case → sub-page with the Case definition + Runs history table + New Run button. New Run → modal → on submit, creates a PMO UAT Run AND updates the Case's `latest_result` / `latest_run_date` / `run_count` via the `on_update` hook.
6. Each Run has its own sub-page accessible by clicking it from the Case sub-page. Run sub-page shows full evidence, attachments, tester, environment, run_date, result.
7. OAT pattern works identically (Check → Check sub-page → Run sub-page).
8. RAID tab has Risk/Assumption/Issue/Dependency sub-tabs, each with its own filtered list and "New" modal.
9. Documentation tab lists PMO Documents grouped by doc_type. Clicking a document renders the markdown in-page; "Edit" toggles into a markdown editor that saves back to the doctype.
10. Breadcrumbs render correctly (`Portfolio → <Project> → UAT → UAT-PMO-001 → Run #3`). Browser back button navigates the sub-page stack.
11. No `frappe.set_route` calls anywhere in the primary user flows (UAT marking, Task editing, RAID creation, Documentation edits). The only allowed routes are the "Open in Desk" overflow and the Sync Log admin drilldown.
12. Re-running the existing UAT-PMO-* and OAT-PMO-* cases from inside the page works: I (Claude) or Tanuj can mark a new Run Pass/Fail with evidence without ever leaving `/app/pmo`.

---

## Out of scope for Phase 2

- n8n Excel mirror — PMO-002-04 separate workstream.
- Time tracking / actual-hours-per-task — defer.
- Resource allocation / capacity planning — defer.
- Email notifications on RAID severity changes — defer to Phase 3.
- Public/external sharing of project status pages — defer.
- Integration with ERPNext Project doctype (the `linked_erpnext_project` field exists; deeper sync is Phase 3).

---

## Open questions for Tanuj (low priority — defaults stated)

- **Gantt library**: default to Frappe Gantt (in-Frappe, vanilla, matches stack). Flag if you'd prefer DHTMLX or a custom SVG.
- **Markdown rendering**: default to `marked.js` loaded from CDN. Flag if you'd prefer a Frappe-side server render (Python `markdown` lib) for offline safety.
- **`project_short` values**: default to "PMO" / "AR" / "HR" / "IMP" based on existing project IDs. Flag if you want a different convention.
- **RAID severity vs probability matrix display**: default to a simple table. Flag if you want a 5×5 heatmap.

---

## Repo path summary

| File | Action |
|---|---|
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_milestone/` | New |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_milestone_dependency/` | New (child) |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_task/` | New |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_task_dependency/` | New (child) |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_raid_item/` | New |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_uat_run/` | New |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_oat_run/` | New |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_document/` | New |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_project/pmo_project.json` | Add fields (charter, kickoff_date, target_completion, current_phase, sponsor, project_manager, project_short) |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_requirement/pmo_requirement.json` | Rename `owner` → `requirement_owner` |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_uat_case/pmo_uat_case.json` | Strip result/tester/date/evidence; add acceptance_criteria + latest_* read-only |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_oat_check/pmo_oat_check.json` | Strip status/last_run/evidence; add acceptance_criteria + latest_* read-only |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_sync_log/pmo_sync_log.json` | autoname → `format:PMO-SYNC-{YYYY}-{MM}-{####}` |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.css` | Rewrite to VCL Brand v1.1 |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.js` | Full rewrite: portfolio + project workspace + sub-pages + Gantt + drawers |
| `vcl_pmo_doctypes/api.py` | Add new methods (above); keep existing |
| `vcl_pmo_doctypes/hooks.py` | Add `on_update` for PMO UAT Run + PMO OAT Run → call recompute_latest |
| `vcl_pmo_doctypes/doctype/` (outer duplicate) | Delete entirely |
| `briefs/2026-05-27_PMO_PHASE2_PM_SYSTEM_BRIEF.md` | This brief (already committed) |
