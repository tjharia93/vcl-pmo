# VCL Weekly Finance Close — cross-reference

**Project ID:** VCL-FIN-CLOSE-001
**Type:** Process design (Phase 1) → Automation (Phase 2)
**Owner:** Tanuj · execution Jitu
**Issued:** 2026-05-27 · Phase 1 starts **W22 (week ending Fri 30 May 2026)**

## What this is

A weekly lock + weekly pack layered on top of VCL's existing daily tooling. Rolling 7-day close, **VCL only** (BIL/BVL stay monthly), pack issued every **Friday 17:00 EAT** as the new EOD batch.

## Where the full doc lives

**Primary working location:**
[`/mnt/vimit/apps/14. AI PMO/projects/Weekly Finance Close/01_brief.md`](../../mnt/vimit/apps/14.AI%20PMO/projects/Weekly%20Finance%20Close/01_brief.md)

The brief covers:

1. Why weekly (not a replacement for monthly statutory close)
2. The 7-day rolling cadence vs today's daily/monthly rhythm
3. Closing checklist Mon–Fri, every step labelled ERPNext / QBO / Both
4. 13 working papers (5 NEW, 8 already running)
5. 8-page weekly pack outline
6. 8 locked KPIs
7. Two-anchor structural recons named explicitly (no fake tick-to-zero)
8. Phases — manual run W22-W24, templated W25-W27, PMO-integrated W28+
9. 5 decisions Tanuj owes before W22 closes

## What's NEW vs what already runs

Already live and pulled forward: Daily Performance Audit v3.6 · EOD 17:00 PDF · `/sales-sync` · `/cashflow` · Daily Control Board · VAT recon cron · WhatsApp Action Inbox · WS1 ERP↔QBO AR alignment.

**Net new build:** 6 working-paper xlsx templates + 1 weasyprint PDF generator + 1 Friday 17:00 cron line.

## Decisions locked (2026-05-27)

- **Sign-off:** Tanuj only · Jitu prepares + sends
- **Sheila:** year-end only · gets the W01–W52 archive at audit kick-off
- **Banks:** BOB USD · BOB KES · Co-op · ABC · M-Pesa (5 accounts)
- **Issue log:** lives in both DCB (live) + WP-13 (Fri snapshot)
- **Backfill:** YES · 21 packs (W01-W21 2026) reconstructed in Phase 1.5 in reverse order

## Tracked-as

This will appear in the PMO at `VCL-FIN-CLOSE-001` once the PMO system is live. Until then, status lives in the brief on the share + this cross-reference.

## Phase 2 code lives at

`~/projects/apps/intranet/weekly_close/` — sibling module of `cashflow/`. Not built yet. Phase 1 must run manually for 3 weeks first.
