# VCL PMO — Codex Rework Brief (Post UAT/OAT)

**Date:** 2026-05-27
**From:** Tanuj (via Claude testing pass)
**To:** Codex
**Project:** VCL-DEV-PMO-002 — VCL PMO System
**Repo:** github.com/tjharia93/vcl-pmo
**Branch off:** main
**Status going in:** Frappe doctypes + seed data + `agent_complete` webhook all work. **The UI shipped does not match the spec.** This brief lists the three reworks needed before UAT/OAT can be re-run.

---

## Context

Claude ran the testing handoff today. Functional pieces pass:

- 4 PMO Projects / 10 PMO Requirements / 10 UAT Cases / 12 OAT Checks seeded and queryable
- `vcl_pmo_doctypes.api.summary`, `oat_run`, `agent_complete`, `log_sync`, `project_packet` all return correct shapes
- `agent_complete` dogfooded end-to-end: PMO-002-06 → status Done, Agent Log row created
- DocPerm matrix correct (PMO User: read/write/create, no delete on logs)

**However Tanuj's browser walkthrough surfaced three build deviations from the brief.** The data + API layer is fine. The page layer needs rework before this can replace the local FastAPI PMO.

See `~/projects/pmo_testing/2026-05-27_test_report.md` for the full test report including Major / Minor findings and Pass/Fail/Blocked grid.

---

## Rework 1 — Apply VCL Brand v1.1 (mandatory)

**Problem.** `vcl_pmo_doctypes/page/pmo/pmo.css` uses an off-brand "Steel+Pulse" palette: background `#0A1130`, accent `#7BB48A`, Inter font, generic chip colours. None of these are in the VCL Brand v1.1 token set.

**Fix.** Rewrite `pmo.css` (and any inline colour values in `pmo.js`) against these exact tokens. **Use the named tokens, not arbitrary hexes.**

Palette (May 2026 v1.1):

| Token | Hex | Use |
|---|---|---|
| VCL Blue | `#2B3990` | Primary brand — H2, headers, table header fills, buttons, hyperlinks |
| VCL Navy | `#1D2766` | H1, document titles, dark shell background |
| VCL Blue Mid | `#5C6DBE` | Dividers, secondary icons, chart lines |
| VCL Blue Light | `#D6DBF5` | Callout fills, info backgrounds |
| VCL Blue Pale | `#EEF0FB` | Page tints, hover states |
| VCL Sage | `#5A9367` | **Brand accent** — logo marks, active nav indicator (inset border + soft tint `rgba(90,147,103,0.22)`), user-pill avatars. Replaces the current `#7BB48A` mint. |
| VCL Sage Soft | `rgba(90,147,103,0.22)` | Active-nav background tint over dark sidebar |
| VCL Green | `#1B7A45` | Pricing figures, Complete/Done status, positive KPIs. **Not blue for pricing.** |
| VCL Green Light | `#D4EDE0` | Complete row fills |
| VCL Amber | `#B86B00` | Warnings, In Progress, AR overdue <90d. **Replaces red for most cautions.** |
| VCL Amber Light | `#FFF0CC` | Warning row fills |
| VCL Red | `#C0392B` | **RESTRICTED.** Only system errors, AR overdue 90+, validation failures, classification stamps. Never for navigation, decoration, general warnings, brand accents. |
| VCL Red Light | `#FADBD8` | Error row fills only |
| Ink | `#1C1C1E` | Body text, H3+ |
| Mid Grey | `#4A4F5C` | Secondary text, H4, captions |
| Muted | `#8A909E` | Footnotes, metadata, helper labels |
| Rule | `#CBD2E0` | All borders/dividers |
| Surface | `#F4F5F8` | Alt table rows, page tints |
| White | `#FFFFFF` | Page background, primary table rows |

Typography:

- **Calibri** — all headings and body. H1 20pt Navy Bold, H2 15pt Blue Bold, H3 12pt Ink Bold, body 11pt Ink, table header 10pt White Bold, table body 10pt Ink, caption 9pt italic Muted.
- **Courier New** — code, ERPNext field names (snake_case), API paths, system values.
- ERPNext DocType names in body copy: Title Case, bold.
- ERPNext field names: snake_case in inline code.

Chip mapping in `pmo.js:chip()` — swap to brand tokens:

- `Done` / `Pass` → VCL Green on Green Light fill
- `In Review` / `In Progress` → VCL Amber on Amber Light fill
- `Blocked` / `Fail` → VCL Red on Red Light fill (this is the rare allowed Red usage)
- default / unknown → VCL Blue on Blue Light fill

Tables:

- Header row VCL Blue fill, White Bold text
- Alt rows White / Surface
- Borders 0.5pt Rule colour
- Hover row tint: Blue Pale

Shell:

- Page background: White (the dark-navy aesthetic must go for portfolio screens; keep dark accent strictly to header/ticker/active-nav if desired, using VCL Navy `#1D2766` not `#0A1130`)
- Active tab: VCL Sage inset border + Sage Soft background tint
- Hover row/card border: VCL Blue Mid

---

## Rework 2 — Stop bouncing every click to the Desk backend

**Problem.** `pmo.js` lines 64-72 wire every interaction to `frappe.set_route("Form" / "List", ...)`. The PMO Page becomes a launcher into the Frappe Desk rather than a self-contained product:

- Click a requirement row → `frappe.set_route("Form", "PMO Requirement", row.name)` → leaves the page entirely
- Click a project card → same, opens PMO Project form in Desk
- "New UAT" button → `frappe.new_doc("PMO UAT Case", ...)` → opens Desk new-doc dialog
- UAT tab buttons → "Open UAT List" → goes to backend list
- OAT tab buttons → "Open OAT List" → goes to backend list

**Fix.** Keep all interactions in-page. The PMO Page is the surface; Frappe Desk is only a fallback for edge edits.

Required behaviour:

- **Requirement row click** → opens a **right-side drawer** (or modal) inside `.pmo-shell` with the full requirement: title, description, area, priority, status (editable inline via a Select), uat_result, owner, linked ERPNext docs table, notes editor, "Mark UAT Pass/Fail" buttons. Save via `frappe.db.set_value` / `frappe.client.save`. No route change.
- **Project card click** → opens a **project workspace inside the page** (see Rework 3). No route change.
- **"New UAT Case"** → in-page modal that prompts for requirement (auto-filled when launched from a requirement row), description, tester, evidence. Save via `frappe.db.insert`. No route change.
- **"New OAT Check"** → same pattern.
- **"New Requirement"** primary action — same pattern. The current `page.set_primary_action("New Requirement", () => frappe.new_doc("PMO Requirement"))` must go.
- **"Open UAT List" / "Open OAT List" buttons** — remove. The page itself is the list.

Hard route changes (i.e. `frappe.set_route`) are allowed only for:

- "Open in Desk" overflow button on the requirement drawer for the rare power-edit
- Sync Log row click (Sync Log is operational/admin, not a daily PMO surface)

Edit path: any inline edit (status, uat_result, notes) → `frappe.db.set_value` → refetch the local row → re-render → no full page reload. Optimistic update OK.

---

## Rework 3 — Project-based UAT and OAT (architectural)

**Problem.** Right now UAT and OAT are presented as **portfolio-flat** lists:

- The UAT tab shows a single "UAT rule" info card with buttons that route to the global `PMO UAT Case` list (all 10 rows across all projects)
- The OAT tab shows the entire 12-row OAT list with a `project` column

This collapses every project's testing into one bucket. Tanuj's expectation: **the PMO is project-based** — each project (VCL-DEV-AR-001, HR-001, IMP-001, PMO-002, future) is its own workstream with its own Requirements, UAT, OAT, Agent Log, Sync Log, Briefing. The portfolio view is a roll-up; the daily work happens inside a project.

**Fix.** Restructure the Projects tab into a portfolio → project drill-down. The top-level tabs (Inbox, Requirements, Projects, UAT, OAT, Briefing) stay for the portfolio view. Clicking a project opens a **project workspace** inside the page with its own scoped sub-tabs.

Information architecture:

```
PMO Page
├── Portfolio view  (current top-level tabs — Inbox / Requirements / Projects / UAT / OAT / Briefing aggregate across ALL projects)
│
└── Project workspace  (opens when you click a project card from Projects tab)
    ├── Overview      (project meta — Project ID, name, system, status, priority, progress %, go_live, requestor, context, linked ERPNext project, Excel path)
    ├── Requirements  (only this project's requirements; the Inbox-style filter applies here too)
    ├── UAT           (only this project's PMO UAT Cases; filter PMO UAT Case where project=<this>)
    ├── OAT           (only this project's PMO OAT Checks; filter where project=<this>)
    ├── Agent Log     (only this project's Agent Log entries; filter where project=<this>)
    └── Sync Log      (only this project's Sync Log entries; filter where project=<this>)
```

Project workspace lives **inside** `.pmo-shell` — no route change to a different Frappe page. Implementation hint: when the user clicks a project card, swap `this.view` to `"project:<project_id>"` and add a `renderProject(projectId)` method that hides the portfolio shell and paints a project-scoped sub-shell. A breadcrumb at the top of the project workspace ("Portfolio → AR Collections") returns the user to the portfolio.

UAT case IDs already include the project (e.g. `UAT-PMO-001` for VCL-DEV-PMO-002). For consistency, future projects should follow the pattern `UAT-{project_short}-NNN` and `OAT-{project_short}-NNN`. The autoname fields are already `field:uat_case_id` / `field:check_id`, so naming stays caller-controlled — no schema change needed.

Within a project's UAT/OAT sub-tabs the **inline edit / drawer pattern from Rework 2** applies: click a UAT case → drawer with Pass/Fail buttons + evidence editor; save without leaving the page.

The portfolio-level UAT/OAT tabs (top-level) keep a roll-up view: "X/Y projects have passing UAT, Z OAT checks blocked across the portfolio" — but they're a portfolio-status surface, not a place where you mark a single case Pass/Fail. Per-case Pass/Fail happens inside the project workspace.

---

## Out of scope for this rework

- n8n Excel mirror build (OAT-006/007/008/011/012). Separate workstream — covered by PMO-002-04 In Review.
- Renaming `PMO Requirement.owner` / `PMO OAT Check.owner` to avoid shadowing Frappe `owner`. Schema migration — separate, lower priority.
- `agent_complete` Comment-insert `ignore_permissions=True` tightening. Security hardening — separate small fix.
- Sync Log autoname format and the junk `PMO-SYNC-.#####` row cleanup. Cosmetic, fold into the next maintenance pass.

These are listed as Minor / Major findings in the test report for traceability but are **not blockers for the UI rework**. Fix them in a follow-up branch.

---

## Acceptance criteria for the rework

Re-running the testing handoff against the reworked branch should pass these without my (Claude's) "Pass with API caveat" qualifier:

1. `/app/pmo` paints with VCL Brand v1.1 — no off-brand hexes in `pmo.css`, no Inter font, no `#7BB48A` mint accent, no `#0A1130` background. Chips use Brand tokens.
2. Clicking a requirement row opens an in-page drawer; user can edit status / uat_result / notes / mark UAT without leaving `/app/pmo`.
3. Clicking a project card opens an in-page project workspace with its own sub-tabs (Overview, Requirements, UAT, OAT, Agent Log, Sync Log). Sub-tabs show data filtered to that project only.
4. Portfolio-level Inbox / Requirements / UAT / OAT tabs stay as the cross-project roll-up surface. Portfolio UAT/OAT tabs do not let the user mark individual cases — that happens inside a project workspace.
5. No `frappe.set_route` calls in the primary user flows. The only allowed routes are: Sync Log drilldown (admin), and an "Open in Desk" overflow on the drawer.
6. UAT-PMO-001 through UAT-PMO-010 + OAT-PMO-001 through OAT-PMO-012 can be re-marked from inside the page without ever opening the Frappe Desk.

When Codex flips PMO-002-03 (Frappe-native PMO UI) back to Done after rework, also amend its `note` to reference this brief.

---

## Repo path summary

| File | Action |
|---|---|
| `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.css` | Rewrite against VCL Brand v1.1 tokens |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.js` | Remove `frappe.set_route` from primary flows; add in-page drawer, modals, project workspace renderer |
| `vcl_pmo_doctypes/vcl_pmo_doctypes/page/pmo/pmo.json` | Likely no change (just the Page registration) |
| `vcl_pmo_doctypes/doctype/` (outer/duplicate) | Delete the entire duplicate directory; Frappe loads from the inner `vcl_pmo_doctypes/vcl_pmo_doctypes/doctype/` path |
| `briefs/2026-05-27_CODEX_REWORK_BRIEF.md` | This brief (already committed) |

Also after rework, update `PMO-002-03.note` (currently still pointing at the May-27 seeding) to reference this rework round.
