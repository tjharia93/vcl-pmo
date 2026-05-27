# VCL PMO System — Build Brief

**Project ID:** VCL-DEV-PMO-002
**Build agent:** Codex CLI
**Reviewer:** Tanuj (CFO/COO)
**Issued:** 2026-05-27
**Status:** Brief locked · build can start

---

## 1 · What we are building

A small FastAPI + SQLite + vanilla-HTML module called **`vcl_pmo`**, mounted under the existing intranet shell at `/pmo` on `vcl-intranet:8500`. It is the orchestrator for every VCL development project — including its own build.

It is **not** a clone of Linear, Asana, or Jira. It is the bridge between Tanuj's two existing systems of record, and a UI for AI agents to take work off his plate.

It tracks itself as **VCL-DEV-PMO-002**, the second project in its own register.

---

## 2 · The two-anchor architecture (locked)

VCL operates with **two co-equal anchors**: ERPNext and Excel. PMO data **lives in ERPNext** (custom doctypes) and is **mirrored to Excel** (per-project workbooks). SQLite is a write-through cache for speed and resilience.

```
            ┌──────────────────────────┐
            │        ERPNext           │   ← system of record for PMO data
            │   vcl.frappe.cloud       │      via custom Frappe app
            │                          │      `vcl_pmo_doctypes`:
            │   • PMO Project          │      every read/write
            │   • PMO Requirement      │      goes here first
            │   • PMO Agent Log        │
            │   • per-record links to  │
            │     Sales Invoice,       │
            │     Purchase Invoice,    │
            │     Customer, Task, etc. │
            └────────────┬─────────────┘
                         │ REST (60 s read cache, write-through)
                         ▼
                   ┌──────────┐
                   │ FastAPI  │  ← intranet UI, /pmo
                   │ vcl_pmo  │
                   │ SQLite   │  ← write-through cache only
                   │ cache    │     never authoritative
                   └────┬─────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
  ┌─────────┐     ┌────────────┐    ┌──────────┐
  │  Tanuj  │     │  Excel     │    │  Agents  │
  │ browser │     │  mirror    │    │  Codex / │
  └─────────┘     │ /mnt/vimit │    │  Claude  │
                  │   AI PMO   │    └──────────┘
                  └────────────┘
                   per-project xlsx,
                   auto-regenerated
                   on every change
```

**Rules of the road:**

- **ERPNext is the data home.** The custom doctypes `PMO Project`, `PMO Requirement`, `PMO Agent Log` (see §7) hold the master state.
- **SQLite is a write-through cache, not a master.** Every read goes to ERPNext, response cached 60 s. Every write goes to ERPNext first, then mirrors to Excel + SQLite. If ERPNext is unreachable, the UI serves from cache in **read-only mode** and shows a banner.
- **Excel is a deterministic mirror.** Every PMO mutation triggers a debounced rewrite of the affected per-project xlsx. Tanuj edits in Excel → inotify watcher diffs → applies via REST to ERPNext (which then mirrors back to SQLite). ERPNext stays the canonical store.
- **ERPNext linked finance docs are per-record references**, not bulk-synced. A `PMO Requirement` may reference 0–N existing ERPNext docs via a child table (`doctype`, `name`, `label`).
- **No PMO logic ever auto-submits an ERPNext PI / JE / Salary Slip / Sales Invoice.** Drafts only on those doctypes. Tanuj submits in the ERPNext UI himself. PMO custom doctypes are not financial — they submit freely.
- **All three are always live, always linked.** Banner shows current sync status of each.

---

## 3 · Where everything lives

**One repo holds everything: `~/projects/vcl-pmo/`** ↔ `github.com/tjharia93/vcl-pmo` (private).

| Thing | Path |
|---|---|
| Repo root | `~/projects/vcl-pmo/` |
| FastAPI source | `~/projects/vcl-pmo/app/backend/` |
| Frontend | `~/projects/vcl-pmo/app/static/index.html` |
| SQLite cache | `~/projects/vcl-pmo/app/data/vcl_pmo.db` (gitignored) |
| Frappe custom app | `~/projects/vcl-pmo/frappe_app/vcl_pmo_doctypes/` (installed on vcl.frappe.cloud) |
| Briefs (this file + future) | `~/projects/vcl-pmo/briefs/` |
| Agent work logs | `~/projects/vcl-pmo/context/projects/<pid>/<rid>.md` |
| Design mockups | `~/projects/vcl-pmo/mockups/` |
| Intranet mount | `~/projects/apps/intranet/vcl_pmo` → symlinked to `~/projects/vcl-pmo/app` |
| Excel master | `/mnt/vimit/apps/14. AI PMO/AI Operations Centre.xlsx` |
| Per-project Excel | `/mnt/vimit/apps/14. AI PMO/projects/<Project Name>/<Project Name> PMO.xlsx` |
| Brand v1.1 reference | already in agent memory; see Section 9 |
| Existing intranet shell | `~/projects/apps/intranet/_shell/main.py` |
| ERPNext REST reference impl | `~/projects/apps/intranet/_shell/ppc/services/erpnext.py` |
| Telegram notify helper | `/home/tanujharia/projects/agent_inbox_bot/notify.sh` |

---

## 4 · Source tree to create

The repo is `~/projects/vcl-pmo/` (already scaffolded with `briefs/`, `mockups/`, `context/`, `app/`, `README.md`, `.gitignore`). Codex fills in `app/` and `frappe_app/`.

```
~/projects/vcl-pmo/
├── README.md                            ← done
├── .gitignore                           ← done
├── briefs/
│   └── 2026-05-27_PMO_BUILD_BRIEF_for_Codex.md   ← this file
├── mockups/                             ← design reference (do not modify)
│   ├── index.html
│   ├── mix-a.html  · Steel (layout source)
│   ├── mix-b.html
│   ├── mix-c.html  · Pulse (theme source)
│   ├── mix-d.html
│   └── seed.js
├── context/projects/                    ← agent MD work logs written here at runtime
├── app/                                 ← FastAPI module · symlinked from intranet
│   ├── __init__.py
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py                      ← FastAPI app, routers, middleware
│   │   ├── database.py                  ← SQLAlchemy engine + Base (mirror petty_cash)
│   │   ├── models.py                    ← ORM models (cache rows only)
│   │   ├── schemas.py                   ← Pydantic models
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── projects.py              ← thin pass-through to ERPNext
│   │   │   ├── requirements.py
│   │   │   ├── issues.py
│   │   │   ├── uat.py
│   │   │   ├── agent.py                 ← /agent/complete webhook
│   │   │   ├── sync.py                  ← excel pull/push, erpnext refresh
│   │   │   ├── erpnext.py               ← preview + search for linked finance docs
│   │   │   └── pages.py                 ← serve index.html
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── erpnext_client.py        ← REST wrapper · cache · retry · auth (read .env)
│   │       ├── erpnext_pmo.py           ← typed access to PMO Project / Requirement / Agent Log
│   │       ├── excel_sync.py            ← read + write per-project xlsx, inotify watcher
│   │       ├── github_sync.py           ← commit/push context/projects/<rid>.md
│   │       ├── telegram.py              ← thin wrapper around notify.sh
│   │       └── audit.py                 ← local-only audit_log (cache mutations + sync events)
│   ├── static/
│   │   ├── index.html                   ← the Steel + Pulse fusion (see §9)
│   │   ├── pmo.js                       ← shipped from mockups, wired to live API
│   │   ├── pmo.css                      ← extracted theme tokens
│   │   └── (svg/font assets if any)
│   ├── data/                            ← gitignored · SQLite cache lives here
│   └── templates/
│       └── req_md.j2                    ← MD template for context/projects/<rid>.md
├── frappe_app/                          ← custom Frappe app · pushed to Frappe Cloud
│   └── vcl_pmo_doctypes/
│       ├── hooks.py
│       ├── modules.txt
│       ├── patches.txt
│       └── vcl_pmo_doctypes/
│           └── doctype/
│               ├── pmo_project/         ← PMO Project doctype JSON + Python
│               ├── pmo_requirement/     ← PMO Requirement doctype + child tables
│               ├── pmo_requirement_link/  ← child table for ERPNext doc links
│               └── pmo_agent_log/       ← PMO Agent Log doctype
└── tests/
    └── test_smoke.py                    ← health + 1 round-trip per route
```

**Intranet wiring (one-time):**

```bash
ln -s ~/projects/vcl-pmo/app ~/projects/apps/intranet/vcl_pmo
```

Then in `~/projects/apps/intranet/_shell/main.py` mount alongside the existing apps:

```python
from vcl_pmo.app.backend.main import app as pmo_app
shell.mount("/pmo", pmo_app)
```

---

## 5 · SQLite schema

SQLAlchemy ORM. Mirror the table-creation pattern from `petty_cash/app/backend/database.py`.

```sql
CREATE TABLE projects (
  id            TEXT PRIMARY KEY,          -- e.g. VCL-DEV-PMO-002
  name          TEXT NOT NULL,
  system        TEXT,
  requestor     TEXT,
  go_live       DATE,
  status        TEXT DEFAULT 'Active',     -- Active | In Build | Live | Paused | Closed
  priority      TEXT DEFAULT 'High',       -- Critical | High | Medium | Low
  progress      INTEGER DEFAULT 0,         -- 0..100, computed but cached
  context       TEXT,                      -- markdown blob (optional)
  excel_path    TEXT,                      -- /mnt/vimit/…/<Project> PMO.xlsx
  erpnext_project TEXT,                    -- optional ERPNext Project doc name
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME
);

CREATE TABLE requirements (
  id            TEXT PRIMARY KEY,          -- e.g. PMO-002-04 or HR-002
  project_id    TEXT REFERENCES projects(id),
  area          TEXT,
  requirement   TEXT NOT NULL,
  priority      TEXT,                      -- Must Have | Should | Nice
  status        TEXT DEFAULT 'Not Started',-- Not Started | In Progress | In Review | Blocked | Done
  owner         TEXT,                      -- 'codex-cli' | 'claude-code' | a person
  uat_result    TEXT DEFAULT 'Not Tested', -- Not Tested | Pass | Fail
  uat_tester    TEXT,
  uat_date      DATE,
  needs_action  INTEGER DEFAULT 0,         -- bool, surfaces to Inbox
  note          TEXT,
  md_path       TEXT,                      -- path inside vcl-pmo-context/projects/<pid>/<rid>.md
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME
);

CREATE TABLE erpnext_links (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  requirement_id TEXT REFERENCES requirements(id),
  project_id    TEXT REFERENCES projects(id),
  doctype       TEXT NOT NULL,             -- e.g. Sales Invoice, Customer, Project, Task
  name          TEXT NOT NULL,             -- the ERPNext doc name
  label         TEXT,                      -- human friendly label cached locally
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE issues (
  id            TEXT PRIMARY KEY,
  project_id    TEXT REFERENCES projects(id),
  description   TEXT,
  raised_by     TEXT,
  date_raised   DATE,
  owner         TEXT,
  status        TEXT DEFAULT 'Open',       -- Open | Working | Closed
  resolution    TEXT,
  date_resolved DATE,
  erpnext_issue TEXT                        -- optional ERPNext Issue doc name
);

CREATE TABLE uat_cases (
  id            TEXT PRIMARY KEY,
  project_id    TEXT REFERENCES projects(id),
  req_id        TEXT REFERENCES requirements(id),
  description   TEXT,
  tester        TEXT,
  result        TEXT DEFAULT 'Not Tested',
  date_tested   DATE,
  notes         TEXT
);

CREATE TABLE agent_log (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  req_id        TEXT,
  project_id    TEXT,
  agent         TEXT,                      -- 'codex-cli' | 'claude-code' | …
  status        TEXT,                      -- dispatched | in_progress | done | failed
  notes         TEXT,
  files         TEXT,                      -- JSON array
  ts            DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ts            DATETIME DEFAULT CURRENT_TIMESTAMP,
  actor         TEXT,                      -- 'tanuj' | 'codex-cli' | 'excel-watcher' | 'erpnext-sync'
  verb          TEXT,                      -- 'create' | 'update' | 'delete' | 'sync'
  target        TEXT,                      -- 'requirement:HR-002'
  diff          TEXT                       -- JSON diff
);

CREATE TABLE sync_state (
  anchor        TEXT PRIMARY KEY,          -- 'excel:<workbook>' | 'erpnext'
  last_pulled   DATETIME,
  last_pushed   DATETIME,
  last_error    TEXT,
  status        TEXT                       -- 'ok' | 'stale' | 'error'
);
```

Seed the database on first boot. **Seed projects = 4** as per Section 12 below.

---

## 6 · Excel layout + sync rules

### Master workbook
`/mnt/vimit/apps/14. AI PMO/AI Operations Centre.xlsx` — keep the existing 3-sheet pattern Tanuj's memory establishes: **Portfolio**, **Decision Inbox**, **Shift Plan**. The PMO app reads/writes the Portfolio sheet.

### Per-project workbooks
`/mnt/vimit/apps/14. AI PMO/projects/<Project Name>/<Project Name> PMO.xlsx` — 4 sheets per project: **Requirements**, **Issues**, **UAT**, **Agent Log**.

Header row formatting: Calibri 10 bold, white text, **VCL Blue `#2B3990`** fill. Alt rows: white / Surface `#F4F5F8`. Status pills as in §9. Borders 0.5pt Rule `#CBD2E0`.

### Sync rules

| Direction | Trigger | Behaviour |
|---|---|---|
| SQLite → Excel | every mutation in API | enqueue debounced write (5 s), then rewrite affected rows + bump `sync_state.last_pushed` |
| Excel → SQLite | `inotify` on the workbook file `/mnt/vimit/…/<Project>.xlsx` | diff vs cached copy, apply changes, mirror to ERPNext per linked row |
| Manual sync | `POST /pmo/api/sync/excel/push` and `…/pull` | force one direction |
| Conflict | both sides edited within the same debounce window | newer `updated_at` wins, loser written to `audit_log` with `verb='conflict'` |

The `excel_sync.py` service uses `openpyxl` (already used by `petty_cash`). **Do not** use `pandas` — Tanuj has explicitly avoided unnecessary deps in intranet modules.

---

## 7 · ERPNext layer — custom doctypes + linked finance docs

ERPNext is the data home. PMO data lives in three custom doctypes inside a dedicated Frappe app. Other doctypes (Sales Invoice, Customer, Salary Structure, etc.) are referenced per-record but never owned by the PMO.

### 7.1 Connection

REST with API key + secret, identical pattern to `~/projects/apps/intranet/_shell/ppc/services/erpnext.py`.

**Live env (already on this host):** `/opt/vcl/config/.env` (perm 600) holds:

```
ERPNEXT_URL=https://vcl.frappe.cloud
ERPNEXT_API_KEY=…
ERPNEXT_API_SECRET=…
```

The reference helper accepts either `ERPNEXT_*` **or** `FRAPPE_*` prefix (`os.environ.get("ERPNEXT_URL") or os.environ.get("FRAPPE_URL")`). Use the same fallback pattern. **Do not duplicate** credentials elsewhere.

### 7.2 Custom Frappe app — `vcl_pmo_doctypes`

Lives at `~/projects/vcl-pmo/frappe_app/vcl_pmo_doctypes/`. Installed on `vcl.frappe.cloud`. Three doctypes:

#### `PMO Project` (single-table)

| Fieldname | Type | Notes |
|---|---|---|
| `project_id` | Data | PRIMARY KEY · e.g. `VCL-DEV-PMO-002` |
| `project_name` | Data | required |
| `system` | Data | e.g. "FastAPI + SQLite + ERPNext links" |
| `requestor` | Data | role or name |
| `go_live` | Date | target |
| `status` | Select | Active / In Build / Live / Paused / Closed |
| `priority` | Select | Critical / High / Medium / Low |
| `progress` | Percent | computed nightly + on requirement update |
| `context` | Long Text | markdown blob |
| `excel_path` | Data | mirror file location |
| `linked_erpnext_project` | Link → Project | optional, for ERPNext-side Gantt |

#### `PMO Requirement`

| Fieldname | Type | Notes |
|---|---|---|
| `requirement_id` | Data | PRIMARY KEY · e.g. `PMO-002-04` |
| `project` | Link → PMO Project | required |
| `area` | Data | e.g. Payroll, Excel sync |
| `requirement` | Text | the ask |
| `priority` | Select | Must Have / Should / Nice |
| `status` | Select | Not Started / In Progress / In Review / Blocked / Done |
| `owner` | Data | agent name or user |
| `uat_result` | Select | Not Tested / Pass / Fail |
| `uat_tester` | Link → User | optional |
| `uat_date` | Date | optional |
| `needs_action` | Check | bool — surfaces to Inbox |
| `note` | Long Text | latest free-form note |
| `md_path` | Data | path inside `context/projects/<pid>/<rid>.md` |
| `erpnext_links` | Table → PMO Requirement Link | child table, 0–N rows |

#### `PMO Requirement Link` (child table)

| Fieldname | Type | Notes |
|---|---|---|
| `link_doctype` | Link → DocType | e.g. Sales Invoice |
| `link_name` | Dynamic Link → link_doctype | the doc name |
| `link_label` | Data | cached human label |

#### `PMO Agent Log` (append-only)

| Fieldname | Type | Notes |
|---|---|---|
| `requirement` | Link → PMO Requirement | optional |
| `project` | Link → PMO Project | optional |
| `agent` | Data | `codex-cli` / `claude-code` / … |
| `status` | Select | dispatched / in_progress / done / failed |
| `notes` | Long Text | what the agent did |
| `files_changed` | Long Text | JSON array, rendered as list in form |
| `ts` | Datetime | default now |

### 7.3 Permissions (D4: system users only)

On all four doctypes:
- **System Manager**: read · write · create · submit · cancel · delete
- **PMO User** (new custom role): read · write · create (no delete, no cancel of agent logs)
- **All other roles**: no access

Apply the same gate at the intranet shell: `/pmo/*` requires the session user to have either `System Manager` or `PMO User`. Other staff get 403 with a "Not authorised for PMO" page.

### 7.4 Linked finance / HR doctypes (read-everywhere)

Per-record references via the `erpnext_links` child table. The PMO never owns these — only reads them. Preview cards surface in the drawer.

| Doctype | Fields surfaced in preview |
|---|---|
| Sales Invoice | customer, posting_date, grand_total, outstanding_amount, docstatus |
| Purchase Invoice | supplier, bill_no, posting_date, grand_total, outstanding_amount, docstatus |
| Customer / Supplier | name, primary_address (short), tax_id (PIN), default_sales_partner |
| Salary Structure | name, company, is_active, formula_check (custom: counts statistical-component refs in formulas) |
| Payroll Entry | name, posting_date, total_salary, no_of_employees, docstatus |
| Project / Task / Issue | project_name (or subject), status, %_complete, expected_end_date |
| Sales Order / Job Card Label / Customer Product Spec | name, customer, status, docstatus |

Preview fetch is cached 60 s in SQLite. Cache key = `<doctype>:<name>`.

### 7.5 Mutation rules

| Target | Allowed | Forbidden |
|---|---|---|
| `PMO Project` / `PMO Requirement` / `PMO Agent Log` | full CRUD + submit | — |
| `Project` / `Task` / `Issue` (linked) | create draft, update fields, comment | submit, delete |
| `Sales Invoice` / `Purchase Invoice` / `Payroll Entry` / `Salary Slip` / `Journal Entry` | comment only (audit trail) | create, update, submit, cancel |
| `Salary Structure` (linked) | comment only | update, submit |
| `Customer` / `Supplier` | comment only | update |

**Tanuj submits all financial / HR docs in the ERPNext UI himself.** The PMO never auto-submits. Period.

---

## 8 · Frontend — Steel + Pulse fusion (locked design)

Tanuj reviewed the 4 mockups at `~/projects/vcl_pmo_mockups/`. Selection: **Steel + Pulse fusion**.

### What that means concretely

| Element | Take from | Notes |
|---|---|---|
| Layout shell | Steel (Mix A) | Left rail nav, sticky topbar, main canvas, right-slide drawer |
| Theme | Pulse (Mix C) | Dark navy background (`--bg:#0A1130`), sage accents, white-on-dark text |
| Default landing | Steel | **Inbox** — items that need Tanuj (status = Blocked, In Review, or `needs_action=1`) |
| Live ticker | Pulse | Thin terminal-style bar above the topbar — UTC clock + 6–8 live KPIs |
| Mission KPI tiles | Pulse | Big monospace numerals + SVG sparklines |
| Inline status edit | Both | Click chip → dropdown → optimistic update + audit_log |
| Command palette | Both | `Cmd/Ctrl+K` opens centred overlay; actions, requirements, projects, **ERPNext docs** |
| Keyboard nav | Steel | `g i / g r / g p / g m / g t / g b` jumps between views |
| Right drawer | Both | Opens on row click; tabs inside drawer: **Detail · ERPNext links · Activity · Agent** |
| Brand | v1.1 | Navy / Blue / Sage / Amber / Green; no decorative red |
| Fonts | Pulse | `DM Sans` for UI, `DM Mono` for numerals and IDs |

### Pages / URLs (mounted under `/pmo`)

```
/pmo/                          → SPA shell, default view = Inbox
/pmo/static/{path}             → static files
/pmo/projects/{id}             → drilldown (project drawer pre-opened)
/pmo/requirements/{id}         → drilldown (req drawer pre-opened)
```

The SPA itself is one HTML file (`index.html`) loaded with seed.js — view switching is client-side via `history.pushState`. Search-engine indexing not required; this is internal.

### ERPNext link UX inside the drawer

When the drawer opens for a requirement:

```
┌─ HR-002 ────────────────────────────────────────────────┐
│ Salary Structure formulas                               │
│ VCL-DEV-HR-001 · Payroll · Must Have                    │
├─ Detail · ERPNext links · Activity · Agent ─────────────┤
│                                                         │
│ 📎 ERPNext links                            + Add link  │
│                                                         │
│ ┌─ Salary Structure ─────────────────────────────────┐ │
│ │ VCL Salary Structure          ● Active             │ │
│ │ company: VCL · formula_errors: 1                  │ │
│ │                                Open in ERPNext ↗  │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌─ Salary Structure ─────────────────────────────────┐ │
│ │ BIL Salary Structure          ● Active             │ │
│ │ company: BIL · formula_errors: 1                  │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌─ Salary Structure ─────────────────────────────────┐ │
│ │ BVL Salary Structure          ● Active             │ │
│ │ company: BVL · formula_errors: 1                  │ │
│ └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**+ Add link** opens an inline search box → fuzzy search via `/pmo/api/erpnext/search?q=…` → click result to attach → row appears immediately (optimistic).

---

## 9 · API surface

All under `/pmo/api`. JSON in / JSON out. CORS not needed (same origin under intranet shell).

```
# Projects
GET    /api/projects                       list (with computed req counts)
GET    /api/projects/{id}                  single
POST   /api/projects                       create
PATCH  /api/projects/{id}                  update

# Requirements
GET    /api/requirements                   list (?project_id=&status=&needs_action=)
GET    /api/requirements/{id}              single (with erpnext links inflated)
POST   /api/requirements                   create
PATCH  /api/requirements/{id}              update
GET    /api/requirements/{id}/export       task packet JSON for AI agent
DELETE /api/requirements/{id}              delete (soft, audit-logged)

# Issues
GET    /api/issues                         list
POST   /api/issues                         create
PATCH  /api/issues/{id}                    update

# UAT
GET    /api/uat                            list
POST   /api/uat                            create
PATCH  /api/uat/{id}                       update

# ERPNext layer
GET    /api/erpnext/preview                ?doctype=&name=  → JSON preview, 60 s cache
GET    /api/erpnext/search                 ?q=&doctypes=    → fuzzy results (Sales Invoice, Customer, Task, …)
POST   /api/erpnext/link                   body { req_id, doctype, name, label }
DELETE /api/erpnext/link/{id}              detach

# Sync
GET    /api/sync/status                    last pulled/pushed per anchor
POST   /api/sync/excel/push                force SQLite → Excel
POST   /api/sync/excel/pull                force Excel → SQLite
POST   /api/sync/erpnext/push              force SQLite → ERPNext (Task status mirror only)
POST   /api/sync/erpnext/pull              optional — refresh ERPNext cache

# Agent
POST   /api/agent/complete                 webhook (see §10)
GET    /api/agent/log                      recent agent activity

# Aggregate
GET    /api/summary                        counts for dashboard
GET    /api/feed                           merged audit_log + agent_log, paginated

# Health
GET    /api/health                         { ok, db, excel_status, erpnext_status }
```

---

## 10 · Agent webhook contract

`POST /pmo/api/agent/complete`

```json
{
  "req_id":        "HR-002",
  "status":        "Done",
  "agent":         "codex-cli",
  "notes":         "Fixed Salary Structure formulas on VCL/BIL/BVL.",
  "uat_result":    "Pass",
  "files_changed": [
    "ERPNext: Salary Structure/VCL Salary Structure",
    "ERPNext: Salary Structure/BIL Salary Structure",
    "ERPNext: Salary Structure/BVL Salary Structure"
  ],
  "erpnext_writes": [
    {"doctype":"Salary Structure","name":"VCL Salary Structure","action":"updated"},
    {"doctype":"Salary Structure","name":"BIL Salary Structure","action":"updated"},
    {"doctype":"Salary Structure","name":"BVL Salary Structure","action":"updated"}
  ]
}
```

Handler does, in order (ERPNext-first because ERPNext is the source of truth):

1. **ERPNext write** — update the `PMO Requirement` doctype (`status`, `uat_result`, `note`)
2. **ERPNext write** — insert a `PMO Agent Log` row (immutable record)
3. **Linked-doc comments** — for each entry in `erpnext_writes`, post a Frappe Comment on that linked doc with the action description (audit trail)
4. **SQLite cache** — refresh the cached row from the ERPNext response
5. **Context MD** — append Markdown work-log entry to `~/projects/vcl-pmo-context/projects/<pid>/<rid>.md`
6. **Git** — `git -C ~/projects/vcl-pmo add context/projects/<pid>/<rid>.md && git commit -m "{rid}: {status}" && git push` (push to `origin/main` since the remote is configured)
7. **Excel mirror** — rewrite the affected row in the per-project xlsx (debounced 5 s if multiple updates in burst)
8. **Telegram** — `/home/tanujharia/projects/agent_inbox_bot/notify.sh "<rid> → <status> · <notes[:120]>"`
9. **Return** — `{ "ok": true, "req_id": "<rid>", "status": "<status>", "erpnext_doc": "<frappe-name>" }`

Each step is wrapped. Failures past step 1+2 are logged to `audit_log` and surface in the UI sync banner, but do not roll back the ERPNext write. If step 1 fails, the whole call returns 502 — the agent should retry.

---

## 11 · Build phases (Codex roadmap)

Build in this order. After each phase, run the verification checklist (§12) and stop for Tanuj to inspect.

### Phase 0 · Repo + scaffold (30 min)
- Repo already initialised at `~/projects/vcl-pmo/` and pushed to `github.com/tjharia93/vcl-pmo` (private).
- Pull latest. Symlink `~/projects/apps/intranet/vcl_pmo → ~/projects/vcl-pmo/app`.
- Create the `app/` source tree (§4).
- `app/backend/main.py` exposes `GET /pmo/api/health` returning `{ok: true, frappe: <status>, excel: <status>}`.

**Verify:** `curl http://localhost:8500/pmo/api/health` → 200 OK.

### Phase 1 · Frappe custom app (3 h) — D3
- Scaffold `~/projects/vcl-pmo/frappe_app/vcl_pmo_doctypes/` via `bench new-app` locally, or write the doctype JSON by hand following the field tables in §7.2.
- Three doctypes: `PMO Project`, `PMO Requirement` (with child table `PMO Requirement Link`), `PMO Agent Log`.
- Custom role `PMO User`. Permissions per §7.3 — system users only.
- Push to Frappe Cloud either by uploading the app to the bench, or by directly creating each doctype via `frappe.client.insert` against `DocType` (acceptable shortcut for v0; bench install is the proper Phase-2 follow-up).
- Seed: create `PMO Project` for `VCL-DEV-PMO-002`, `VCL-DEV-HR-001`, `VCL-DEV-IMP-001`, `VCL-DEV-AR-001`.
- Seed: create all `PMO Requirement` rows from §13 + §13bis (HR seed).

**Verify:** Log into ERPNext, search "PMO Requirement" → 25 rows visible. Search "PMO Project" → 4 rows. Try as a non-system-user → 403.

### Phase 2 · ERPNext client + read-through cache (2 h)
- `services/erpnext_client.py` — generic REST wrapper. Methods: `get_doc`, `list_docs`, `update_doc`, `insert_doc`, `add_comment`. 60-s in-memory cache for reads. Retry on 5xx with exponential backoff.
- `services/erpnext_pmo.py` — typed helpers for the three custom doctypes.
- `/api/projects`, `/api/requirements`, `/api/agent/log` pass through to ERPNext (cached).
- SQLite mirrors the response (write-through cache) so the UI is fast even on cold reads.

**Verify:** `curl /pmo/api/requirements?project_id=VCL-DEV-PMO-002` returns the 10 seeded rows, fetched live from Frappe.

### Phase 3 · Frontend (Steel + Pulse fusion) (4 h)
- Lift `mix-a.html` (Steel layout) and re-skin with `mix-c.html` (Pulse theme) tokens.
- Wire every fetch to the live `/pmo/api/*` endpoints. No `seed.js` runtime path in production — keep it only as a fallback when `frappe` status is down.
- Views: **Inbox** (default) · Requirements · Projects · Mission · Timeline · Briefing.
- `Cmd+K` / `Ctrl+K` palette: search across requirements, projects, and ERPNext docs (calls `/api/erpnext/search`).
- Inline status edit → PATCH → optimistic UI → background mirror to ERPNext.
- Right drawer with 4 tabs: **Detail · ERPNext links · Activity · Agent**.
- Live ticker top bar (Pulse) showing clock, KPI counts, current build status.

**Verify:** Open `http://vcl-intranet:8500/pmo/`. Change a status pill. Reload. Value persists (it round-tripped through ERPNext).

### Phase 4 · Excel mirror (3 h)
- `services/excel_sync.py` — write per-project xlsx on every PMO mutation (debounced 5 s).
- VCL brand v1.1 header formatting (Blue fill, white bold, Calibri 10).
- `inotify` watcher on `/mnt/vimit/apps/14. AI PMO/projects/*/` — when a workbook changes externally, diff vs cached copy, push diffs to ERPNext via the PMO doctypes.
- **Lock conflict handling (D5):** if openpyxl reports the file is locked, retry every 30 s. Up to 10 attempts (5 min). Each attempt logged to `audit_log`. After 10 fails, Telegram alert "Excel locked > 5 min — close workbook". App writes never block — only the Excel mirror lags.
- `/api/sync/status` shows last_pulled / last_pushed / status per workbook.

**Verify:** Edit `VCL PMO System PMO.xlsx` in Excel, save, close → within 30 s the UI shows the change. Vice versa: change in UI → workbook updates within 10 s.

### Phase 5 · Linked finance-doc previews + search (3 h)
- `/api/erpnext/preview?doctype=…&name=…` returns the field-set per §7.4.
- `/api/erpnext/search?q=` does fuzzy match across { Sales Invoice, Purchase Invoice, Customer, Supplier, Salary Structure, Payroll Entry, Project, Task, Issue }.
- Drawer "ERPNext links" tab: list child rows as preview cards · `+ Add link` opens inline search → click → POST `/api/erpnext/link`.
- Seed examples: attach 3 Salary Structure docs to `HR-002`. Attach the ERPNext `Project` for HR Payroll to `VCL-DEV-HR-001`.

**Verify:** Open the HR-002 drawer → see live cards for VCL / BIL / BVL Salary Structures with their current `is_active` and `formula_check` values.

### Phase 6 · Agent webhook + context repo (2 h)
- `POST /api/agent/complete` implements §10.
- `templates/req_md.j2` renders the per-requirement MD file.
- `services/github_sync.py` commits + pushes to `origin/main` of the repo (the same one Codex is working in).
- Telegram notify integration.

**Verify:** Curl the webhook with the §12 step 7 payload → ERPNext shows new `PMO Agent Log` row, the requirement status flips, the MD file appears in `context/projects/`, a commit lands on GitHub, Telegram message arrives.

### Phase 7 · UAT + Issues (2 h)
- UAT cases as a child table on `PMO Requirement` OR a separate doctype `PMO UAT Case` — Codex picks; child table is simpler.
- UAT tab in drawer (list cases, mark Pass/Fail inline → ERPNext update).
- Issues view (table + create via UI; backed by ERPNext `Issue` linked to `PMO Project`).
- Sign-off banner on Inbox when project's UAT cases are 100 % Pass.

### Phase 8 · Polish (3 h)
- Live ticker on top (UTC clock + KPI strip — Pulse pattern, scrolls if overflow).
- Sparklines on Mission KPIs (SVG, no chart libs).
- "Render to PDF" button on Briefing (use weasyprint pattern from `hr_payroll` — see §15) — **per D2, build the button but keep the existing 17:00 EOD cron in place until parallel-tested for a week**.
- "Send to Telegram" wired.
- Stale-cache banner when ERPNext is unreachable (read-only mode).

**Total: ~22 hours of build. Realistically 2–3 working days.**

---

## 12 · Verification checklist (run after every phase)

```bash
# 1. Intranet still healthy
curl -s http://localhost:8500/healthz | grep ok

# 2. PMO health includes excel + erpnext status
curl -s http://localhost:8500/pmo/api/health | python3 -m json.tool

# 3. 4 seed projects
curl -s http://localhost:8500/pmo/api/projects | python3 -c "import json,sys;print(len(json.load(sys.stdin)))"

# 4. VCL-DEV-PMO-002 has 10 requirements
curl -s "http://localhost:8500/pmo/api/requirements?project_id=VCL-DEV-PMO-002" | python3 -c "import json,sys;print(len(json.load(sys.stdin)))"

# 5. Excel master exists and has Portfolio sheet
test -f "/mnt/vimit/apps/14. AI PMO/AI Operations Centre.xlsx" && echo OK

# 6. ERPNext reachable (only after Phase 4)
curl -s http://localhost:8500/pmo/api/erpnext/preview?doctype=Project\&name=VCL+PMO+System | python3 -m json.tool

# 7. Agent webhook round-trips (only after Phase 5)
curl -s -X POST http://localhost:8500/pmo/api/agent/complete \
  -H "Content-Type: application/json" \
  -d '{"req_id":"PMO-002-04","status":"Done","agent":"codex-cli","notes":"verify","files_changed":[]}'

# 8. SQLite → Excel push
curl -s -X POST http://localhost:8500/pmo/api/sync/excel/push | python3 -m json.tool

# 9. Frontend
curl -s http://localhost:8500/pmo/ | grep -i "VCL PMO" && echo OK
```

---

## 13 · Seed data for VCL-DEV-PMO-002 (the PMO project tracking itself)

```python
SEED_REQS_PMO = [
  ("PMO-002-01","VCL-DEV-PMO-002","Scaffold",      "FastAPI app + intranet mount + health route",            "Must Have", "Done",        "codex-cli", "Pass"),
  ("PMO-002-02","VCL-DEV-PMO-002","Database",      "SQLite schema (projects, requirements, erpnext_links…)", "Must Have", "In Progress", "codex-cli", "Not Tested"),
  ("PMO-002-03","VCL-DEV-PMO-002","Frontend",      "Steel+Pulse fusion · Inbox default landing",             "Must Have", "Not Started", "codex-cli", "Not Tested"),
  ("PMO-002-04","VCL-DEV-PMO-002","Excel sync",    "Read/write per-project xlsx + inotify watcher",          "Must Have", "Not Started", "codex-cli", "Not Tested"),
  ("PMO-002-05","VCL-DEV-PMO-002","ERPNext read",  "REST wrapper + /api/erpnext/{preview,search}",           "Must Have", "Not Started", "codex-cli", "Not Tested"),
  ("PMO-002-06","VCL-DEV-PMO-002","Agent webhook", "POST /agent/complete · MD + git + Telegram",             "Must Have", "Not Started", "codex-cli", "Not Tested"),
  ("PMO-002-07","VCL-DEV-PMO-002","ERPNext write", "Task mirror only · no financial doctype writes",         "Should",    "Not Started", "codex-cli", "Not Tested"),
  ("PMO-002-08","VCL-DEV-PMO-002","Command palette","⌘K · search + actions + ERPNext doc lookup",            "Must Have", "Not Started", "codex-cli", "Not Tested"),
  ("PMO-002-09","VCL-DEV-PMO-002","UAT + Issues",  "UAT tab in drawer · sign-off banner · issues view",      "Should",    "Not Started", "codex-cli", "Not Tested"),
  ("PMO-002-10","VCL-DEV-PMO-002","Polish",        "Live ticker · sparklines · Render to PDF · Telegram",    "Should",    "Not Started", "codex-cli", "Not Tested"),
]
```

The 14 HR requirements from the original handoff are seeded under VCL-DEV-HR-001 (already complete; Phase 1's seed should mark them all Done except HR-002 which stays In Review).

---

## 14 · Decisions — all resolved

| # | Decision | Resolution |
|---|---|---|
| D1 | GitHub remote | ✅ **`github.com/tjharia93/vcl-pmo` (private)**. Repo holds code + briefs + context + mockups. |
| D2 | Briefing → PDF | ✅ **Build the button, keep the cron.** Parallel-test for one week before retiring the existing 17:00 EOD pipeline. |
| D3 | ERPNext data shape | ✅ **Custom Frappe app `vcl_pmo_doctypes`** with `PMO Project`, `PMO Requirement` (child table `PMO Requirement Link`), `PMO Agent Log`. ERPNext is the source of truth; SQLite is a cache. |
| D4 | Access | ✅ **System users only** (CFO + IT). Enforced at the doctype level (`System Manager` + custom role `PMO User`) **and** at the intranet shell. No staff in Phase 1. |
| D5 | Excel lock conflict | ✅ **Retry + log + escalate.** Retry every 30 s, up to 10 attempts. Each attempt logged to `audit_log`. After 5 min still locked → Telegram alert "Excel locked > 5 min — close workbook". App stays writable to ERPNext + SQLite; only the Excel mirror lags. |

---

## 15 · Existing patterns to steal from

- **FastAPI + intranet mount**: `~/projects/apps/intranet/petty_cash/app/backend/main.py`
- **SQLAlchemy models**: `~/projects/apps/intranet/petty_cash/app/backend/models.py`
- **ERPNext REST wrapper**: `~/projects/apps/intranet/_shell/ppc/services/erpnext.py`
- **Vanilla SPA frontend**: `~/projects/apps/intranet/hr_payroll/app/static/index.html` (large file; reference for component patterns, not paradigm)
- **Static mount + PrefixRedirectMiddleware**: see petty_cash main.py
- **Boot via systemd**: see `~/projects/apps/intranet/start.sh`
- **Brand v1.1 (palette, fonts, table headers)**: encoded in agent memory `feedback_vcl_brand`; use the tokens listed in §8

---

## 16 · How to start

1. `cd ~/projects/apps/intranet`
2. `mkdir -p vcl_pmo/app/backend/{routes,services} vcl_pmo/app/static vcl_pmo/data vcl_pmo/templates vcl_pmo/tests`
3. Implement Phase 0–8 in order.
4. After each phase, run `bash ~/projects/apps/intranet/start.sh` (or restart the systemd unit), then run §12 checklist.
5. On Phase 8 completion, POST the final completion webhook (§10) with `req_id: PMO-002-10`.

The mockups at `~/projects/vcl_pmo_mockups/` are the visual reference; mix-a (Steel layout) and mix-c (Pulse theme) are the source materials for the fusion.

---

*End of build brief · VCL IT Development Team · 2026-05-27*
