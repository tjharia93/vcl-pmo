# Codex Brief — Tanuj review of Status Report v4 (28 May 2026)

**Repo:** github.com/tjharia93/vcl-pmo (auto-deploys on push to `main`)
**Annotated PDF:** `briefs/review/2026-05-28_status_report_v4_annotated.pdf`
**Author:** Claude — handing off the build-side items from Tanuj's review

Tanuj reviewed v4 on reMarkable and left 7 handwritten annotations. Claude
(me) answered them all in the CLI and is shipping v5 of the status report
+ a Slack-bot setup card PDF. The three items below are the build-side
follow-ups — your lane.

---

## Item A — SHIFT-0002 spec (closes your Planning shift)

**Plan:** PLAN-0003. **Shift:** SHIFT-0002 (Allocated, requires_uat=1).
**Deliverable:** `briefs/2026-05-28_SCHEDULED_PLAN_REVIEW_SPEC.md`.

Tanuj has handwritten the answer on page 4 of the annotated PDF, verbatim:

> Tanuj will add a rough plan, or what direction we want to go in.
> ↓
> Read by codex or claude depending on tokens & usage
> they draft & send a plan to Tanuj via Slack for approval.

Translate that into a six-point spec that answers, in order:

1. **Trigger.** Frappe scheduler entry in `hooks.py`. Recommendation:
   `scheduler_events = {"hourly_long": ["vcl_pmo_doctypes.api.review_pending_plans"]}`
   running 00:00 / 06:00 / 12:00 / 18:00 EAT — short enough to feel
   responsive when Tanuj drops a rough plan, long enough to batch.
2. **What "needs review" means.** A `PMO Plan` with `status in (Draft,
   Proposed)` AND no row in `proposed_items` has `promoted_to_doctype` set
   AND `description.length > 20` (filter out skeletons).
3. **Capacity probe.** `frappe.conf.pmo_codex_available` flag (Bool).
   - True → call Codex (via dispatch_shift to a "draft-plan" n8n route).
   - False or unset → fall back to Claude.
   Document how Tanuj sets it (`bench set-config pmo_codex_available 1` /
   `0`); leave the actual probe automation as out-of-scope follow-up.
4. **Reviewer payload (what the drafting agent receives).** Plan
   record + `project_packet(project.project_id)` + the previous N=5
   approved plans on the same project for context. The agent's job is
   to expand the rough description into `PMO Plan Item` rows with
   correct `item_type`, sensible `assignee_hint` for each, and any
   `needs_uat`/`needs_oat` flags.
5. **Approval surface.** After the agent drafts items, it calls
   `send_plan_to_slack(plan.plan_id, comment="Drafted by codex — review")`
   which already exists. Then it POSTs a Slack message into the same
   thread with three buttons: **Approve all to Claude / Codex / Human**
   (Slack Block Kit `actions` block with `interactivity` routed back to
   Frappe via a new whitelisted method `vcl_pmo_doctypes.api.slack_approve_plan(plan_id, allocate_to)`).
6. **Action on approve.** `slack_approve_plan` calls existing
   `allocate_plan_items(plan_id, item_indices=all, assignee=allocate_to)`,
   stamps `approved_by` + `approved_at`, and posts a confirmation reply
   in the Slack thread.
7. **Failure modes.**
   - Reviewer agent crashes: log to `PMO Sync Log` direction=`plan-review`,
     mark plan `Proposed` with `description` appended `[review-failed @ ts]`
     so the next cron run won't loop forever. Cap retries at 3.
   - Human ignores >72h: send a Telegram nudge via `notify.sh`.
   - Codex quota mid-draft: catch and degrade — fall back to Claude.

UAT for SHIFT-0002 = Tanuj reads the spec and confirms all 7 points
covered. OAT = none yet (this is a planning shift; build is a separate
shift to be created from PLAN-0003 after the spec lands).

Once the spec file is committed:

```
update_doc("PMO Shift", "SHIFT-0002", {
  "status": "Done",
  "actual_end": "<now>",
  "output_notes": "Spec at briefs/2026-05-28_SCHEDULED_PLAN_REVIEW_SPEC.md (commit <hash>). UAT pending Tanuj read."
})
```

---

## Item B — Add `+ New Project` button to the portfolio toolbar

**Why:** Today there is no SPA path to create a PMO Project. You have to
use the bare Desk form. Tanuj flagged this on page 3 of the annotated PDF
(annotation: *"? What about new projects?"*).

**Where:** `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.js`.

The portfolio toolbar already has `New Requirement` + `Refresh`. Pattern:

```html
<button class="pmo-btn primary" data-action="new-project">+ New Project</button>
```

Wire a `modalNewProject()` that prompts for the four required fields:
`project_id` (validated against the existing `_next_id("VCL-DEV", ...)` shape
— let the user pick the prefix), `project_name`, `system`, and
`current_phase` (default `Phase 0 Discovery`). On save call a new
`@frappe.whitelist()` method `vcl_pmo_doctypes.api.create_project(project_id,
project_name, system, current_phase)` that inserts the doc and returns its
`name`. Refresh the portfolio after save.

UAT: click the button → modal opens → fill it → save → the new project
card appears in the Projects tab without a full page reload.

---

## Item C — Filter Inbox to "needs Tanuj"

**Why:** Tanuj's page-5 annotation: *"Inbox should not be the first page?
Or only show items pending approval."*

The current Inbox (top-left tab on the portfolio) shows every
`PMO Requirement` with `needs_action=1`. That's too noisy — it includes
items already in flight.

**Define "needs Tanuj":** an item where Tanuj is the gate. Concretely:

- `PMO Plan` with `status in (Draft, Proposed)` and at least one un-promoted
  item (i.e. waiting for Tanuj to allocate).
- `PMO Shift` with `status = Done` and either `uat_case` or `oat_check`
  whose `latest_result != Pass` (waiting for Tanuj's sign-off).
- `PMO Requirement` with `status = Blocked` (waiting for CFO decisions).
- `PMO Note` with `note_type = Plan Review` and unread (once Item A
  ships).

**Where:** the Inbox view in `pmo.js` plus a new API method
`vcl_pmo_doctypes.api.inbox_for_tanuj()` that returns the four buckets
above with `{kind, name, title, project, action_required}`.

Render with sub-section headers (Plans needing allocation / Shifts
needing UAT / Blocked requirements / Plan reviews pending).

UAT: Inbox shows 4 distinct buckets, total count matches the sum of the
sub-counts, and each row links to the right sub-page.

---

## Style notes (from review)

- Tanuj asked separately for `+ New Plan` and `+ Add Item` buttons in the
  workflow diagram (Figure 1 of the status report) to be split into
  "plan-level" vs "shift-level" because they got conflated. Claude is
  fixing this in v5 of the status report — no action for you, just FYI.
- The annotation arrow asking *"how are these linked?"* about Allocate /
  Send PDF / Execute via n8n is being clarified in v5 + the Slack-bot
  setup card. Again no action for you.

---

## Where the annotated PDF lives

`briefs/review/2026-05-28_status_report_v4_annotated.pdf` — read pages
3 and 4 for Tanuj's full handwritten flow before drafting the SHIFT-0002
spec. His handwriting on page 4 is the source of truth for the workflow.

## Doing the work — practical pointers

- **Branch:** `claude/review-response` or push direct to `main`; Tanuj's
  workflow tolerates direct-to-main when CI is green.
- **Auto-deploy** to Frappe Cloud happens on push to `main`. Migrations
  run automatically; no manual bench commands needed for new doctypes
  or new whitelisted methods.
- **Site config** for SHIFT-0002's capacity flag: `pmo_codex_available`
  (Bool, defaults to absent → treated as False, falls back to Claude).
  Document this in the spec.

## Ordering

Recommend doing them in order **A → C → B** because:
- A is the spec — pure markdown, no deploy needed.
- C only touches Inbox rendering + one API method.
- B introduces a new modal + the `create_project` API.

But all three can ship in one commit if convenient.
