frappe.pages["pmo"].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({ parent: wrapper, title: "VCL PMO", single_column: true });
  page.main.addClass("vcl-pmo-page");
  const app = new VCLPMOPage(page);
  app.boot();
};

class VCLPMOPage {
  constructor(page) {
    this.page = page;
    this.state = {
      view: "portfolio:inbox",
      project: null,
      subtab: "overview",
      caseKind: null,
      caseId: null,
      runName: null,
      summary: {},
      projects: [],
      requirements: [],
      uatCases: [],
      oatChecks: [],
      raid: [],
      docs: {},
      packet: null,
      overview: null,
      gantt: null,
      dragging: null,
    };
    this.$root = $(this.shell()).appendTo(this.page.main);
    this.$body = this.$root.find("[data-body]");
    this.bind();
    setInterval(() => this.tick(), 1000);
    window.addEventListener("popstate", (event) => {
      if (event.state && event.state.view) {
        Object.assign(this.state, event.state);
        this.render();
      }
    });
  }

  shell() {
    return `
      <div class="pmo-shell">
        <div class="pmo-ticker">
          <span class="live">LIVE</span>
          <span>UTC <b data-clock>--:--:--</b></span>
          <span>PROJECTS <b data-kpi="projects">0</b></span>
          <span>REQS <b data-kpi="requirements">0</b></span>
          <span>DONE <b data-kpi="done">0</b></span>
          <span>IN REVIEW <b data-kpi="in_review">0</b></span>
          <span>RAID OPEN <b data-kpi="raid_open">0</b></span>
        </div>
        <div class="pmo-topline">
          <div class="pmo-title"><h1>VCL PMO</h1><p>Portfolio, project workspace, test history, RAID, and documentation</p></div>
          <div class="pmo-spacer"></div>
          <button class="pmo-btn primary" data-action="new-requirement">New Requirement</button>
          <button class="pmo-btn" data-action="refresh">Refresh</button>
        </div>
        <div data-tabs></div>
        <div class="pmo-body" data-body></div>
      </div>`;
  }

  bind() {
    this.$root.on("click", "[data-action]", (event) => this.action(event.currentTarget.dataset.action, event.currentTarget));
    this.$root.on("click", "[data-view]", (event) => this.setPortfolioView(event.currentTarget.dataset.view));
    this.$root.on("click", "[data-project]", (event) => this.openProject(event.currentTarget.dataset.project));
    this.$root.on("click", "[data-subtab]", (event) => this.openProject(this.state.project, event.currentTarget.dataset.subtab));
    this.$root.on("click", "[data-req]", (event) => this.openRequirementDrawer(event.currentTarget.dataset.req));
    this.$root.on("click", "[data-milestone]", (event) => this.openRecordDrawer("PMO Milestone", event.currentTarget.dataset.milestone));
    this.$root.on("click", "[data-task]", (event) => this.openRecordDrawer("PMO Task", event.currentTarget.dataset.task));
    this.$root.on("click", "[data-raid]", (event) => this.openRecordDrawer("PMO RAID Item", event.currentTarget.dataset.raid));
    this.$root.on("click", "[data-doc]", (event) => this.openDocument(event.currentTarget.dataset.doc));
    this.$root.on("click", "[data-case]", (event) => this.openCase(event.currentTarget.dataset.kind, event.currentTarget.dataset.case));
    this.$root.on("click", "[data-run]", (event) => this.openRun(event.currentTarget.dataset.kind, event.currentTarget.dataset.run));
    this.$root.on("mousedown", "[data-gantt-task]", (event) => this.startDrag(event));
    $(document).on("mousemove.pmo", (event) => this.dragGantt(event));
    $(document).on("mouseup.pmo", () => this.endDrag());
  }

  async boot() {
    this.tick();
    await this.refresh();
  }

  async refresh() {
    await Promise.all([this.loadSummary(), this.loadPortfolio()]);
    if (this.state.project) await this.loadProject(this.state.project);
    this.render();
  }

  tick() {
    this.$root.find("[data-clock]").text(new Date().toISOString().slice(11, 19));
  }

  async call(method, args = {}) {
    const response = await frappe.call({ method, args });
    return response.message;
  }

  async loadSummary() {
    this.state.summary = await this.call("vcl_pmo_doctypes.api.summary");
    Object.entries(this.state.summary || {}).forEach(([key, value]) => this.$root.find(`[data-kpi="${key}"]`).text(value || 0));
  }

  async loadPortfolio() {
    const [projects, requirements, uatCases, oatChecks, raid, docs] = await Promise.all([
      frappe.db.get_list("PMO Project", { fields: ["name", "project_id", "project_name", "project_short", "system", "status", "priority", "progress", "current_phase", "target_completion"], limit: 200, order_by: "project_id asc" }),
      frappe.db.get_list("PMO Requirement", { fields: ["name", "requirement_id", "project", "area", "requirement", "priority", "status", "requirement_owner", "uat_result", "needs_action"], limit: 800, order_by: "requirement_id asc" }),
      frappe.db.get_list("PMO UAT Case", { fields: ["name", "uat_case_id", "project", "requirement", "description", "latest_result", "latest_run_date", "run_count"], limit: 800, order_by: "uat_case_id asc" }),
      frappe.db.get_list("PMO OAT Check", { fields: ["name", "check_id", "project", "area", "check", "latest_result", "latest_run_date", "run_count"], limit: 800, order_by: "check_id asc" }),
      frappe.db.get_list("PMO RAID Item", { fields: ["name", "raid_id", "project", "type", "title", "severity", "probability", "status", "due_date"], limit: 800, order_by: "due_date asc" }),
      this.call("vcl_pmo_doctypes.api.documents_for"),
    ]);
    Object.assign(this.state, { projects, requirements, uatCases, oatChecks, raid, docs });
  }

  async loadProject(projectId) {
    const [packet, overview, gantt, docs] = await Promise.all([
      this.call("vcl_pmo_doctypes.api.project_packet", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.project_overview", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.project_gantt", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.documents_for", { project_id: projectId }),
    ]);
    Object.assign(this.state, { packet, overview, gantt, docs });
  }

  pushState() {
    history.pushState({ view: this.state.view, project: this.state.project, subtab: this.state.subtab, caseKind: this.state.caseKind, caseId: this.state.caseId, runName: this.state.runName }, "", `/app/pmo#${encodeURIComponent(this.state.view)}`);
  }

  setPortfolioView(view) {
    Object.assign(this.state, { view: `portfolio:${view}`, project: null, caseKind: null, caseId: null, runName: null });
    this.pushState();
    this.render();
  }

  async openProject(projectId, subtab = "overview") {
    Object.assign(this.state, { view: "project", project: projectId, subtab, caseKind: null, caseId: null, runName: null });
    await this.loadProject(projectId);
    this.pushState();
    this.render();
  }

  async openCase(kind, caseName) {
    Object.assign(this.state, { view: "case", caseKind: kind, caseId: caseName, runName: null });
    this.pushState();
    this.render();
  }

  async openRun(kind, runName) {
    Object.assign(this.state, { view: "run", caseKind: kind, runName });
    this.pushState();
    this.render();
  }

  action(name, el) {
    if (name === "refresh") return this.refresh();
    if (name === "new-requirement") return this.modalRequirement();
    if (name === "back-portfolio") return this.setPortfolioView("projects");
    if (name === "new-uat-run") return this.modalRun("uat", el.dataset.case);
    if (name === "new-oat-run") return this.modalRun("oat", el.dataset.case);
    if (name === "new-raid") return this.modalRAID(el.dataset.type || "Risk");
    if (name === "new-doc") return this.modalDocument();
    if (name === "open-desk") return window.open(`/app/${encodeURIComponent(el.dataset.doctype.toLowerCase().replaceAll(" ", "-"))}/${encodeURIComponent(el.dataset.name)}`, "_blank");
    if (name === "close-overlay") return this.closeOverlay();
  }

  render() {
    if (this.state.view.startsWith("portfolio:")) return this.renderPortfolio();
    if (this.state.view === "project") return this.renderProject();
    if (this.state.view === "case") return this.renderCase();
    if (this.state.view === "run") return this.renderRun();
  }

  renderTabs(items, active, attr = "data-view") {
    return `<div class="pmo-tabs">${items.map(item => `<button ${attr}="${item[0]}" class="${item[0] === active ? "active" : ""}">${item[1]}</button>`).join("")}</div>`;
  }

  renderPortfolio() {
    const active = this.state.view.split(":")[1];
    this.$root.find("[data-tabs]").html(this.renderTabs([
      ["inbox", "Inbox"], ["projects", "Projects"], ["roadmap", "Roadmap"], ["raid", "RAID"], ["documentation", "Documentation"], ["test-status", "Test Status"]
    ], active));
    if (active === "inbox") return this.renderPortfolioInbox();
    if (active === "projects") return this.renderPortfolioProjects();
    if (active === "roadmap") return this.renderRoadmap();
    if (active === "raid") return this.renderPortfolioRAID();
    if (active === "documentation") return this.renderDocumentation(null);
    return this.renderTestStatus();
  }

  renderPortfolioInbox() {
    const reqs = this.state.requirements.filter(r => r.needs_action || ["Blocked", "In Review"].includes(r.status));
    const raids = this.state.raid.filter(r => ["Open", "Mitigating"].includes(r.status));
    this.$body.html(`${this.head("Inbox", `${reqs.length + raids.length} portfolio items need attention`)}<div class="pmo-list">${reqs.map(r => this.reqRow(r)).join("")}${raids.map(r => this.raidRow(r)).join("") || "<div class='pmo-card'>Inbox clear.</div>"}</div>`);
  }

  renderPortfolioProjects() {
    this.$body.html(`${this.head("Projects", "Click a project card to open its workspace")}<div class="pmo-grid">${this.state.projects.map(p => this.projectCard(p)).join("")}</div>`);
  }

  renderRoadmap() {
    const projects = this.state.projects;
    this.$body.html(`${this.head("Roadmap", "Portfolio-level progress by project")}<div class="pmo-grid">${projects.map(p => `<div class="pmo-card"><div class="pmo-card-title">${this.esc(p.project_name || p.name)}</div><div class="pmo-muted pmo-mono">${this.esc(p.project_id)}</div><div class="pmo-progress"><i style="width:${Number(p.progress || 0)}%"></i></div><p>${this.esc(p.current_phase || p.status || "")}</p></div>`).join("")}</div>`);
  }

  renderPortfolioRAID() {
    this.$body.html(`${this.head("RAID", "Open risks, assumptions, issues and dependencies")}${this.raidTable(this.state.raid)}`);
  }

  renderTestStatus() {
    this.$body.html(`${this.head("Test Status", "Latest UAT/OAT results across the portfolio")}<div class="pmo-two-col"><div>${this.caseTable("uat", this.state.uatCases)}</div><div>${this.caseTable("oat", this.state.oatChecks)}</div></div>`);
  }

  renderProject() {
    const p = this.state.packet?.project || {};
    this.$root.find("[data-tabs]").html(`<div class="pmo-subtabs"><button data-action="back-portfolio">Portfolio</button>${[["overview","Overview"],["timeline","Timeline"],["open","Open Items"],["milestones","Milestones"],["raid","RAID"],["uat","UAT"],["oat","OAT"],["history","Test History"],["documentation","Documentation"],["activity","Activity"]].map(i => `<button data-subtab="${i[0]}" class="${this.state.subtab === i[0] ? "active" : ""}">${i[1]}</button>`).join("")}</div>`);
    if (this.state.subtab === "overview") return this.renderProjectOverview(p);
    if (this.state.subtab === "timeline") return this.renderTimeline();
    if (this.state.subtab === "open") return this.renderOpenItems();
    if (this.state.subtab === "milestones") return this.renderMilestones();
    if (this.state.subtab === "raid") return this.renderProjectRAID();
    if (this.state.subtab === "uat") return this.renderProjectCases("uat");
    if (this.state.subtab === "oat") return this.renderProjectCases("oat");
    if (this.state.subtab === "history") return this.renderTestHistory();
    if (this.state.subtab === "documentation") return this.renderDocumentation(this.state.project);
    return this.renderActivity();
  }

  renderProjectOverview(p) {
    const overview = this.state.overview || {};
    this.$body.html(`${this.breadcrumb(["Portfolio", p.project_name || p.name])}${this.head(p.project_name || p.name, `${p.current_phase || p.status || ""} · ${p.project_id || p.name}`)}<div class="pmo-two-col"><div class="pmo-card pmo-markdown">${this.renderMD(p.charter || p.context || "No charter captured yet.")}</div><div class="pmo-grid"><div class="pmo-card pmo-kpi"><span>Progress</span><b>${Number(p.progress || 0)}%</b></div><div class="pmo-card"><b>${(overview.milestones || []).length}</b><span>Milestones</span></div><div class="pmo-card"><b>${Object.values(overview.raid_counts || {}).reduce((a,b)=>a+b,0)}</b><span>RAID items</span></div></div></div>`);
  }

  renderTimeline() {
    this.$body.html(`${this.breadcrumb(["Portfolio", this.state.project, "Timeline"])}${this.head("Timeline", "Drag task bars horizontally to reschedule end dates")}${this.ganttSVG()}`);
  }

  renderOpenItems() {
    const reqs = this.state.packet.requirements.filter(r => r.status !== "Done");
    const tasks = this.state.packet.tasks.filter(t => t.status !== "Done" && t.status !== "Cancelled");
    this.$body.html(`${this.head("Open Items", "Requirements and tasks still in flight")}<div class="pmo-two-col"><div><h3>Requirements</h3><div class="pmo-list">${reqs.map(r => this.reqRow(r)).join("")}</div></div><div><h3>Tasks</h3><div class="pmo-list">${tasks.map(t => this.taskRow(t)).join("")}</div></div></div>`);
  }

  renderMilestones() {
    this.$body.html(`${this.head("Milestones", "Project milestone register")}<table class="pmo-table"><thead><tr><th>ID</th><th>Name</th><th>Target</th><th>Actual</th><th>Status</th><th>Weight</th></tr></thead><tbody>${this.state.packet.milestones.map(m => `<tr data-milestone="${m.name}"><td class="pmo-mono">${this.esc(m.milestone_id)}</td><td>${this.esc(m.milestone_name)}</td><td>${this.date(m.target_date)}</td><td>${this.date(m.actual_date)}</td><td>${this.chip(m.status)}</td><td>${Number(m.weight || 0)}%</td></tr>`).join("")}</tbody></table>`);
  }

  renderProjectRAID() {
    const tabs = ["Risk", "Assumption", "Issue", "Dependency"];
    this.$body.html(`${this.head("RAID", "Project-scoped risk, assumption, issue and dependency register")}<div class="pmo-actions">${tabs.map(t => `<button class="pmo-btn" data-action="new-raid" data-type="${t}">New ${t}</button>`).join("")}</div>${tabs.map(t => `<h3>${t}</h3>${this.raidTable(this.state.packet.raid.filter(r => r.type === t))}`).join("")}`);
  }

  renderProjectCases(kind) {
    const rows = kind === "uat" ? this.state.packet.uat_cases : this.state.packet.oat_checks;
    this.$body.html(`${this.head(kind.toUpperCase(), `${kind.toUpperCase()} definitions and latest run state`)}${this.caseTable(kind, rows)}`);
  }

  async renderCase() {
    const kind = this.state.caseKind;
    const rows = kind === "uat" ? this.state.packet.uat_cases : this.state.packet.oat_checks;
    const row = rows.find(r => r.name === this.state.caseId || r.uat_case_id === this.state.caseId || r.check_id === this.state.caseId) || {};
    const caseId = row.uat_case_id || row.check_id || row.name;
    const history = await this.call("vcl_pmo_doctypes.api.case_history", { case_id: row.name, kind });
    this.$root.find("[data-tabs]").html("");
    this.$body.html(`${this.breadcrumb(["Portfolio", this.state.project, kind.toUpperCase(), caseId])}${this.head(caseId, row.description || row.check || "Case detail")}<div class="pmo-card pmo-markdown">${this.renderMD(row.acceptance_criteria || "No acceptance criteria captured yet.")}</div><div class="pmo-actions"><button class="pmo-btn primary" data-action="new-${kind}-run" data-case="${row.name}">New Run</button></div><table class="pmo-table"><thead><tr><th>#</th><th>Date</th><th>Tester</th><th>Result</th><th>Evidence</th></tr></thead><tbody>${history.map(run => `<tr data-run="${run.name}" data-kind="${kind}"><td>${run.run_number}</td><td>${this.date(run.run_date)}</td><td>${this.esc(run.tester)}</td><td>${this.chip(run.result)}</td><td>${this.esc((run.evidence || "").slice(0,90))}</td></tr>`).join("")}</tbody></table>`);
  }

  async renderRun() {
    const dt = this.state.caseKind === "uat" ? "PMO UAT Run" : "PMO OAT Run";
    const run = await frappe.db.get_doc(dt, this.state.runName);
    this.$root.find("[data-tabs]").html("");
    this.$body.html(`${this.breadcrumb(["Portfolio", this.state.project, this.state.caseKind.toUpperCase(), `Run #${run.run_number}`])}${this.head(run.run_id, `${run.result} · ${this.date(run.run_date)} · ${run.environment || ""}`)}<div class="pmo-two-col"><div class="pmo-card pmo-markdown">${this.renderMD(run.evidence || "No evidence captured.")}</div><div class="pmo-card"><p><b>Tester</b><br>${this.esc(run.tester)}</p><p><b>Result</b><br>${this.chip(run.result)}</p><p><b>Notes</b><br>${this.esc(run.notes || "")}</p></div></div>`);
  }

  renderTestHistory() {
    this.$body.html(`${this.head("Test History", "Open UAT/OAT cases to inspect their run history")}<div class="pmo-two-col"><div>${this.caseTable("uat", this.state.packet.uat_cases)}</div><div>${this.caseTable("oat", this.state.packet.oat_checks)}</div></div>`);
  }

  renderDocumentation(projectId) {
    const docs = this.state.docs || {};
    this.$body.html(`${this.head("Documentation", "PMO documents stored in Frappe markdown fields")}<div class="pmo-actions"><button class="pmo-btn primary" data-action="new-doc">New Document</button></div>${Object.entries(docs).map(([type, rows]) => `<h3>${this.esc(type)}</h3><div class="pmo-grid">${rows.map(d => `<div class="pmo-card" data-doc="${d.name}"><div class="pmo-card-title">${this.esc(d.title)}</div><p>${this.esc(d.status)} · v${this.esc(d.version || "1.0")}</p></div>`).join("")}</div>`).join("") || "<div class='pmo-card'>No PMO Documents yet.</div>"}`);
  }

  async openDocument(name) {
    const doc = await frappe.db.get_doc("PMO Document", name);
    this.drawer("PMO Document", doc.title, `<div class="pmo-markdown">${this.renderMD(doc.content_md || "")}</div>`, [{ label: "Open in Desk", action: "open-desk", doctype: "PMO Document", name }]);
  }

  renderActivity() {
    const activity = this.state.overview?.recent_activity || [];
    this.$body.html(`${this.head("Activity", "Agent and sync events for this project")}<div class="pmo-list">${activity.map(a => `<div class="pmo-row"><div class="pmo-dot">${this.esc((a.status || a.direction || "A").slice(0,1))}</div><div><b>${this.esc(a.agent || a.anchor || a.name)}</b><small>${this.date(a.ts)} · ${this.esc(a.notes || a.detail || "")}</small></div>${this.chip(a.status || "ok")}</div>`).join("")}</div>`);
  }

  head(title, sub) { return `<div class="pmo-head"><div><h2>${this.esc(title)}</h2><p>${this.esc(sub || "")}</p></div></div>`; }
  breadcrumb(parts) { return `<div class="pmo-breadcrumbs">${parts.map((p, i) => i === 0 ? `<button data-action="back-portfolio">${this.esc(p)}</button>` : `<span>›</span><span>${this.esc(p)}</span>`).join("")}</div>`; }
  projectCard(p) { return `<div class="pmo-card" data-project="${p.name}"><div class="pmo-card-title">${this.esc(p.project_name || p.name)}</div><div class="pmo-muted pmo-mono">${this.esc(p.project_id || p.name)}</div><p>${this.esc(p.system || "")}</p><div class="pmo-progress"><i style="width:${Number(p.progress || 0)}%"></i></div><div>${this.chip(p.status)} ${this.chip(p.priority)}</div></div>`; }
  reqRow(r) { return `<div class="pmo-row" data-req="${r.name}"><div class="pmo-dot">${this.esc((r.requirement_id || "?").split("-").pop())}</div><div><b>${this.esc(r.requirement)}</b><small>${this.esc(r.requirement_id)} · ${this.esc(r.project)} · ${this.esc(r.area || "")}</small></div>${this.chip(r.status)}</div>`; }
  taskRow(t) { return `<div class="pmo-row" data-task="${t.name}"><div class="pmo-dot">T</div><div><b>${this.esc(t.title)}</b><small>${this.date(t.start_date)} → ${this.date(t.end_date)} · ${this.esc(t.assignee || "")}</small></div>${this.chip(t.status)}</div>`; }
  raidRow(r) { return `<div class="pmo-row" data-raid="${r.name}"><div class="pmo-dot">R</div><div><b>${this.esc(r.title)}</b><small>${this.esc(r.raid_id)} · ${this.esc(r.type)} · due ${this.date(r.due_date)}</small></div>${this.chip(r.severity || r.status)}</div>`; }
  raidTable(rows) { return `<table class="pmo-table"><thead><tr><th>ID</th><th>Type</th><th>Title</th><th>Severity</th><th>Probability</th><th>Status</th><th>Due</th></tr></thead><tbody>${rows.map(r => `<tr data-raid="${r.name}"><td class="pmo-mono">${this.esc(r.raid_id)}</td><td>${this.esc(r.type)}</td><td>${this.esc(r.title)}</td><td>${this.chip(r.severity)}</td><td>${this.esc(r.probability || "")}</td><td>${this.chip(r.status)}</td><td>${this.date(r.due_date)}</td></tr>`).join("")}</tbody></table>`; }
  caseTable(kind, rows) { const id = kind === "uat" ? "uat_case_id" : "check_id"; const text = kind === "uat" ? "description" : "check"; return `<table class="pmo-table"><thead><tr><th>ID</th><th>Definition</th><th>Latest</th><th>Last Run</th><th>Runs</th></tr></thead><tbody>${rows.map(r => `<tr data-case="${r.name}" data-kind="${kind}"><td class="pmo-mono">${this.esc(r[id])}</td><td>${this.esc(r[text])}</td><td>${this.chip(r.latest_result || "Not Yet Run")}</td><td>${this.date(r.latest_run_date)}</td><td>${Number(r.run_count || 0)}</td></tr>`).join("")}</tbody></table>`; }

  ganttSVG() {
    const tasks = this.state.gantt?.tasks || [];
    const milestones = this.state.gantt?.milestones || [];
    if (!tasks.length && !milestones.length) return `<div class="pmo-card">No milestones or tasks yet.</div>`;
    const dates = [...tasks.flatMap(t => [t.start_date, t.end_date]), ...milestones.map(m => m.target_date)].filter(Boolean).map(d => new Date(d));
    const min = new Date(Math.min(...dates)); const max = new Date(Math.max(...dates));
    const day = 86400000; const span = Math.max(1, Math.round((max - min) / day) + 3);
    const left = 190, top = 34, rowH = 34, scale = 26, width = left + span * scale + 80, height = top + (tasks.length + milestones.length) * rowH + 30;
    const x = d => left + Math.round((new Date(d) - min) / day) * scale;
    const rows = [];
    milestones.forEach((m, i) => { const y = top + i * rowH; rows.push(`<text x="12" y="${y+18}">${this.esc(m.milestone_name || m.milestone_id)}</text><polygon data-milestone="${m.name}" class="bar-milestone" points="${x(m.target_date)},${y+6} ${x(m.target_date)+10},${y+16} ${x(m.target_date)},${y+26} ${x(m.target_date)-10},${y+16}"></polygon>`); });
    tasks.forEach((t, i) => { const y = top + (milestones.length + i) * rowH; const sx = x(t.start_date), ex = Math.max(sx + 18, x(t.end_date)); rows.push(`<text x="12" y="${y+18}">${this.esc(t.title)}</text><rect data-gantt-task="${t.name}" data-start="${t.start_date}" data-end="${t.end_date}" class="${t.status === "Blocked" ? "bar-critical" : "bar-task"}" x="${sx}" y="${y+7}" width="${ex-sx}" height="18" rx="3"></rect><text x="${ex+6}" y="${y+21}">${Number(t.percent_complete || 0)}%</text>`); });
    return `<div class="pmo-gantt"><svg viewBox="0 0 ${width} ${height}" width="${width}" height="${height}"><line x1="${left}" y1="10" x2="${left}" y2="${height}" stroke="var(--vcl-rule)"></line>${rows.join("")}</svg></div>`;
  }

  startDrag(event) { this.state.dragging = { el: event.currentTarget, startX: event.clientX, origWidth: Number(event.currentTarget.getAttribute("width")) }; }
  dragGantt(event) { const d = this.state.dragging; if (!d) return; d.el.setAttribute("width", Math.max(18, d.origWidth + event.clientX - d.startX)); }
  async endDrag() { const d = this.state.dragging; if (!d) return; const el = d.el; this.state.dragging = null; const days = Math.round((Number(el.getAttribute("width")) - d.origWidth) / 26); if (!days) return; const end = new Date(el.dataset.end); end.setDate(end.getDate() + days); const endDate = end.toISOString().slice(0,10); await frappe.db.set_value("PMO Task", el.dataset.ganttTask, "end_date", endDate); await this.loadProject(this.state.project); this.render(); }

  async openRequirementDrawer(name) { const doc = await frappe.db.get_doc("PMO Requirement", name); this.drawer("PMO Requirement", doc.requirement, this.requirementForm(doc), [{ label: "Save", className: "primary", fn: () => this.saveRequirement(name) }, { label: "Open in Desk", action: "open-desk", doctype: "PMO Requirement", name }]); }
  requirementForm(doc) { return `<div class="pmo-form-grid"><label>Status<select data-field="status"><option>${["Not Started","In Progress","In Review","Blocked","Done"].join("</option><option>")}</option></select></label><label>UAT<select data-field="uat_result"><option>${["Not Tested","Pass","Fail"].join("</option><option>")}</option></select></label><label class="span2">Notes<textarea data-field="note">${this.esc(doc.note || "")}</textarea></label></div>`.replace(`>${doc.status}</option>`, ` selected>${doc.status}</option>`).replace(`>${doc.uat_result}</option>`, ` selected>${doc.uat_result}</option>`); }
  async saveRequirement(name) { const fields = {}; this.$overlay.find("[data-field]").each((_, el) => fields[el.dataset.field] = $(el).val()); await frappe.db.set_value("PMO Requirement", name, fields); this.closeOverlay(); await this.refresh(); }
  async openRecordDrawer(dt, name) { const doc = await frappe.db.get_doc(dt, name); this.drawer(dt, doc.title || doc.milestone_name || doc.raid_id || doc.task_id || name, `<pre class="pmo-code">${this.esc(JSON.stringify(doc, null, 2))}</pre>`, [{ label: "Open in Desk", action: "open-desk", doctype: dt, name }]); }

  drawer(kind, title, body, actions = []) { this.closeOverlay(); this.$overlay = $(`<div><div class="pmo-drawer-backdrop" data-action="close-overlay"></div><aside class="pmo-drawer"><header><h3>${this.esc(title)}</h3><p>${this.esc(kind)}</p></header><div class="pmo-drawer-body">${body}<div class="pmo-actions">${actions.map((a, i) => `<button class="pmo-btn ${a.className || ""}" data-ov-action="${i}" ${a.action ? `data-action="${a.action}" data-doctype="${a.doctype}" data-name="${a.name}"` : ""}>${this.esc(a.label)}</button>`).join("")}<button class="pmo-btn" data-action="close-overlay">Close</button></div></div></aside></div>`).appendTo(document.body); this.$overlay.on("click", "[data-action]", (event) => this.action(event.currentTarget.dataset.action, event.currentTarget)); actions.forEach((a, i) => { if (a.fn) this.$overlay.find(`[data-ov-action="${i}"]`).on("click", a.fn); }); }
  modal(title, body, saveFn) { this.closeOverlay(); this.$overlay = $(`<div><div class="pmo-modal-backdrop" data-action="close-overlay"></div><section class="pmo-modal"><header><h3>${this.esc(title)}</h3></header><div class="pmo-modal-body">${body}<div class="pmo-actions"><button class="pmo-btn primary" data-save>Save</button><button class="pmo-btn" data-action="close-overlay">Cancel</button></div></div></section></div>`).appendTo(document.body); this.$overlay.on("click", "[data-action]", (event) => this.action(event.currentTarget.dataset.action, event.currentTarget)); this.$overlay.find("[data-save]").on("click", saveFn); }
  closeOverlay() { if (this.$overlay) this.$overlay.remove(); this.$overlay = null; }

  modalRequirement() { this.modal("New Requirement", `<div class="pmo-form-grid"><label>ID<input data-field="requirement_id"></label><label>Project<select data-field="project">${this.state.projects.map(p => `<option value="${p.name}">${this.esc(p.project_name || p.name)}</option>`).join("")}</select></label><label>Area<input data-field="area"></label><label>Priority<select data-field="priority"><option>Must Have</option><option>Should</option><option>Nice</option></select></label><label class="span2">Requirement<textarea data-field="requirement"></textarea></label></div>`, async () => { const doc = this.formDoc("PMO Requirement"); doc.status = "Not Started"; await frappe.db.insert(doc); this.closeOverlay(); await this.refresh(); }); }
  modalRun(kind, caseName) { this.modal(`New ${kind.toUpperCase()} Run`, `<div class="pmo-form-grid"><label>Result<select data-field="result"><option>Pass</option><option>Fail</option><option>Blocked</option><option>Not Run</option></select></label><label>Environment<input data-field="environment" value="Frappe Cloud production"></label><label class="span2">Evidence<textarea data-field="evidence"></textarea></label><label class="span2">Notes<textarea data-field="notes"></textarea></label></div>`, async () => { const values = this.formValues(); await this.call("vcl_pmo_doctypes.api.new_run", { case_id: caseName, kind, result: values.result, evidence: values.evidence, notes: values.notes, environment: values.environment }); this.closeOverlay(); await this.loadProject(this.state.project); await this.openCase(kind, caseName); }); }
  modalRAID(type) { this.modal(`New ${type}`, `<div class="pmo-form-grid"><label>ID<input data-field="raid_id"></label><label>Type<input data-field="type" value="${type}"></label><label class="span2">Title<input data-field="title"></label><label>Severity<select data-field="severity"><option>High</option><option>Critical</option><option>Medium</option><option>Low</option></select></label><label>Status<select data-field="status"><option>Open</option><option>Mitigating</option><option>Accepted</option><option>Closed</option></select></label><label class="span2">Mitigation<textarea data-field="mitigation"></textarea></label></div>`, async () => { const doc = this.formDoc("PMO RAID Item"); doc.project = this.state.project; await frappe.db.insert(doc); this.closeOverlay(); await this.loadProject(this.state.project); this.render(); }); }
  modalDocument() { this.modal("New Document", `<div class="pmo-form-grid"><label>ID<input data-field="document_id"></label><label>Type<select data-field="doc_type"><option>How-to</option><option>Workflow</option><option>SOP</option><option>Spec</option><option>Brief</option><option>Decision Log</option></select></label><label class="span2">Title<input data-field="title"></label><label class="span2">Markdown<textarea data-field="content_md"></textarea></label></div>`, async () => { const doc = this.formDoc("PMO Document"); doc.project = this.state.project || null; doc.status = "Draft"; await frappe.db.insert(doc); this.closeOverlay(); await this.refresh(); }); }
  formValues() { const values = {}; this.$overlay.find("[data-field]").each((_, el) => values[el.dataset.field] = $(el).val()); return values; }
  formDoc(doctype) { return Object.assign({ doctype }, this.formValues()); }

  chip(value) { const v = value || ""; const tone = ["Done","Pass","Achieved","Closed"].includes(v) ? "green" : ["In Review","In Progress","Mitigating","At Risk"].includes(v) ? "amber" : ["Blocked","Fail","Missed","Critical"].includes(v) ? "red" : "blue"; return `<span class="pmo-chip ${tone}">${this.esc(v)}</span>`; }
  renderMD(md) { return this.esc(md || "").replace(/^### (.*)$/gm, "<h3>$1</h3>").replace(/^## (.*)$/gm, "<h2>$1</h2>").replace(/^# (.*)$/gm, "<h1>$1</h1>").replace(/\*\*(.*?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>"); }
  date(value) { return value ? String(value).slice(0, 16) : ""; }
  esc(value) { return frappe.utils.escape_html(String(value ?? "")); }
}
