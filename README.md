# vcl-pmo

The VCL Programme Management Office — code, context, and design references in one repo.

<!-- bench-bump 2026-05-27 -->


## Repo structure

| Path | Contents |
|---|---|
| `app/` | FastAPI + SQLite source. Symlinked into the intranet at `~/projects/apps/intranet/vcl_pmo`. Mounted at `/pmo`. |
| `briefs/` | Build briefs, change requests, decisions. Source of truth for what's being built. |
| `context/projects/<pid>/<rid>.md` | Per-requirement Markdown work logs, written by AI agents on completion. |
| `mockups/` | Interactive design references (4 paradigms). **Steel + Pulse fusion is locked** for the build. |
| `frappe_app/` | Custom Frappe app `vcl_pmo_doctypes` for PMO doctypes, native API methods, UAT/OAT, and sync logs. Installed on Frappe Cloud. |
| `docs/` | Testing documentation and n8n Excel sync contract for the Frappe-native migration. |

## The two-anchor model

The PMO links — never replaces — VCL's two systems of record:

1. **ERPNext** (`vcl.frappe.cloud`) — owns the PMO data via custom doctypes (`PMO Project`, `PMO Requirement`, `PMO Agent Log`), and is the per-record link target for every finance / HR / sales doc the PMO touches.
2. **Excel** (`/mnt/vimit/apps/14. AI PMO/`) — human-readable mirror. The Operations Centre workbook + one per-project workbook. Always live, always synced.

**SQLite is a write-through cache, not a master.** Every read goes to ERPNext (cached 60 s); every write goes to ERPNext, then mirrors to Excel + SQLite. If ERPNext is unreachable the app serves from cache in read-only mode.

## Run

```bash
cd ~/projects/apps/intranet && bash start.sh
open http://vcl-intranet:8500/pmo
```

## Status

- Build brief: [`briefs/2026-05-27_PMO_BUILD_BRIEF_for_Codex.md`](briefs/2026-05-27_PMO_BUILD_BRIEF_for_Codex.md)
- Project ID inside the PMO: **VCL-DEV-PMO-002**
- Mockups: `mockups/index.html` — open and click through.

## Access

System users only (CFO + IT). Enforced at the intranet shell during the reference phase and by Frappe roles in the native phase.



## Frappe-native migration

The migration target is `https://vimitconverters.frappe.cloud/app/pmo`.

See:

- [`briefs/2026-05-27_FRAPPE_NATIVE_PMO_MIGRATION.md`](briefs/2026-05-27_FRAPPE_NATIVE_PMO_MIGRATION.md)
- [`docs/PMO_TESTING.md`](docs/PMO_TESTING.md)
- [`docs/N8N_EXCEL_SYNC_CONTRACT.md`](docs/N8N_EXCEL_SYNC_CONTRACT.md)
