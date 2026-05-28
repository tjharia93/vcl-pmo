# VCL-DEV-PROD-001

Project: `Production Log & Job Card System`

System: `ERPNext v16 (Frappe Cloud) - production_log Frappe app`

Repo: `github.com/tjharia93/vcl-production`

Status: `In Build`

Priority: `High`

Requestor: `COO / Head of Production`

Go Live: `Phase 1 Live - Phase 2 TBD`

Excel Mirror: `/mnt/vimit/apps/14. AI PMO/projects/Production Log/Production Log PMO.xlsx`

## Context

Custom Frappe app managing the full job card lifecycle across Computer Paper, Labels, Cartons, and ETR.

This is one PMO project with five lanes in the `area` field. Do not split it into separate project IDs.

## Lanes

| Lane | Scope |
|---|---|
| CPS | Shared Customer Product Specification foundation and snapshots |
| Computer Paper | Computer Paper job card, traveller, and resource consumption |
| Label | Label job card, traveller, and resource consumption |
| Carton | Carton job card traveller v4, SVG layout, Chrome PDF output |
| ETR | ETR job card schema and execution path |

## Phase 1 Live

- Customer Product Specification doctype with CP, Label, and Carton product types.
- CPS to Job Card link and spec snapshot auto-populate.
- Job Card Computer Paper with traveller and resource consumption.
- Job Card Label with traveller and resource consumption.
- Job Card Carton traveller v4 with SVG layout, Chrome PDF, and 6-page output.
- Job Card ETR with its own schema: status, delivery_date, order_qty.
- Workstation master with 14 types and 8 product line routes using process_number.
- EOD Gemba PDF via n8n webhook to Telegram at 17:00 EAT.

## Open Items

- `PROD-009`: Hamada 01 reclassification - R2R vs S2S Printing. Status: `Blocked`. Owner: `Tanuj`.
- `PROD-010`: S3 install - rename Slotter 01 / Bundler 01 to actual equipment IDs. Status: `Not Started`.

## Phase 2 Not Started

- `PROD-011`: Daily Production Log + Production Entry redesign.
- `PROD-012`: Daily Production Plan + Actuals redesign.
- `PROD-013`: Production reports - Daily Summary, Incomplete Reels, Operator Performance.

