# VCL PMO Frappe-Native Migration

## Decision

Move the PMO user experience and PMO data ownership to Frappe Cloud at:

`https://vimitconverters.frappe.cloud/app/pmo`

The local intranet FastAPI implementation remains a reference build and fallback until the Frappe-native app passes UAT and OAT.

## Target Architecture

```text
Frappe Cloud
  PMO Workspace / Page
  PMO Project
  PMO Requirement
  PMO UAT Case
  PMO OAT Check
  PMO Agent Log
  PMO Sync Log
        |
        | webhooks
        v
n8n
  Frappe -> Excel mirror
  Excel -> Frappe scheduled diff
        |
        v
/mnt/vimit/apps/14. AI PMO/projects
```

## What Moves To Frappe

- Inbox, Projects, Requirements, UAT, OAT, Briefing views.
- PMO Project, Requirement, UAT Case, OAT Check, Agent Log, Sync Log doctypes.
- Agent completion webhook as a whitelisted Frappe method.
- ERPNext linked-document preview/search through Frappe server methods.
- System Manager / PMO User permissions.

## What Stays Local

- Excel file access under `/mnt/vimit`.
- n8n workflow execution, if n8n is the existing local Excel automation layer.
- Any local-only watcher or scheduled Excel diff job.

## n8n Excel Mirror

### Frappe To Excel

1. Frappe document event fires on PMO Project / Requirement / UAT Case / OAT Check.
2. Webhook calls n8n with doctype, name, project id, modified timestamp.
3. n8n fetches the full project packet from Frappe.
4. n8n updates `/mnt/vimit/apps/14. AI PMO/projects/<Project>/<Project> PMO.xlsx`.
5. n8n posts sync result to `PMO Sync Log`.

### Excel To Frappe

1. Scheduled n8n workflow polls workbook mtime/hash.
2. n8n reads workbook rows.
3. n8n diffs rows against last sync hash.
4. n8n patches Frappe PMO doctypes through the API.
5. Frappe remains canonical.

## Cutover Criteria

- Frappe workspace loads and matches the current PMO dashboard.
- PMO Project count is 4.
- VCL-DEV-PMO-002 has 10 requirements.
- UAT cases can be created and marked Pass/Fail.
- OAT run records pass/fail state and evidence.
- Agent completion webhook updates requirement, agent log, and sync log.
- n8n writes all per-project Excel workbooks.
- Excel-to-Frappe diff updates a test requirement correctly.
- PMO User permissions are verified.
- Local FastAPI PMO is retired only after one week of parallel operation.
