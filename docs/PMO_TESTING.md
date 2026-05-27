# PMO Testing Documentation

## Purpose

This document defines UAT and OAT for the Frappe-native PMO migration.

UAT confirms that Tanuj can run the PMO workflow. OAT confirms that the operating system around PMO is dependable: permissions, Excel mirror, n8n sync, agent webhook, audit logs, and fallback behaviour.

## UAT Scope

| ID | Area | Test | Expected Result |
|---|---|---|---|
| UAT-001 | Workspace | Open `/app/pmo` | PMO workspace loads for System Manager / PMO User |
| UAT-002 | Inbox | View action queue | Blocked, In Review, and needs_action requirements are shown |
| UAT-003 | Requirement | Open requirement | Detail, links, activity, UAT, and agent sections are visible |
| UAT-004 | Status | Change status | Requirement status persists in Frappe |
| UAT-005 | UAT | Create UAT case | `PMO UAT Case` row is created and linked to requirement |
| UAT-006 | UAT | Mark Pass | UAT result is saved with tester/date/evidence |
| UAT-007 | UAT | Mark Fail | Requirement UAT result becomes Fail and item returns to action queue |
| UAT-008 | ERPNext Links | Add linked doc | Link appears and preview opens the target ERPNext doc |
| UAT-009 | Agent | Submit completion webhook | Requirement updates, Agent Log row is created |
| UAT-010 | Briefing | Render/print briefing | Output is readable and suitable for handoff |

## OAT Scope

| ID | Area | Check | Evidence |
|---|---|---|---|
| OAT-001 | Permissions | Non-PMO user is denied | Screenshot / 403 |
| OAT-002 | Permissions | PMO User can read/write but not delete critical logs | Role permission report |
| OAT-003 | ERPNext | Frappe doctypes exist | DocType list |
| OAT-004 | ERPNext | Four seed projects exist | PMO Project report |
| OAT-005 | ERPNext | VCL-DEV-PMO-002 has 10 requirements | PMO Requirement filter |
| OAT-006 | n8n | Frappe to Excel workflow runs | PMO Sync Log ok row |
| OAT-007 | n8n | Excel to Frappe diff updates test row | Before/after row evidence |
| OAT-008 | Excel | Per-project workbook has expected sheets | Workbook screenshot |
| OAT-009 | Agent | Agent webhook posts completion | PMO Agent Log row |
| OAT-010 | Audit | Linked ERPNext docs receive comments | Comment timeline |
| OAT-011 | Recovery | n8n failure writes Sync Log error | PMO Sync Log error row |
| OAT-012 | Cutover | One-week parallel run clean | Sign-off note |

## Cutover Rule

Do not retire the local FastAPI PMO until all required UAT and OAT checks pass, n8n mirrors Excel successfully for one week, and Tanuj signs off in `PMO-002-10`.
