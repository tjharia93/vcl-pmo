# n8n Excel Sync Contract

## Frappe To Excel

Frappe webhook on:

- `PMO Project`
- `PMO Requirement`
- `PMO UAT Case`
- `PMO OAT Check`

Webhook payload:

```json
{
  "event": "on_update",
  "doctype": "PMO Requirement",
  "name": "PMO-002-04",
  "project": "VCL-DEV-PMO-002",
  "modified": "2026-05-27 12:00:00"
}
```

n8n steps:

1. Receive Frappe webhook.
2. Call `/api/method/vcl_pmo_doctypes.api.project_packet?project_id=<project>`.
3. Open or create `/mnt/vimit/apps/14. AI PMO/projects/<Project Name>/<Project Name> PMO.xlsx`.
4. Write sheets: `Requirements`, `Issues`, `UAT`, `Agent Log`, `OAT`.
5. Call `/api/method/vcl_pmo_doctypes.api.log_sync`.

Sync success payload:

```json
{
  "anchor": "excel:VCL-DEV-PMO-002",
  "direction": "Frappe to Excel",
  "status": "ok",
  "project": "VCL-DEV-PMO-002",
  "detail": "Workbook updated"
}
```

## Excel To Frappe

Use the same trigger pattern currently used for label/jobcard Excel updates, or run a scheduled workflow every 5 minutes.

n8n steps:

1. Read workbook mtime/hash.
2. Skip if unchanged.
3. Read workbook rows.
4. Diff against last synced row hashes.
5. Patch Frappe doctypes through Frappe REST API.
6. Write `PMO Sync Log`.

## Conflict Rule

Frappe wins by default.

If Excel and Frappe both changed the same row since the last sync:

1. Keep Frappe value.
2. Write Excel value into `PMO Sync Log.detail`.
3. Mark sync status `blocked`.
4. Surface it in PMO Inbox.

## Authentication

n8n should use a dedicated Frappe API user with `PMO User`.

Do not embed credentials in the PMO repo.
