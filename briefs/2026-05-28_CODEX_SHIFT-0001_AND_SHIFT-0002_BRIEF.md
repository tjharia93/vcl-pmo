# Codex Brief — SHIFT-0001 (PMO Nav Fix) + SHIFT-0002 (Scheduled Plan Review)

**Date:** 2026-05-28
**Author:** Claude (assigned the sister shifts SHIFT-0003 / SHIFT-0004)
**Repo:** github.com/tjharia93/vcl-pmo
**Project:** VCL-DEV-PMO-002 (VCL PMO System)
**Auto-deploy:** push to `main` → Frappe Cloud `bench migrate`

You own two shifts. SHIFT-0001 is already `In Progress`. SHIFT-0002 is `Allocated`
and queued behind it. Both have `requires_uat=1` and `requires_oat=1`.
Auto-created tracking docs exist:

- `UAT-SHIFT-0001`, `OAT-SHIFT-0001`
- `UAT-SHIFT-0002`, `OAT-SHIFT-0002`

These now also carry `bucket = "SHIFT-0001"` / `"SHIFT-0002"` and `linked_shift`
fields after my SHIFT-0004 schema change, so the Test History view will group
them under the shift automatically once the migration runs.

---

## SHIFT-0001 — Fix PMO plan/project back navigation

**Plan:** PLAN-0004 ("Check all Pages Work").
**Symptom (Tanuj):** clicking browser **Back** from a Plan sub-page lands on
"Page not available".

> **Status note (2026-05-28 18:15):** Commit **22f68fa** *"fix: stabilize PMO
> route state and requirement IDs"* already landed on `main`. That commit adds
> 9 `popstate` / `pushState` call sites in `pmo.js` and bumps
> `pmo_requirement.py`. Treat the implementation as **done pending UAT** —
> the work below now reduces to *verify the acceptance criteria and mark the
> ERPNext shift Done* (see end of brief).

### Root cause that was addressed

The PMO SPA at `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.js` kept
view state in `this.state.view / project / subtab / planId / shiftId / caseId / runId`,
but route writes (`history.pushState`) on sub-page entry didn't encode every
identifier. When the user hit Back, Frappe's Desk router couldn't reconstruct
the state — hence "Page not available."

### Acceptance criteria (`OAT-SHIFT-0001`)

The Plan brief description nailed it: *"Make `/app/pmo` route state include
project, subtab, plan, shift, case, and run identifiers so browser Back and
reload never land on a page-not-available state."*

Concretely:

1. Every navigation transition (`renderProject`, `renderPlan`, `renderShift`,
   `renderCase`, run history view) must `history.pushState` a URL fragment
   that uniquely identifies the view.
2. `popstate` handler reads the fragment and rebuilds `this.state` + calls
   the matching render.
3. Hard reload (F5) on any sub-page lands back on the same sub-page, not on
   the portfolio root.
4. Existing button-driven nav (Portfolio chip, breadcrumbs) continues to
   work — they should call the same router method, not bypass it.

### Suggested fragment shape

```
/app/pmo                            → portfolio
/app/pmo#p/VCL-DEV-PMO-002                → project root (default subtab)
/app/pmo#p/VCL-DEV-PMO-002/plans          → project Plans tab
/app/pmo#p/VCL-DEV-PMO-002/plans/PLAN-0002  → plan sub-page
/app/pmo#p/VCL-DEV-PMO-002/shifts/SHIFT-0003 → shift sub-page
/app/pmo#p/VCL-DEV-PMO-002/uat/UAT-SHIFT-0001  → case detail
/app/pmo#p/VCL-DEV-PMO-002/uat/UAT-SHIFT-0001/run/3 → run detail
```

Short keys (`p`, `plans`, `shifts`, `uat`, `oat`, `run`) keep the fragment
copy-paste-friendly.

### UAT (`UAT-SHIFT-0001`)

Tanuj will manually walk:
- Open `/app/pmo` → click project → Plans → open a plan → Back → expect Plans tab.
- Open a plan, F5 → expect the same plan to reload.
- Paste a deep-link URL into a new tab → expect the target sub-page to render
  with the right state.
- All three above for Shifts, UAT, OAT, and run detail.

---

## SHIFT-0002 — Design scheduled plan review workflow (Planning shift)

**Plan:** PLAN-0003 ("Scheduled Plan Runs").
**Tanuj's framing (verbatim from PMO Plan):**

> The Plans doctype should be reviewed by codex (if it has limits available);
> if not then Claude reviews all and builds the tasks for the shift for PMO
> human to review.

So this is a **design** shift — output is a written spec (markdown), not
running code. Save it as `briefs/2026-05-28_SCHEDULED_PLAN_REVIEW_SPEC.md`
(or similar) in this repo when done.

### The problem

`PMO Plan` rows currently sit at `status=Draft|Allocated` indefinitely until
a human (Tanuj) opens the Plans tab and clicks **Allocate to Claude / Codex /
Human** on each item. There is no scheduled sweep. We want:

1. A nightly (or hourly) job that walks `PMO Plan` rows in `Draft` /
   `Proposed` / `Allocated` (with un-promoted items).
2. For each plan, *one* agent reviews the items and proposes which should be
   bulk-allocated to `claude`, `codex`, or `human`.
3. Capacity-aware routing: ask `codex` first; if codex is at quota
   (define how we know — site_config flag, last-N-minutes throttle, env var,
   etc.), fall back to `claude`.
4. The reviewer agent does **not** auto-allocate. It writes its proposal back
   to the plan (new PMO Note linked to the plan, or new fields on the plan
   itself) and notifies the PMO human via Slack / Telegram / email to
   approve.
5. Once human approves, items are bulk-allocated via the existing
   `allocate_plan_items` API.

### Acceptance criteria (`OAT-SHIFT-0002`)

The spec must answer:

1. **Trigger** — cron schedule? Frappe scheduler entry in `hooks.py`?
   On-create webhook?
2. **Capacity probe** — how do we decide codex has capacity vs not?
   A `pmo_codex_available` site_config flag set by an external monitor is the
   simplest; alternatives (n8n ping, env var, last-write timestamp) should be
   listed with trade-offs.
3. **Reviewer payload** — what the reviewer reads: plan + items + project
   context + maybe last N notes. What it returns: per-item assignee proposal
   + rationale. Where it lands: `PMO Note` typed `Plan Review` linked to the
   plan, OR a new `proposed_assignee` column on `PMO Plan Item`.
4. **Approval surface** — where the PMO human sees pending reviews. New
   "Inbox" widget on `/app/pmo` Plans tab? Daily Telegram digest? Slack
   `#ai-pmo-plans` message with an "Approve all" button (links into Plans
   sub-page)?
5. **Action on approve** — call `allocate_plan_items` for each item using
   the agent-proposed assignee. Record approver + timestamp on the plan
   (`approved_by`, `approved_at` already exist).
6. **Failure modes** — what if the reviewer agent crashes? What if the human
   ignores the proposal for >N days?

### UAT (`UAT-SHIFT-0002`)

The spec is the deliverable. UAT = Tanuj reading the spec and confirming all
six points above are answered. No runtime test until the implementation
shift is split off.

---

## Pointers — files you'll touch / read

- `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.js` — the SPA. View state
  in `state`, routing in `render()` + the `action()` dispatcher (~line 240).
- `vcl_pmo_doctypes/api.py` — backend. Existing patterns to follow:
  - `dispatch_shift` (line 826) for n8n webhooks
  - `allocate_plan_items` (line 573) for bulk promotion
  - `_spawn_from_plan_item` (line 619) for promotion targets
  - `send_plan_to_slack` (appended today) for Slack push pattern — useful
    template if the SHIFT-0002 spec wants to push the approval prompt to
    Slack with the brand PDF.
- `vcl_pmo_doctypes/hooks.py` — wire any scheduler entry here:
  `scheduler_events = {"daily": ["vcl_pmo_doctypes.api.review_pending_plans"]}`

---

## What's already shipped today (don't redo this)

Claude's SHIFT-0003 + SHIFT-0004 are pushed in the same commit batch:

- **SHIFT-0004:** `PMO UAT Case` + `PMO OAT Check` now have `bucket`,
  `linked_shift`, `linked_task`, `linked_plan` fields. Shift's
  `before_save` and the plan-driven autocreate both populate them. The
  Test Status / UAT / OAT views in `pmo.js` now group cases by bucket
  with a header row showing pass/fail/blocked/not-run counts.
- **SHIFT-0003:** `vcl_pmo_doctypes.api.send_plan_to_slack(plan_id)` +
  "Send PDF to Slack" button on the Plan sub-page. Renders a VCL-branded
  A4 PDF (14pt, brand blue) and uploads it to `#ai-pmo-plans`. Needs
  `pmo_slack_bot_token` in `site_config.json` before it works in
  production. See `docs/SLACK_INTEGRATION.md`.

Both shifts are marked `In Progress` until Tanuj UATs the Slack push end-to-end.

---

## Updating ERPNext when you're done

For SHIFT-0001 — after the navigation fix:
```
update_doc("PMO Shift", "SHIFT-0001", {
  "status": "Done",
  "actual_end": "<now>",
  "output_notes": "<markdown summary + commit hash>"
})
```

For SHIFT-0002 — after the spec lands:
```
update_doc("PMO Shift", "SHIFT-0002", {
  "status": "Done",
  "actual_end": "<now>",
  "output_notes": "Spec at briefs/2026-05-28_SCHEDULED_PLAN_REVIEW_SPEC.md (commit <hash>)"
})
```

Don't auto-pass UAT/OAT — those land via `complete_shift` with
`uat_result=Pass / oat_result=Pass` once Tanuj has walked the test.
