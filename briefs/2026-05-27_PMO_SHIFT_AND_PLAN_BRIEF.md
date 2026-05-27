# VCL PMO — Shift & Plan Module

**Date:** 2026-05-27
**Branch:** `claude/shift-plan`
**Built by:** Claude
**Repo:** github.com/tjharia93/vcl-pmo
**Scope:** Add a planning + shift-work loop on top of the Phase 2 PMO so any agent (Claude / Codex / human) can read its queue, execute, and update status — and plans can propose Milestones / Requirements / Tasks / RAID / Shifts in one go with `needs_uat` / `needs_oat` checkboxes that auto-create test records on allocation.

---

## What ships in this branch

### New doctypes (3)

- **PMO Plan** — parent. Fields: `plan_id`, `project`, `title`, `description`, `planner`, `status` (Draft / Proposed / Allocated / Executed / Closed), `proposed_items` (Table), `created_at`, `approved_by`, `approved_at`.
- **PMO Plan Item** — child table. Fields: `item_type` (Milestone / Requirement / Task / RAID / Shift), `title`, `description`, `metadata` (Long Text, JSON for type-specific fields), `needs_uat` (Check), `needs_oat` (Check), `assignee_hint` (unassigned / claude / codex / human), `promoted_to_doctype`, `promoted_to_name`, `promoted_at`.
- **PMO Shift** — actual work assignment. Fields: `shift_id`, `project`, `title`, `description`, `shift_type` (Planning / Execution / Review / Test), `assigned_to` (claude / codex / human), `status` (Proposed / Allocated / In Progress / Done / Blocked / Cancelled), `planned_start`, `planned_end`, `actual_start`, `actual_end`, `requires_uat`, `requires_oat`, `uat_case` (Link), `oat_check` (Link), `output_notes`, `linked_plan`, `linked_requirement`, `linked_milestone`, `linked_task`.

### New API methods (`vcl_pmo_doctypes.api`)

- `create_plan(project_id, title, description, items)` — create a plan with proposed items.
- `add_plan_items(plan_id, items)` — append items to an existing plan.
- `plan_detail(plan_id)` — fetch plan + items with parsed metadata.
- `allocate_plan_items(plan_id, item_indices, assignee, planned_start, planned_end)` — bulk-promote selected items into their target doctypes; for `item_type=Shift` an `assigned_to` is required; for any item with `needs_uat`/`needs_oat` ticked, auto-creates a `PMO UAT Case` / `PMO OAT Check` and (for Shift) links them on the new shift.
- `project_plans(project_id)` — list plans for a project.
- `project_shifts(project_id, assignee=None, status_filter=None)` — list shifts for a project, optionally filtered by agent + status.
- `agent_shift_queue(agent, project_id=None, status_filter=None)` — read the work queue for a specific agent. Default returns Allocated + In Progress.
- `start_shift(shift_id)` — flip status to In Progress, stamp `actual_start`.
- `complete_shift(shift_id, output_notes, uat_result=None, oat_result=None)` — flip status to Done, stamp `actual_end`; if `uat_result`/`oat_result` supplied AND the shift has a linked `uat_case`/`oat_check`, auto-logs a `PMO UAT Run` / `PMO OAT Run` against the linked case/check.
- `block_shift(shift_id, reason)` — flip status to Blocked, append the reason to `output_notes`.
- `dispatch_shift(shift_id, set_in_progress=True)` — fire an outbound webhook to n8n with the full shift payload (see n8n contract below).

### Doctype controllers (auto-behaviours)

- `PMOShift.before_save`: if `requires_uat=1` and `uat_case` is empty, auto-creates a `PMO UAT Case` named `UAT-<shift_id>`. Same for `requires_oat` + `PMO OAT Check`. So even shifts created directly (not via a plan) get their UAT/OAT records lazily.

### UI in `/app/pmo`

Two new project sub-tabs added between **Open Items** and **Milestones**: **Plans** and **Shifts**. New page order:

`Overview · Timeline · Open Items · Plans · Shifts · Milestones · RAID · UAT · OAT · Test History · Documentation · Activity`

**Plans tab:**
- List of plans (ID, Title, Status, Planner, Created).
- "New Plan" button → in-page modal.
- Click a row → opens the **Plan sub-page** inside `/app/pmo` (no Desk route).

**Plan sub-page:**
- Plan title, status chip, item count, full description (rendered markdown).
- Items table with row checkboxes + columns: Type / Title / Description / UAT / OAT / Hint / Promoted.
- Header checkbox toggles select-all.
- Three bulk-allocate buttons: **Allocate selected to Claude / Codex / Human**.
- "Add Item" button → modal to append a new item (with type, title, description, UAT/OAT checkboxes, assignee hint, optional JSON metadata).
- Rows already promoted show their target doctype + name, and are disabled in the selection.

**Shifts tab:**
- Three groups (Claude / Codex / Human) with a table per group.
- Per-row inline actions: **Execute via n8n** (if agent + Allocated/Proposed), **Start**, **Complete**, **Block** depending on status.
- "New Shift" button → in-page modal for manual shift creation outside the plan flow.

**Shift sub-page:**
- Title, status chip, assignee, planned vs actual timestamps, linked UAT case + OAT check, output notes (rendered markdown).
- Action bar: Execute via n8n / Start / Complete / Block / Open in Desk.

### Webhook hooks

`PMO Plan` and `PMO Shift` added to the existing `enqueue_excel_sync` event so the n8n Excel mirror picks them up alongside the rest of the doctypes.

---

## n8n contract (for the Execute button + Excel mirror)

### Execute via n8n (Frappe → n8n → agent)

When the user clicks **Execute via n8n** on a shift assigned to `claude` or `codex`:

1. Frappe `dispatch_shift(shift_id)` reads `site_config.json` → `pmo_n8n_dispatch_url`.
2. Frappe POSTs this payload to that URL:

```json
{
  "event": "pmo.shift.dispatch",
  "shift_id": "SHIFT-0001",
  "shift_name": "SHIFT-0001",
  "title": "Build the X feature",
  "description": "Markdown description of the work",
  "assigned_to": "claude",
  "shift_type": "Execution",
  "project": "VCL-DEV-PMO-002",
  "requires_uat": 1,
  "requires_oat": 0,
  "uat_case": "UAT-SHIFT-0001",
  "oat_check": null,
  "linked_plan": "PLAN-0001",
  "linked_requirement": "PMO-002-09",
  "linked_milestone": null,
  "linked_task": null,
  "complete_shift_callback": "/api/method/vcl_pmo_doctypes.api.complete_shift"
}
```

3. n8n receives the webhook and routes by `assigned_to`:
   - **claude** → SSH or HTTP-POST to the local Claude runner on this PC (`vcl-intranet` via Tailscale) with the shift payload. The runner spawns a Claude session with the shift description as the prompt and posts the result back.
   - **codex** → SSH or HTTP-POST to a local Codex runner (`codex exec <prompt>`), captures stdout/stderr.
   - **human** → no auto-route; n8n posts to Slack `#pmo` so the assigned human can pick it up.
4. When the agent finishes, the runner (or n8n) POSTs back to `complete_shift_callback`:

```json
POST /api/method/vcl_pmo_doctypes.api.complete_shift
{
  "shift_id": "SHIFT-0001",
  "output_notes": "What was done, with markdown evidence",
  "uat_result": "Pass",   // only if shift has uat_case
  "oat_result": null      // only if shift has oat_check
}
```

5. `complete_shift` flips status to Done, stamps `actual_end`, and if `uat_result`/`oat_result` supplied + the shift has a linked case/check, auto-creates a `PMO UAT Run` / `PMO OAT Run`.

**Frappe-side config needed:** add `pmo_n8n_dispatch_url` to the site's `site_config.json` (e.g. `https://n8n.vimitconverters.com/webhook/pmo-shift-dispatch`).

**n8n-side build needed:** workflow `vcl-pmo-shift-dispatch` that does the routing + agent invocation + callback. Suggest building it as a sibling to existing VCL n8n workflows.

### n8n Excel mirror (PMO-002-04)

The Frappe-side endpoints have been live since Phase 2 PR3:

- `project_packet(project_id)` returns the full project bundle (project, requirements, milestones, tasks, raid, uat_cases, oat_checks, documents — now also plans + shifts).
- `log_sync(anchor, direction, status, detail, project)` writes a `PMO Sync Log` row.
- The `enqueue_excel_sync` webhook fires on every PMO doctype `on_update` and writes a `PMO Sync Log` with `status="stale"` + a JSON `detail` blob containing `{event, doctype, name, project, modified}`.

**n8n-side build needed:**

1. **Frappe → Excel** workflow: trigger on Sync Log row creation (or HTTP webhook from Frappe), call `project_packet`, write `/mnt/vimit/apps/14. AI PMO/projects/<Project Name>/<Project Name> PMO.xlsx` with sheets Requirements / Milestones / Tasks / RAID / Plans / Shifts / UAT / OAT / Agent Log, then call `log_sync` with `status="ok"`.
2. **Excel → Frappe** workflow: every 5 min poll workbook mtime/hash, diff rows, PATCH Frappe doctypes via REST.

Full spec in `docs/N8N_EXCEL_SYNC_CONTRACT.md`. Add Plans + Shifts to the workbook sheet list when building.

---

## Migration / deploy

- Branch: `claude/shift-plan` (committed by Claude, awaiting review + merge).
- After merge to `main`, Frappe Cloud auto-deploys → `bench migrate` picks up the 3 new doctypes + the 2 new hooks entries.
- `site_config.json` needs `pmo_n8n_dispatch_url` set before the Execute button does anything useful (the API returns a clean error message until it's set).

---

## Acceptance criteria

After merge + deploy:

1. `/app/pmo` → click VCL-DEV-PMO-002 → Plans and Shifts sub-tabs visible (12 sub-tabs total).
2. New Plan modal creates a `PMO Plan` and opens its sub-page.
3. Add Item → row appears with item_type / title / description / UAT / OAT / assignee_hint columns.
4. Select rows + click "Allocate selected to Claude" → server creates the right downstream doctype per row (Milestone / Requirement / Task / RAID / Shift), back-fills `promoted_to_*` on the plan item, auto-creates UAT Case + OAT Check where ticked, links them on the Shift if the item_type was Shift, flips plan status to Allocated.
5. Shifts tab shows 3 groups (Claude / Codex / Human) with the allocated shifts.
6. Click a Shift → Shift sub-page shows full detail + actions.
7. With `pmo_n8n_dispatch_url` configured and an n8n endpoint reachable, clicking "Execute via n8n" POSTs the payload and flips status to In Progress.
8. n8n's callback to `complete_shift` flips status to Done and (if uat_result/oat_result passed) creates the corresponding Run.

---

## Out of scope for this branch

- n8n workflow itself (separate workstream — see contract above).
- Local agent runner on this PC (the thing n8n calls into). Should be a small FastAPI app at `~/projects/pmo_runner/` listening on a Tailscale-only port.
- Wiring `pmo_n8n_dispatch_url` into `site_config.json` (Frappe Cloud bench command, Tanuj-owned).
- Adding a portfolio-level "Shifts" tab (cross-project agent queue). Easy follow-up; currently each agent reads its queue by hitting `agent_shift_queue("claude" | "codex")` against one project at a time.
- Time tracking / actual-hours reporting on shifts (just `actual_start` / `actual_end` for now).

---

## Files touched

| Path | Action |
|---|---|
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_plan/` | New (JSON + .py + __init__.py) |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_plan_item/` | New (child table) |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/pmo_shift/` | New (with `before_save` controller for auto UAT/OAT case create) |
| `vcl_pmo_doctypes/api.py` | Added: plan/shift APIs + `dispatch_shift` + `_next_id` + `_parse_metadata` helpers + `_spawn_from_plan_item` |
| `vcl_pmo_doctypes/hooks.py` | Added PMO Plan + PMO Shift to `doc_events` for Excel sync |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.js` | Added: Plans + Shifts sub-tabs + sub-pages + bulk-allocate UI + Execute-via-n8n button + state for plans/shifts/planId/shiftId |
| `briefs/2026-05-27_PMO_SHIFT_AND_PLAN_BRIEF.md` | This brief |
