# VCL-DEV-PMO-002 — Technical Brief

**Project:** `VCL-DEV-PMO-002` (VCL PMO System)
**System:** Frappe-native PMO + n8n Excel mirror
**App URL:** https://vimitconverters.frappe.cloud/app/pmo
**Repo:** github.com/tjharia93/vcl-pmo (auto-deploys on push to `main`)
**Current phase:** Phase 2 Build (Plan & Shift module live; Slack integration shipped today)
**Kickoff:** 2026-05-27 · **Target completion:** 2026-06-07
**Active milestone:** `MS-PMO-001` Phase 2 PM System Foundation, due 2026-06-02

---

## 1. Architecture

```
ERPNext (Frappe Cloud) ──[doctype writes]──> PMO doctypes
        │                                         │
        ├──[on_update]── webhooks.enqueue_excel_sync ──> n8n ──> Excel mirror
        │                                         │
        └──[dispatch_shift]── HTTP webhook ──> n8n ──> claude / codex CLI runner
                                                  │
                                                  └── send_plan_to_slack ──> Slack files API ──> #ai-pmo-plans
```

**Two-anchor pattern:** Frappe is the source of truth. Excel (`/mnt/vimit/apps/14. AI PMO/projects/VCL PMO System/VCL PMO System PMO.xlsx`) is a downstream mirror managed by n8n. No bidirectional writes from Excel.

---

## 2. Doctypes (in `VCL PMO Doctypes` module)

| Doctype | Purpose | Key fields |
|---|---|---|
| `PMO Project` | Top-level container | `project_id`, `project_name`, `project_short`, `system`, `status`, `priority`, `progress`, `current_phase`, `target_completion` |
| `PMO Requirement` | Functional requirement | `requirement_id`, `area`, `requirement`, `priority`, `status`, `requirement_owner`, `uat_result`, `needs_action` |
| `PMO Milestone` | Time-boxed delivery point | `milestone_id`, `milestone_name`, `target_date`, `status`, `weight` |
| `PMO Task` | Scheduled work | `task_id`, `title`, `start_date`, `end_date`, `assignee`, `percent_complete`, `status` |
| `PMO Task Dependency` | Task FS / SS / FF / SF links | `predecessor_task_id`, `type`, `lag_days` |
| `PMO Milestone Dependency` | Milestone graph | — |
| `PMO RAID Item` | Risk / Assumption / Issue / Dependency | `raid_id`, `type`, `severity`, `probability`, `status`, `raid_owner`, `due_date` |
| `PMO Plan` | Planning proposal | `plan_id`, `title`, `description`, `planner`, `status` (Draft / Proposed / Allocated / Executed / Closed), `proposed_items[]`, `approved_by`, `approved_at` |
| `PMO Plan Item` (child) | One proposed item | `item_type` (Milestone / Requirement / Task / RAID / Shift), `title`, `description`, `metadata` (JSON), `needs_uat`, `needs_oat`, `assignee_hint`, `promoted_to_doctype`, `promoted_to_name`, `promoted_at` |
| `PMO Shift` | Allocated work to a single agent | `shift_id`, `title`, `description`, `shift_type` (Planning / Execution / Review / Test), `assigned_to` (claude / codex / human), `status` (Proposed / Allocated / In Progress / Done / Blocked / Cancelled), `planned_start/end`, `actual_start/end`, `requires_uat`, `requires_oat`, `uat_case`, `oat_check`, `linked_plan`, `linked_requirement`, `linked_milestone`, `linked_task`, `output_notes` |
| `PMO UAT Case` | UAT acceptance case | `uat_case_id`, `project`, `requirement`, **`bucket`**, **`linked_shift`**, **`linked_task`**, **`linked_plan`**, `description`, `acceptance_criteria`, `latest_result`, `latest_run_date`, `run_count` |
| `PMO OAT Check` | Operational readiness check | `check_id`, `project`, `area`, **`bucket`**, **`linked_shift`**, **`linked_task`**, **`linked_plan`**, `check`, `acceptance_criteria`, `latest_result`, `latest_run_date`, `run_count` |
| `PMO UAT Run` | One UAT execution log | `run_number`, `run_date`, `tester`, `result`, `evidence`, `notes`, `environment` |
| `PMO OAT Run` | One OAT execution log | — |
| `PMO Document` | Repo of markdown docs scoped to project | `title`, `doc_type`, `version`, `status` |
| `PMO Note` | Inbox + per-project notes | `title`, `content_md`, `note_type`, `status` |
| `PMO Agent Log` | Audit trail of agent_complete calls | — |
| `PMO Sync Log` | Excel sync direction + status | — |

**Bold = added 2026-05-28 by SHIFT-0004** (UAT/OAT bucketing).

---

## 3. API methods (`vcl_pmo_doctypes.api`)

All `@frappe.whitelist()`-gated to System Manager or `PMO User` role.

### Read

- `summary()` — KPI counters for the portfolio
- `project_packet(project_id)` — full project bundle (project + requirements + milestones + tasks + raid + uat_cases + oat_checks + documents)
- `project_overview(project_id)`
- `project_gantt(project_id)`
- `project_plans(project_id)` / `project_shifts(project_id, assignee, status_filter)`
- `agent_shift_queue(agent, project_id, status_filter)`
- `plan_detail(plan_id)`
- `case_history(case_id, kind)` — UAT or OAT run log
- `raid_register(project_id, type)`
- `documents_for(project_id)` / `notes_for(project_id, include_inbox)`

### Write

- `create_note` / `assign_note`
- `create_plan(project_id, title, description, items)`
- `add_plan_items(plan_id, items)`
- `allocate_plan_items(plan_id, item_indices, assignee, planned_start, planned_end)` — bulk-promote items to Milestone / Requirement / Task / RAID / Shift; auto-creates UAT Case / OAT Check when `needs_uat` / `needs_oat` ticked
- `start_shift(shift_id)` / `complete_shift(shift_id, output_notes, uat_result, oat_result)` / `block_shift(shift_id, reason)`
- `dispatch_shift(shift_id, set_in_progress=True)` — fires the n8n webhook (`pmo_n8n_dispatch_url` in `site_config.json`)
- `send_plan_to_slack(plan_id, channel=None, comment=None)` — renders the plan as a VCL-branded A4 PDF and uploads to Slack via `files.getUploadURLExternal` flow (added 2026-05-28 by SHIFT-0003)
- `mark_milestone(milestone_id, status, actual_date)`
- `link_task(task_id, predecessor_task_id, type, lag_days)`
- `new_run(case_id, kind, result, tester, evidence, notes, environment)`
- `agent_complete(req_id, status, agent, notes, uat_result, files_changed, erpnext_writes)` — the completion webhook used by the agent runner

### Internal helpers

- `_spawn_from_plan_item(plan, item, project_name, metadata, assignee)` — promotion target factory
- `_autocreate_uat_for_promoted` / `_autocreate_oat_for_promoted` — auto-create UAT/OAT for plan-item promotions, populates `bucket` + `linked_plan` + `linked_task`
- `_vcl_brand_html(plan, items, project)` — branded HTML template for the Slack PDF
- `_render_plan_pdf(plan_id)` — wraps `frappe.utils.pdf.get_pdf`

---

## 4. Doctype controllers

- **`PMOShift.before_save`** — if `requires_uat=1` and `uat_case` empty, auto-creates `UAT-<shift_id>` and stamps `bucket=shift_id`, `linked_shift=shift.name`, `linked_plan=shift.linked_plan` on it. Backfills the same fields on a pre-existing case. Mirror logic for OAT.

---

## 5. UI — single page at `/app/pmo`

Source: `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.{js,css,py,json}`.

**Tabs (sub-tab strip):** Overview · Timeline · Open Items · Notes · Plans · Shifts · Milestones · RAID · UAT · OAT · Test History · Documentation · Activity.

**Plan sub-page** — title, status pill, item count, markdown description; items table with row-level checkboxes; actions: Add Item, **Send PDF to Slack**, Allocate selected to Claude / Codex / Human.

**Shift sub-page** — header + two-col card layout; actions per status: Start, Execute via n8n (for claude/codex), Complete, Block, Open in Desk.

**UAT / OAT tables** (`caseTable` helper) — grouped by `bucket` with a header row showing the bucket name + pass/fail/blocked/not-run counts. Sort order: bucket name ascending; `Ungrouped` last.

**Route state (SHIFT-0001 fix in commit `22f68fa`):** every navigation now `pushState`s a unique fragment (`/app/pmo#p/<project>/plans/<plan>` shape). `popstate` rebuilds `this.state` and re-renders. F5 and deep-link paste both land on the same sub-page.

---

## 6. Hook events (`hooks.py`)

```python
doc_events = {
  "PMO Project / Requirement / Milestone / Task / RAID Item / UAT Case / OAT Check": {
      "on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"
  },
  "PMO UAT Run / OAT Run": {
      "on_update": [
          "vcl_pmo_doctypes.webhooks.recompute_uat_latest" | "recompute_oat_latest",
          "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"
      ]
  },
  "PMO Document / Note / Plan / Shift": { "on_update": "...enqueue_excel_sync" },
}
```

---

## 7. n8n contract

### Dispatch shift (Frappe → n8n)

```
POST <pmo_n8n_dispatch_url>
{
  "event": "pmo.shift.dispatch",
  "shift_id": "SHIFT-0003",
  "shift_name": "...",
  "title": "...",
  "description": "...",
  "assigned_to": "claude" | "codex" | "human",
  "shift_type": "Planning|Execution|Review|Test",
  "project": "VCL-DEV-PMO-002",
  "requires_uat": 0|1, "requires_oat": 0|1,
  "uat_case": "UAT-SHIFT-XXXX", "oat_check": "OAT-SHIFT-XXXX",
  "linked_plan": "PLAN-XXXX", "linked_requirement": "...",
  "linked_milestone": "...", "linked_task": "...",
  "complete_shift_callback": "/api/method/vcl_pmo_doctypes.api.complete_shift"
}
```

### Completion (agent runner → Frappe)

```
POST https://vimitconverters.frappe.cloud/api/method/vcl_pmo_doctypes.api.complete_shift
{
  "shift_id": "SHIFT-0003",
  "output_notes": "...",     # markdown
  "uat_result": "Pass" | "Fail" | "Blocked",
  "oat_result": "Pass" | "Fail" | "Blocked"
}
```

If `uat_result` / `oat_result` is supplied AND the shift has `uat_case` / `oat_check`, the API auto-logs a `PMO UAT Run` / `PMO OAT Run`.

### Excel sync

`webhooks.enqueue_excel_sync` debounces and pushes diffs to n8n which rewrites the per-project workbook in the share. No reverse flow.

---

## 8. `site_config.json` keys

| Key | Required? | Set by | Purpose |
|---|---|---|---|
| `pmo_n8n_dispatch_url` | for shift dispatch | bench shell | n8n webhook URL |
| `pmo_slack_bot_token` | for Slack PDF push | bench shell | `xoxb-…` bot token, `chat:write` + `files:write` |
| `pmo_slack_plans_channel` | optional | bench shell | defaults to `C0B5DA141MM` (#ai-pmo-plans) |

```bash
bench --site vimitconverters.frappe.cloud set-config pmo_slack_bot_token "xoxb-XXX"
bench --site vimitconverters.frappe.cloud set-config pmo_n8n_dispatch_url "https://n8n.vcl/..."
```

---

## 9. Plans / Shifts state (as of 2026-05-28 21:30)

| Plan | Title | Status | Spawned shift |
|---|---|---|---|
| PLAN-0001 | UAT/OAT items grouped per testing session | Allocated | SHIFT-0004 |
| PLAN-0002 | Slack Integration | Allocated | SHIFT-0003 |
| PLAN-0003 | Scheduled Plan Runs | Allocated | SHIFT-0002 |
| PLAN-0004 | Check all Pages Work | Allocated | SHIFT-0001 |

| Shift | Owner | Status | UAT / OAT | Notes |
|---|---|---|---|---|
| SHIFT-0001 | codex | Done pending UAT (commit `22f68fa`) | UAT + OAT pending | Route-state stabilized, 9 popstate sites; requirement IDs cleaned up |
| SHIFT-0002 | codex | Allocated | UAT + OAT pending | Planning shift — design spec only, see Codex brief |
| SHIFT-0003 | claude | In Progress | UAT + OAT pending | Needs `pmo_slack_bot_token` in site_config before end-to-end UAT can run |
| SHIFT-0004 | claude | Done | n/a (`requires_uat=0`, `requires_oat=0`) | UAT/OAT bucket fields live; UI grouping live; backfill of old cases happens on next shift save |

---

## 10. Open requirements

| ID | Area | Requirement | Status |
|---|---|---|---|
| PMO-002-04 | Excel sync | n8n-managed read/write per-project Excel mirror | In Review |
| PMO-002-07 | ERPNext write | Task/status mirror only; no financial document submission | In Review |

(8 of 10 already Done.)

---

## 11. Acceptance criteria — open shifts

### SHIFT-0001 (UAT pending)
1. Back from any sub-page lands on the parent tab, not "Page not available".
2. F5 on a sub-page reloads the same sub-page.
3. Pasted deep-link URL renders the target view.
4. Existing Portfolio chip + breadcrumbs continue to work.

### SHIFT-0002 (Planning — design output)
The deliverable is a markdown spec answering: trigger, capacity probe, reviewer payload, approval surface, action-on-approve, failure modes. Filename: `briefs/2026-05-28_SCHEDULED_PLAN_REVIEW_SPEC.md`. UAT = Tanuj reads the spec and confirms all six points covered.

### SHIFT-0003 (UAT pending)
1. `pmo_slack_bot_token` installed and bot invited to `#ai-pmo-plans`.
2. Click **Send PDF to Slack** on a plan → success toast with file permalink within 10s.
3. PDF opens cleanly on desktop, Boox Air 5, reMarkable.
4. Brand: navy `#1F4E79`, A4 portrait, 14pt body, plan title in 24pt, item table with #/Type/Title&Desc/Hint/Tests/Promoted columns.
5. Initial Slack comment contains plan title, ID, project, status, and a link back to `/app/pmo`.

### SHIFT-0004 (done)
Schema migrated. `caseTable` renders bucket groups. Verified locally; no UAT/OAT required per shift definition.

---

## 12. Completion webhook (for agents marking own shifts done)

```python
mcp__vcl-erpnext__run_method(
  method="vcl_pmo_doctypes.api.complete_shift",
  args={"shift_id": "SHIFT-0003", "output_notes": "<markdown>",
        "uat_result": "Pass", "oat_result": "Pass"})
```

This: flips status to Done, stamps `actual_end`, and (if the shift has linked UAT/OAT) logs a `PMO UAT Run` and `PMO OAT Run` with `result=Pass`.

---

## 13. Next-up tasks (PMO human owns)

1. Install Slack bot + drop `pmo_slack_bot_token` into `site_config.json`. Invite bot to `#ai-pmo-plans`.
2. UAT walk SHIFT-0001 (back-nav). On Pass → `complete_shift(SHIFT-0001, ..., "Pass", "Pass")`.
3. UAT-test SHIFT-0003 (Slack PDF). On Pass → `complete_shift(SHIFT-0003, ..., "Pass", "Pass")`.
4. Hand SHIFT-0002 to Codex with the brief at `briefs/2026-05-28_CODEX_SHIFT-0001_AND_SHIFT-0002_BRIEF.md`.
5. Once all four shifts Done → mark `MS-PMO-001` Done (`mark_milestone("MS-PMO-001", "Done", "2026-05-XX")`).
