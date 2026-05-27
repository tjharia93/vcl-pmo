# Claude CLI Handoff — Frappe PMO Testing

## Target

Test the Frappe-native VCL PMO app.

- Repo: https://github.com/tjharia93/vcl-pmo
- App URL: https://vimitconverters.frappe.cloud/app/pmo
- Project under test: `VCL-DEV-PMO-002`

## Safety Rules

Only edit PMO doctypes:

- `PMO Project`
- `PMO Requirement`
- `PMO UAT Case`
- `PMO OAT Check`
- `PMO Agent Log`
- `PMO Sync Log`

Do not edit or submit:

- Sales Invoice
- Purchase Invoice
- Journal Entry
- Payroll Entry
- Salary Slip
- Customer
- Supplier
- Salary Structure
- Any finance, HR, customer, or supplier master outside PMO

## Expected Seed Counts

Verify these records exist:

| Doctype | Expected |
|---|---:|
| PMO Project | 4 |
| PMO Requirement for `VCL-DEV-PMO-002` | 10 |
| PMO UAT Case | 10 |
| PMO OAT Check | 12 |

## Test Documents

Use these repo docs as reference:

- `docs/PMO_TESTING.md`
- `docs/N8N_EXCEL_SYNC_CONTRACT.md`
- `briefs/2026-05-27_FRAPPE_NATIVE_PMO_MIGRATION.md`

## Test Checklist

1. Open `https://vimitconverters.frappe.cloud/app/pmo`.
2. Confirm the PMO dashboard loads.
3. Confirm tabs exist:
   - Inbox
   - Requirements
   - Projects
   - UAT
   - OAT
   - Briefing
4. Confirm KPI strip shows project and requirement counts.
5. Open `PMO Project` list and confirm 4 projects exist.
6. Open `PMO Requirement` list filtered to `VCL-DEV-PMO-002` and confirm 10 requirements exist.
7. Confirm Inbox shows requirements with:
   - `In Review`
   - `Blocked`
   - `needs_action`
8. Open `PMO-002-03` and confirm the form opens.
9. Create or update a `PMO UAT Case` for `PMO-002-03`.
10. Mark the UAT case:
    - `Pass` if dashboard works
    - `Fail` if dashboard does not work
11. Add evidence to the UAT case:
    - URL tested
    - observed result
    - exact error if any
12. Open `PMO UAT Case` list and confirm 10 starter cases exist.
13. Open `PMO OAT Check` list and confirm 12 starter checks exist.
14. Mark `OAT-PMO-003` Pass if all PMO doctypes exist:
    - PMO Project
    - PMO Requirement
    - PMO UAT Case
    - PMO OAT Check
    - PMO Agent Log
    - PMO Sync Log
15. Check `PMO Sync Log`:
    - confirm rows exist
    - note any `error` or `blocked` rows
16. If API credentials are available, test `vcl_pmo_doctypes.api.agent_complete` for `PMO-002-06` with notes `Claude test`.
17. Confirm a `PMO Agent Log` row is created.

## Permissions Test

If possible:

1. Confirm `System Manager` can access `/app/pmo`.
2. Confirm `PMO User` can access `/app/pmo`.
3. Confirm a non-PMO user cannot access PMO doctypes/page.

## Report Format

Return findings in this format:

```text
Findings

Critical:
- ...

Major:
- ...

Minor:
- ...

Pass/Fail Summary:
- Dashboard:
- Seed data:
- UAT:
- OAT:
- Permissions:
- Sync Log:
- Agent webhook:

Evidence:
- URLs opened:
- Records created/updated:
- Screenshots:
- Exact errors:
```

## Completion Rule

Do not mark PMO testing complete until:

- Dashboard loads.
- Seed counts match.
- At least one UAT case is updated with evidence.
- At least one OAT check is updated with evidence.
- Any blocker is recorded as Critical or Major.
