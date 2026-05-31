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
      planId: null,
      shiftId: null,
      summary: {},
      projects: [],
      requirements: [],
      uatCases: [],
      oatChecks: [],
      raid: [],
      docs: {},
      notes: [],
      packet: null,
      overview: null,
      gantt: null,
      plans: [],
      shifts: [],
      planDetail: null,
      dragging: null,
    };
    this.$root = $(this.shell()).appendTo(this.page.main);
    this.$body = this.$root.find("[data-body]");
    this.bind();
    setInterval(() => this.tick(), 1000);
    window.addEventListener("popstate", (event) => {
      if (event.state && event.state.view) {
        Object.assign(this.state, event.state);
        this.hydrateForState().then(() => this.render());
        return;
      }
      this.applyRouteFromLocation();
      this.hydrateForState().then(() => this.render());
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
          <button class="pmo-btn primary" data-action="new-note">New Note</button>
          <button class="pmo-btn" data-action="new-requirement">New Requirement</button>
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
    this.$root.on("click", "[data-plan]", (event) => this.openPlan(event.currentTarget.dataset.plan));
    this.$root.on("click", "[data-shift]", (event) => this.openShift(event.currentTarget.dataset.shift));
    this.$root.on("mousedown", "[data-gantt-task]", (event) => this.startDrag(event));
    $(document).on("mousemove.pmo", (event) => this.dragGantt(event));
    $(document).on("mouseup.pmo", () => this.endDrag());
  }

  async boot() {
    this.tick();
    this.applyRouteFromLocation();
    await this.refresh();
  }

  async refresh() {
    await Promise.all([this.loadSummary(), this.loadPortfolio()]);
    await this.hydrateForState();
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
    const [projects, requirements, uatCases, oatChecks, raid, docs, notes] = await Promise.all([
      frappe.db.get_list("PMO Project", { fields: ["name", "project_id", "project_name", "project_short", "system", "status", "priority", "progress", "current_phase", "target_completion"], limit: 200, order_by: "project_id asc" }),
      frappe.db.get_list("PMO Requirement", { fields: ["name", "requirement_id", "project", "area", "requirement", "priority", "status", "requirement_owner", "uat_result", "needs_action"], limit: 800, order_by: "requirement_id asc" }),
      frappe.db.get_list("PMO UAT Case", { fields: ["name", "uat_case_id", "project", "requirement", "description", "latest_result", "latest_run_date", "run_count", "bucket", "linked_shift", "linked_task", "linked_plan"], limit: 800, order_by: "uat_case_id asc" }),
      frappe.db.get_list("PMO OAT Check", { fields: ["name", "check_id", "project", "area", "check", "latest_result", "latest_run_date", "run_count", "bucket", "linked_shift", "linked_task", "linked_plan"], limit: 800, order_by: "check_id asc" }),
      frappe.db.get_list("PMO RAID Item", { fields: ["name", "raid_id", "project", "type", "title", "severity", "probability", "status", "due_date"], limit: 800, order_by: "due_date asc" }),
      this.call("vcl_pmo_doctypes.api.documents_for"),
      this.call("vcl_pmo_doctypes.api.notes_for"),
    ]);
    Object.assign(this.state, { projects, requirements, uatCases, oatChecks, raid, docs, notes });
  }

  async loadProject(projectId) {
    const [packet, overview, gantt, docs, plans, shifts, notes] = await Promise.all([
      this.call("vcl_pmo_doctypes.api.project_packet", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.project_overview", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.project_gantt", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.documents_for", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.project_plans", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.project_shifts", { project_id: projectId }),
      this.call("vcl_pmo_doctypes.api.notes_for", { project_id: projectId }),
    ]);
    Object.assign(this.state, { packet, overview, gantt, docs, plans, shifts, notes });
  }

  async hydrateForState() {
    await this.inferProjectForState();
    if (this.state.project) await this.loadProject(this.state.project);
    if (this.state.view === "plan" && this.state.planId) {
      this.state.planDetail = await this.call("vcl_pmo_doctypes.api.plan_detail", { plan_id: this.state.planId });
    }
    if (["project", "case", "run", "plan", "shift"].includes(this.state.view) && !this.state.project) {
      this.state.view = "portfolio:projects";
      this.state.subtab = "overview";
      this.clearDrilldownState();
    }
  }

  async inferProjectForState() {
    if (this.state.project) return;
    if (this.state.view === "plan" && this.state.planId) {
      const planName = await frappe.db.get_value("PMO Plan", { plan_id: this.state.planId }, "name");
      const name = planName?.message?.name || this.state.planId;
      if (name) {
        const plan = await frappe.db.get_doc("PMO Plan", name);
        this.state.project = plan.project;
      }
    }
    if (this.state.view === "shift" && this.state.shiftId) {
      const shiftName = await frappe.db.get_value("PMO Shift", { shift_id: this.state.shiftId }, "name");
      const name = shiftName?.message?.name || this.state.shiftId;
      if (name) {
        const shift = await frappe.db.get_doc("PMO Shift", name);
        this.state.project = shift.project;
      }
    }
    if (this.state.view === "case" && this.state.caseKind && this.state.caseId) {
      const doctype = this.state.caseKind === "oat" ? "PMO OAT Check" : "PMO UAT Case";
      const idField = this.state.caseKind === "oat" ? "check_id" : "uat_case_id";
      const caseName = await frappe.db.get_value(doctype, { [idField]: this.state.caseId }, "name");
      const name = caseName?.message?.name || this.state.caseId;
      if (name) {
        const row = await frappe.db.get_doc(doctype, name);
        this.state.project = row.project;
      }
    }
    if (this.state.view === "run" && this.state.caseKind && this.state.runName) {
      const doctype = this.state.caseKind === "oat" ? "PMO OAT Run" : "PMO UAT Run";
      const caseField = this.state.caseKind === "oat" ? "oat_check" : "uat_case";
      const caseDoctype = this.state.caseKind === "oat" ? "PMO OAT Check" : "PMO UAT Case";
      const run = await frappe.db.get_doc(doctype, this.state.runName);
      if (run && run[caseField]) {
        const row = await frappe.db.get_doc(caseDoctype, run[caseField]);
        this.state.project = row.project;
      }
    }
  }

  clearDrilldownState() {
    Object.assign(this.state, { caseKind: null, caseId: null, runName: null, planId: null, shiftId: null, planDetail: null });
  }

  routeState() {
    const params = new URLSearchParams();
    ["view", "project", "subtab", "caseKind", "caseId", "runName", "planId", "shiftId"].forEach((key) => {
      if (this.state[key]) params.set(key, this.state[key]);
    });
    return params.toString();
  }

  applyRouteFromLocation() {
    const raw = decodeURIComponent((window.location.hash || "").replace(/^#/, ""));
    Object.assign(this.state, { view: "portfolio:inbox", project: null, subtab: "overview", caseKind: null, caseId: null, runName: null, planId: null, shiftId: null, planDetail: null });
    if (!raw) return;
    if (!raw.includes("=")) {
      this.state.view = raw;
      return;
    }
    const params = new URLSearchParams(raw);
    ["view", "project", "subtab", "caseKind", "caseId", "runName", "planId", "shiftId"].forEach((key) => {
      const value = params.get(key);
      if (value) this.state[key] = value;
    });
  }

  pushState() {
    const state = { view: this.state.view, project: this.state.project, subtab: this.state.subtab, caseKind: this.state.caseKind, caseId: this.state.caseId, runName: this.state.runName, planId: this.state.planId, shiftId: this.state.shiftId };
    history.pushState(state, "", `/app/pmo#${this.routeState()}`);
  }

  setPortfolioView(view) {
    Object.assign(this.state, { view: "portfolio:" + view, project: null, subtab: "overview" });
    this.clearDrilldownState();
    this.pushState();
    this.render();
  }

  async openProject(projectId, subtab = "overview") {
    Object.assign(this.state, { view: "project", project: projectId, subtab });
    this.clearDrilldownState();
    await this.loadProject(projectId);
    this.pushState();
    this.render();
  }

  async openCase(kind, caseName) {
    Object.assign(this.state, { view: "case", caseKind: kind, caseId: caseName, runName: null, planId: null, shiftId: null });
    this.pushState();
    this.render();
  }

  async openRun(kind, runName) {
    Object.assign(this.state, { view: "run", caseKind: kind, runName, planId: null, shiftId: null });
    this.pushState();
    this.render();
  }

  action(name, el) {
    if (name === "refresh") return this.refresh();
    if (name === "new-note") return this.modalNote();
    if (name === "assign-note") return this.assignNote(el.dataset.note);
    if (name === "archive-note") return this.archiveNote(el.dataset.note);
    if (name === "notes-to-codex-plan") return this.modalNotesToCodexPlan();
    if (name === "new-requirement") return this.modalRequirement();
    if (name === "back-portfolio") return this.setPortfolioView("projects");
    if (name === "back-project") return this.openProject(this.state.project, this.state.subtab || "plans");
    if (name === "new-uat-run") return this.modalRun("uat", el.dataset.case);
    if (name === "new-oat-run") return this.modalRun("oat", el.dataset.case);
    if (name === "new-raid") return this.modalRAID(el.dataset.type || "Risk");
    if (name === "new-doc") return this.modalDocument();
    if (name === "new-plan") return this.modalPlan();
    if (name === "add-plan-item") return this.modalAddPlanItem(el.dataset.plan);
    if (name === "new-shift") return this.modalNewShift();
    if (name === "allocate-claude") return this.bulkAllocate(el.dataset.plan, "claude");
    if (name === "allocate-codex") return this.bulkAllocate(el.dataset.plan, "codex");
    if (name === "allocate-human") return this.bulkAllocate(el.dataset.plan, "human");
    if (name === "start-shift") return this.shiftAction(el.dataset.shift, "start");
    if (name === "complete-shift") return this.modalCompleteShift(el.dataset.shift);
    if (name === "block-shift") return this.modalBlockShift(el.dataset.shift);
    if (name === "dispatch-shift") return this.dispatchShift(el.dataset.shift);
    if (name === "send-plan-slack") return this.sendPlanToSlack(el.dataset.plan);
    if (name === "approve-plan") return this.approvePlan(el.dataset.plan);
    if (name === "open-desk") return window.open(`/app/${encodeURIComponent(el.dataset.doctype.toLowerCase().replaceAll(" ", "-"))}/${encodeURIComponent(el.dataset.name)}`, "_blank");
    if (name === "close-overlay") return this.closeOverlay();
  }

  render() {
    if (this.state.view.startsWith("portfolio:")) return this.renderPortfolio();
    if (this.state.view === "project") return this.renderProject();
    if (this.state.view === "case") return this.renderCase();
    if (this.state.view === "run") return this.renderRun();
    if (this.state.view === "plan") return this.renderPlan();
    if (this.state.view === "shift") return this.renderShift();
  }

  renderTabs(items, active, attr = "data-view") {
    return `<div class="pmo-tabs">${items.map(item => `<button ${attr}="${item[0]}" class="${item[0] === active ? "active" : ""}">${item[1]}</button>`).join("")}</div>`;
  }

  renderPortfolio() {
    const active = this.state.view.split(":")[1];
    this.$root.find("[data-tabs]").html(this.renderTabs([
      ["inbox", "Inbox"], ["notes", "Notes"], ["projects", "Projects"], ["roadmap", "Roadmap"], ["raid", "RAID"], ["documentation", "Documentation"], ["test-status", "Test Status"]
    ], active));
    if (active === "inbox") return this.renderPortfolioInbox();
    if (active === "notes") return this.renderNotes(null);
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
    this.$root.find("[data-tabs]").html(`<div class="pmo-subtabs"><button data-action="back-portfolio">Portfolio</button>${[["overview","Overview"],["timeline","Timeline"],["open","Open Items"],["notes","Notes"],["plans","Plans"],["shifts","Shifts"],["milestones","Milestones"],["raid","RAID"],["uat","UAT"],["oat","OAT"],["history","Test History"],["documentation","Documentation"],["activity","Activity"]].map(i => `<button data-subtab="${i[0]}" class="${this.state.subtab === i[0] ? "active" : ""}">${i[1]}</button>`).join("")}</div>`);
    if (this.state.subtab === "overview") return this.renderProjectOverview(p);
    if (this.state.subtab === "timeline") return this.renderTimeline();
    if (this.state.subtab === "open") return this.renderOpenItems();
    if (this.state.subtab === "notes") return this.renderNotes(this.state.project);
    if (this.state.subtab === "plans") return this.renderPlans();
    if (this.state.subtab === "shifts") return this.renderShifts();
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

  renderNotes(projectId) {
    const rows = this.state.notes || [];
    const inbox = rows.filter(n => !n.project || n.status === "Inbox");
    const sorted = projectId ? rows.filter(n => n.project === projectId && n.status !== "Inbox") : rows.filter(n => n.project && n.status !== "Inbox");
    const title = projectId ? "Project Notes" : "Notes Inbox";
    const sub = projectId ? "Notes assigned to this project plus unsorted inbox notes" : "Capture loose notes, then assign them to a PMO project";
    this.$body.html(`${this.head(title, sub)}<div class="pmo-actions"><button class="pmo-btn primary" data-action="new-note">New Note</button><button class="pmo-btn sage" data-action="notes-to-codex-plan">Send selected to Codex plan</button></div><div class="pmo-card pmo-muted">Select one or more notes, create one grouped project plan, approve the plan, then schedule Codex shifts.</div><h3>Inbox</h3>${this.noteList(inbox, true)}<h3>Sorted</h3>${this.noteList(sorted, false)}`);
  }

  noteList(rows, sortable) {
    if (!rows.length) return "<div class='pmo-card pmo-muted'>No notes here.</div>";
    return `<div class="pmo-list">${rows.map(n => `<div class="pmo-card"><div class="pmo-card-title"><label><input type="checkbox" class="pmo-note-check" data-note="${this.esc(n.name)}"> ${this.esc(n.title)}</label></div><div class="pmo-muted pmo-mono">${this.esc(n.name)} · ${this.esc(n.note_type || "General")} · ${this.esc(n.status || "Inbox")}</div><div class="pmo-markdown">${this.renderMD((n.content_md || "").slice(0, 700))}</div><div class="pmo-actions"><select data-note-project="${n.name}"><option value="">Unassigned</option>${this.state.projects.map(p => `<option value="${p.name}" ${p.name === n.project ? "selected" : ""}>${this.esc(p.project_id || p.name)} · ${this.esc(p.project_name || p.name)}</option>`).join("")}</select><button class="pmo-btn primary" data-action="assign-note" data-note="${n.name}">${sortable ? "Sort" : "Move"}</button><button class="pmo-btn" data-action="archive-note" data-note="${n.name}">Archive</button><button class="pmo-btn" data-action="open-desk" data-doctype="PMO Note" data-name="${n.name}">Open in Desk</button></div></div>`).join("")}</div>`;
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
  caseTable(kind, rows) {
    const id = kind === "uat" ? "uat_case_id" : "check_id";
    const text = kind === "uat" ? "description" : "check";
    const groups = new Map();
    (rows || []).forEach(r => {
      const key = r.bucket || r.linked_shift || r.linked_task || r.linked_plan || "Ungrouped";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(r);
    });
    const sortedKeys = Array.from(groups.keys()).sort((a, b) => {
      if (a === "Ungrouped") return 1;
      if (b === "Ungrouped") return -1;
      return String(a).localeCompare(String(b));
    });
    const bucketBlock = (key) => {
      const items = groups.get(key);
      const passed = items.filter(r => r.latest_result === "Pass").length;
      const failed = items.filter(r => r.latest_result === "Fail").length;
      const blocked = items.filter(r => r.latest_result === "Blocked").length;
      const notRun = items.filter(r => !r.latest_result || r.latest_result === "Not Yet Run").length;
      const meta = `<span class="pmo-bucket-meta">${items.length} item${items.length === 1 ? "" : "s"} · ${passed} pass · ${failed} fail · ${blocked} blocked · ${notRun} not run</span>`;
      const rowsHtml = items.map(r => `<tr data-case="${r.name}" data-kind="${kind}"><td class="pmo-mono pmo-indent">${this.esc(r[id])}</td><td>${this.esc(r[text])}</td><td>${this.chip(r.latest_result || "Not Yet Run")}</td><td>${this.date(r.latest_run_date)}</td><td>${Number(r.run_count || 0)}</td></tr>`).join("");
      return `<tr class="pmo-bucket-row" data-bucket="${this.esc(key)}"><td colspan="5"><b>${this.esc(key)}</b> ${meta}</td></tr>${rowsHtml}`;
    };
    return `<table class="pmo-table pmo-case-table"><thead><tr><th>ID</th><th>Definition</th><th>Latest</th><th>Last Run</th><th>Runs</th></tr></thead><tbody>${sortedKeys.map(bucketBlock).join("") || "<tr><td colspan='5' class='pmo-muted'>No cases yet.</td></tr>"}</tbody></table>`;
  }

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

  modalRequirement() { this.modal("New Requirement", `<div class="pmo-form-grid"><label>Project<select data-field="project">${this.state.projects.map(p => `<option value="${p.name}" ${p.name === this.state.project ? "selected" : ""}>${this.esc(p.project_name || p.name)}</option>`).join("")}</select></label><label>Area<input data-field="area"></label><label>Priority<select data-field="priority"><option>Must Have</option><option>Should</option><option>Nice</option></select></label><label class="span2">Requirement<textarea data-field="requirement"></textarea></label></div>`, async () => { const doc = this.formDoc("PMO Requirement"); doc.status = "Not Started"; await frappe.db.insert(doc); this.closeOverlay(); await this.refresh(); }); }
  modalRun(kind, caseName) { this.modal(`New ${kind.toUpperCase()} Run`, `<div class="pmo-form-grid"><label>Result<select data-field="result"><option>Pass</option><option>Fail</option><option>Blocked</option><option>Not Run</option></select></label><label>Environment<input data-field="environment" value="Frappe Cloud production"></label><label class="span2">Evidence<textarea data-field="evidence"></textarea></label><label class="span2">Notes<textarea data-field="notes"></textarea></label></div>`, async () => { const values = this.formValues(); await this.call("vcl_pmo_doctypes.api.new_run", { case_id: caseName, kind, result: values.result, evidence: values.evidence, notes: values.notes, environment: values.environment }); this.closeOverlay(); await this.loadProject(this.state.project); await this.openCase(kind, caseName); }); }
  modalRAID(type) { this.modal(`New ${type}`, `<div class="pmo-form-grid"><label>ID<input data-field="raid_id"></label><label>Type<input data-field="type" value="${type}"></label><label class="span2">Title<input data-field="title"></label><label>Severity<select data-field="severity"><option>High</option><option>Critical</option><option>Medium</option><option>Low</option></select></label><label>Status<select data-field="status"><option>Open</option><option>Mitigating</option><option>Accepted</option><option>Closed</option></select></label><label class="span2">Mitigation<textarea data-field="mitigation"></textarea></label></div>`, async () => { const doc = this.formDoc("PMO RAID Item"); doc.project = this.state.project; await frappe.db.insert(doc); this.closeOverlay(); await this.loadProject(this.state.project); this.render(); }); }
  modalNote() { this.modal("New Note", `<div class="pmo-form-grid"><label class="span2">Title<input data-field="title"></label><label>Project<select data-field="project"><option value="">Inbox / unsorted</option>${this.state.projects.map(p => `<option value="${p.name}" ${p.name === this.state.project ? "selected" : ""}>${this.esc(p.project_id || p.name)} · ${this.esc(p.project_name || p.name)}</option>`).join("")}</select></label><label>Type<select data-field="note_type"><option>General</option><option>Idea</option><option>Issue</option><option>Decision</option><option>Meeting</option><option>Follow-up</option></select></label><label class="span2">Note<textarea data-field="content_md" rows="7"></textarea></label></div>`, async () => { const v = this.formValues(); await this.call("vcl_pmo_doctypes.api.create_note", { title: v.title, content_md: v.content_md, project_id: v.project || null, note_type: v.note_type }); this.closeOverlay(); await this.refresh(); }); }
  async assignNote(name) { const project = this.$body.find(`[data-note-project="${name}"]`).val() || null; await this.call("vcl_pmo_doctypes.api.assign_note", { note_id: name, project_id: project }); await this.refresh(); }
  async archiveNote(name) { await this.call("vcl_pmo_doctypes.api.assign_note", { note_id: name, status: "Archived" }); await this.refresh(); }
  modalNotesToCodexPlan() {
    const noteIds = [];
    this.$body.find(".pmo-note-check:checked").each((_, el) => noteIds.push(el.dataset.note));
    if (!noteIds.length) { frappe.show_alert({ message: "Select at least one note", indicator: "amber" }); return; }
    this.modal("Create grouped Codex plan", `<div class="pmo-form-grid"><label>Project<select data-field="project"><option value="">Select project</option>${this.state.projects.map(p => `<option value="${p.name}" ${p.name === this.state.project ? "selected" : ""}>${this.esc(p.project_id || p.name)} · ${this.esc(p.project_name || p.name)}</option>`).join("")}</select></label><label>Selected notes<input value="${noteIds.length}" disabled></label><label class="span2">Plan title<input data-field="title" placeholder="Optional grouped-plan title"></label><label class="span2">Planning instructions<textarea data-field="description" rows="4" placeholder="Optional scope or acceptance guidance for Codex"></textarea></label></div>`, async () => {
      const v = this.formValues();
      if (!v.project) { frappe.show_alert({ message: "Choose a project", indicator: "amber" }); return; }
      const result = await this.call("vcl_pmo_doctypes.api.create_plan_from_notes", { note_ids: JSON.stringify(noteIds), project_id: v.project, title: v.title || null, description: v.description || "", post_to_slack: 0 });
      this.closeOverlay();
      await this.openProject(v.project, "plans");
      await this.openPlan(result.plan_id);
      frappe.show_alert({ message: `Created ${result.plan_id}. Review and approve before allocating shifts.`, indicator: "green" }, 10);
    });
  }
  modalDocument() { this.modal("New Document", `<div class="pmo-form-grid"><label>ID<input data-field="document_id"></label><label>Type<select data-field="doc_type"><option>How-to</option><option>Workflow</option><option>SOP</option><option>Spec</option><option>Brief</option><option>Decision Log</option></select></label><label class="span2">Title<input data-field="title"></label><label class="span2">Markdown<textarea data-field="content_md"></textarea></label></div>`, async () => { const doc = this.formDoc("PMO Document"); doc.project = this.state.project || null; doc.status = "Draft"; await frappe.db.insert(doc); this.closeOverlay(); await this.refresh(); }); }
  formValues() { const values = {}; this.$overlay.find("[data-field]").each((_, el) => values[el.dataset.field] = $(el).val()); return values; }
  formDoc(doctype) { return Object.assign({ doctype }, this.formValues()); }

  chip(value) { const v = value || ""; const tone = ["Done","Pass","Achieved","Closed"].includes(v) ? "green" : ["In Review","In Progress","Mitigating","At Risk","Allocated","Proposed"].includes(v) ? "amber" : ["Blocked","Fail","Missed","Critical","Cancelled"].includes(v) ? "red" : "blue"; return `<span class="pmo-chip ${tone}">${this.esc(v)}</span>`; }
  renderMD(md) { return this.esc(md || "").replace(/^### (.*)$/gm, "<h3>$1</h3>").replace(/^## (.*)$/gm, "<h2>$1</h2>").replace(/^# (.*)$/gm, "<h1>$1</h1>").replace(/\*\*(.*?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>"); }
  date(value) { return value ? String(value).slice(0, 16) : ""; }
  esc(value) { return frappe.utils.escape_html(String(value ?? "")); }

  // ==========================================================================
  // Plans & Shifts
  // ==========================================================================

  async openPlan(planName) {
    const plan = this.state.plans.find(p => p.name === planName || p.plan_id === planName);
    const planId = plan ? plan.plan_id : planName;
    const detail = await this.call("vcl_pmo_doctypes.api.plan_detail", { plan_id: planId });
    Object.assign(this.state, { view: "plan", project: detail.plan.project || this.state.project, subtab: "plans", planId, planDetail: detail, shiftId: null, caseKind: null, caseId: null, runName: null });
    this.pushState();
    this.render();
  }

  async openShift(shiftName) {
    const shift = this.state.shifts.find(s => s.name === shiftName || s.shift_id === shiftName);
    const shiftId = shift ? shift.shift_id : shiftName;
    Object.assign(this.state, { view: "shift", subtab: "shifts", shiftId, planId: null, caseKind: null, caseId: null, runName: null });
    this.pushState();
    this.render();
  }

  renderPlans() {
    const plans = this.state.plans || [];
    this.$body.html(`${this.head("Plans", "Planning proposals for this project. Each plan generates Milestones, Tasks, RAID, Shifts — with UAT/OAT auto-created where ticked.")}<div class="pmo-actions"><button class="pmo-btn primary" data-action="new-plan">New Plan</button></div><table class="pmo-table"><thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Planner</th><th>Created</th></tr></thead><tbody>${plans.map(p => `<tr data-plan="${p.name}"><td class="pmo-mono">${this.esc(p.plan_id)}</td><td>${this.esc(p.title)}</td><td>${this.chip(p.status)}</td><td>${this.esc(p.planner || "")}</td><td>${this.date(p.created_at)}</td></tr>`).join("") || "<tr><td colspan='5' class='pmo-muted'>No plans yet. Click New Plan to create one.</td></tr>"}</tbody></table>`);
  }

  renderShifts() {
    const shifts = this.state.shifts || [];
    const groups = { claude: [], codex: [], human: [] };
    shifts.forEach(s => { (groups[s.assigned_to] || (groups[s.assigned_to] = [])).push(s); });
    this.$body.html(`${this.head("Shifts", "Work allocated to claude, codex, or human — with status and UAT/OAT links")}<div class="pmo-actions"><button class="pmo-btn primary" data-action="new-shift">New Shift</button></div>${["claude","codex","human"].map(a => `<h3>${a[0].toUpperCase() + a.slice(1)}</h3>${this.shiftTable(groups[a] || [])}`).join("")}`);
  }

  shiftTable(rows) {
    if (!rows.length) return "<div class='pmo-card pmo-muted'>No shifts in this queue.</div>";
    return `<table class="pmo-table"><thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Status</th><th>Planned</th><th>UAT</th><th>OAT</th><th>Actions</th></tr></thead><tbody>${rows.map(s => `<tr data-shift="${s.name}"><td class="pmo-mono">${this.esc(s.shift_id)}</td><td>${this.esc(s.title)}</td><td>${this.esc(s.shift_type)}</td><td>${this.chip(s.status)}</td><td>${this.date(s.planned_start)} → ${this.date(s.planned_end)}</td><td>${s.requires_uat ? "✓" : ""}</td><td>${s.requires_oat ? "✓" : ""}</td><td>${this.shiftActionBtns(s)}</td></tr>`).join("")}</tbody></table>`;
  }

  shiftActionBtns(s) {
    const isAgent = s.assigned_to === "claude" || s.assigned_to === "codex";
    if (s.status === "Allocated" || s.status === "Proposed") {
      const dispatch = isAgent ? `<button class="pmo-btn pmo-small primary" data-action="dispatch-shift" data-shift="${s.shift_id}" title="Send to n8n → ${s.assigned_to}">Execute via n8n</button> ` : "";
      return `${dispatch}<button class="pmo-btn pmo-small" data-action="start-shift" data-shift="${s.shift_id}">Start</button>`;
    }
    if (s.status === "In Progress") return `<button class="pmo-btn pmo-small" data-action="complete-shift" data-shift="${s.shift_id}">Complete</button> <button class="pmo-btn pmo-small" data-action="block-shift" data-shift="${s.shift_id}">Block</button>`;
    return "";
  }

  async renderPlan() {
    const detail = this.state.planDetail || { plan: {}, items: [] };
    const plan = detail.plan;
    const items = detail.items;
    this.$root.find("[data-tabs]").html("");
    const checkboxes = items.map((it, i) => `<tr><td><input type="checkbox" class="pmo-plan-check" data-idx="${i}" ${it.promoted_to_doctype ? "disabled" : ""}></td><td class="pmo-mono">${this.esc(it.item_type)}</td><td>${this.esc(it.title)}</td><td>${this.esc((it.description || "").slice(0, 80))}</td><td>${it.needs_uat ? "✓" : ""}</td><td>${it.needs_oat ? "✓" : ""}</td><td>${this.esc(it.assignee_hint || "")}</td><td>${it.promoted_to_doctype ? `${this.esc(it.promoted_to_doctype)}<br><span class="pmo-mono">${this.esc(it.promoted_to_name)}</span>` : "<span class='pmo-muted'>not allocated</span>"}</td></tr>`).join("");
    const approved = Boolean(plan.approved_at);
    const gated = approved ? "" : " disabled title=\"Approve the plan before scheduling shifts\"";
    this.$body.html(`${this.breadcrumb(["Portfolio", this.state.project, "Plans", plan.plan_id])}${this.head(plan.title || plan.plan_id, `${plan.status} · ${items.length} proposed item${items.length === 1 ? "" : "s"}`)}<div class="pmo-card pmo-markdown">${this.renderMD(plan.description || "No description.")}</div><div class="pmo-card ${approved ? "" : "pmo-muted"}"><b>Approval gate:</b> ${approved ? `Approved by ${this.esc(plan.approved_by || "PMO user")} at ${this.date(plan.approved_at)}. Shift planning is unlocked.` : "Review this plan and approve it before sending the PDF to Slack or scheduling shifts."}</div><div class="pmo-actions"><button class="pmo-btn primary" data-action="add-plan-item" data-plan="${plan.plan_id}">Add Item</button>${approved ? "" : `<button class="pmo-btn sage" data-action="approve-plan" data-plan="${plan.plan_id}">Approve Plan</button>`}<button class="pmo-btn" data-action="send-plan-slack" data-plan="${plan.plan_id}"${gated}>Send approved PDF to Slack</button><button class="pmo-btn" data-action="allocate-claude" data-plan="${plan.plan_id}"${gated}>Allocate selected to Claude</button><button class="pmo-btn" data-action="allocate-codex" data-plan="${plan.plan_id}"${gated}>Allocate selected to Codex</button><button class="pmo-btn" data-action="allocate-human" data-plan="${plan.plan_id}"${gated}>Allocate selected to Human</button></div><table class="pmo-table"><thead><tr><th><input type="checkbox" id="pmo-plan-check-all"></th><th>Type</th><th>Title</th><th>Description</th><th>UAT</th><th>OAT</th><th>Hint</th><th>Promoted</th></tr></thead><tbody>${checkboxes || "<tr><td colspan='8' class='pmo-muted'>No items. Click Add Item to start.</td></tr>"}</tbody></table>`);
    this.$body.find("#pmo-plan-check-all").on("change", (e) => {
      const checked = e.currentTarget.checked;
      this.$body.find(".pmo-plan-check:not(:disabled)").prop("checked", checked);
    });
  }

  async renderShift() {
    const shiftName = (this.state.shifts.find(s => s.shift_id === this.state.shiftId) || {}).name || this.state.shiftId;
    const shift = await frappe.db.get_doc("PMO Shift", shiftName);
    this.$root.find("[data-tabs]").html("");
    const actions = [];
    if (shift.status === "Allocated" || shift.status === "Proposed") actions.push(`<button class="pmo-btn primary" data-action="start-shift" data-shift="${shift.shift_id}">Start</button>`);
    const isAgent = shift.assigned_to === "claude" || shift.assigned_to === "codex";
    if ((shift.status === "Allocated" || shift.status === "Proposed") && isAgent) actions.push(`<button class="pmo-btn primary" data-action="dispatch-shift" data-shift="${shift.shift_id}">Execute via n8n → ${shift.assigned_to}</button>`);
    if (shift.status === "In Progress") { actions.push(`<button class="pmo-btn primary" data-action="complete-shift" data-shift="${shift.shift_id}">Complete</button>`); actions.push(`<button class="pmo-btn" data-action="block-shift" data-shift="${shift.shift_id}">Block</button>`); }
    actions.push(`<button class="pmo-btn" data-action="open-desk" data-doctype="PMO Shift" data-name="${shift.name}">Open in Desk</button>`);
    this.$body.html(`${this.breadcrumb(["Portfolio", this.state.project, "Shifts", shift.shift_id])}${this.head(shift.title || shift.shift_id, `${shift.shift_type} · ${shift.assigned_to} · ${shift.status}`)}<div class="pmo-two-col"><div class="pmo-card pmo-markdown">${this.renderMD(shift.description || "No description.")}</div><div class="pmo-card"><p><b>Status</b><br>${this.chip(shift.status)}</p><p><b>Assigned to</b><br>${this.esc(shift.assigned_to)}</p><p><b>Planned</b><br>${this.date(shift.planned_start)} → ${this.date(shift.planned_end)}</p><p><b>Actual</b><br>${this.date(shift.actual_start)} → ${this.date(shift.actual_end)}</p><p><b>UAT Case</b><br>${shift.uat_case ? `<span class="pmo-mono">${this.esc(shift.uat_case)}</span>` : "–"}</p><p><b>OAT Check</b><br>${shift.oat_check ? `<span class="pmo-mono">${this.esc(shift.oat_check)}</span>` : "–"}</p></div></div><div class="pmo-card"><h3>Output Notes</h3><div class="pmo-markdown">${this.renderMD(shift.output_notes || "No output captured yet.")}</div></div><div class="pmo-actions">${actions.join("")}</div>`);
  }

  modalPlan() {
    this.modal("New Plan", `<div class="pmo-form-grid"><label>Plan ID<input data-field="plan_id" placeholder="leave blank to auto-generate"></label><label>Title<input data-field="title"></label><label class="span2">Description (markdown)<textarea data-field="description" rows="4"></textarea></label></div>`, async () => {
      const values = this.formValues();
      await this.call("vcl_pmo_doctypes.api.create_plan", { project_id: this.state.project, title: values.title, description: values.description, items: JSON.stringify([]) });
      this.closeOverlay();
      await this.loadProject(this.state.project);
      this.render();
    });
  }

  modalAddPlanItem(planId) {
    this.modal("Add Plan Item", `<div class="pmo-form-grid"><label>Type<select data-field="item_type"><option>Shift</option><option>Milestone</option><option>Requirement</option><option>Task</option><option>RAID</option></select></label><label>Assignee Hint<select data-field="assignee_hint"><option>unassigned</option><option>claude</option><option>codex</option><option>human</option></select></label><label class="span2">Title<input data-field="title"></label><label class="span2">Description<textarea data-field="description" rows="3"></textarea></label><label><input type="checkbox" data-field="needs_uat"> Needs UAT</label><label><input type="checkbox" data-field="needs_oat"> Needs OAT</label><label class="span2">Metadata (JSON, optional)<textarea data-field="metadata" rows="2" placeholder='e.g. {"target_date":"2026-06-15","severity":"High"}'></textarea></label></div>`, async () => {
      const v = this.formValues();
      const item = { item_type: v.item_type, title: v.title, description: v.description, assignee_hint: v.assignee_hint, needs_uat: this.$overlay.find('[data-field="needs_uat"]').prop("checked") ? 1 : 0, needs_oat: this.$overlay.find('[data-field="needs_oat"]').prop("checked") ? 1 : 0 };
      if (v.metadata) { try { item.metadata = JSON.parse(v.metadata); } catch (e) { frappe.show_alert({ message: "Invalid JSON in metadata", indicator: "red" }); return; } }
      await this.call("vcl_pmo_doctypes.api.add_plan_items", { plan_id: planId, items: JSON.stringify([item]) });
      this.closeOverlay();
      await this.openPlan(planId);
    });
  }

  modalNewShift() {
    this.modal("New Shift", `<div class="pmo-form-grid"><label>Shift ID<input data-field="shift_id" placeholder="e.g. SHIFT-MANUAL-01"></label><label>Assigned to<select data-field="assigned_to"><option>claude</option><option>codex</option><option>human</option></select></label><label class="span2">Title<input data-field="title"></label><label class="span2">Description<textarea data-field="description" rows="3"></textarea></label><label>Type<select data-field="shift_type"><option>Execution</option><option>Planning</option><option>Review</option><option>Test</option></select></label><label>Status<select data-field="status"><option>Allocated</option><option>Proposed</option></select></label><label><input type="checkbox" data-field="requires_uat"> Requires UAT</label><label><input type="checkbox" data-field="requires_oat"> Requires OAT</label></div>`, async () => {
      const v = this.formValues();
      const doc = { doctype: "PMO Shift", shift_id: v.shift_id, project: this.state.project, title: v.title, description: v.description, shift_type: v.shift_type, assigned_to: v.assigned_to, status: v.status, requires_uat: this.$overlay.find('[data-field="requires_uat"]').prop("checked") ? 1 : 0, requires_oat: this.$overlay.find('[data-field="requires_oat"]').prop("checked") ? 1 : 0 };
      await frappe.db.insert(doc);
      this.closeOverlay();
      await this.loadProject(this.state.project);
      this.render();
    });
  }

  modalCompleteShift(shiftId) {
    this.modal("Complete Shift", `<div class="pmo-form-grid"><label class="span2">Output Notes (markdown)<textarea data-field="output_notes" rows="4"></textarea></label><label>UAT Result (if shift has UAT)<select data-field="uat_result"><option value="">–</option><option>Pass</option><option>Fail</option><option>Blocked</option></select></label><label>OAT Result (if shift has OAT)<select data-field="oat_result"><option value="">–</option><option>Pass</option><option>Fail</option><option>Blocked</option></select></label></div>`, async () => {
      const v = this.formValues();
      await this.call("vcl_pmo_doctypes.api.complete_shift", { shift_id: shiftId, output_notes: v.output_notes, uat_result: v.uat_result || null, oat_result: v.oat_result || null });
      this.closeOverlay();
      await this.loadProject(this.state.project);
      this.render();
    });
  }

  modalBlockShift(shiftId) {
    this.modal("Block Shift", `<div class="pmo-form-grid"><label class="span2">Reason<textarea data-field="reason" rows="3"></textarea></label></div>`, async () => {
      const v = this.formValues();
      await this.call("vcl_pmo_doctypes.api.block_shift", { shift_id: shiftId, reason: v.reason });
      this.closeOverlay();
      await this.loadProject(this.state.project);
      this.render();
    });
  }

  async bulkAllocate(planId, assignee) {
    const indices = [];
    this.$body.find(".pmo-plan-check:checked").each((_, el) => indices.push(Number(el.dataset.idx)));
    if (!indices.length) { frappe.show_alert({ message: "Select at least one item to allocate", indicator: "amber" }); return; }
    const result = await this.call("vcl_pmo_doctypes.api.allocate_plan_items", { plan_id: planId, item_indices: JSON.stringify(indices), assignee });
    frappe.show_alert({ message: `Allocated ${(result.created || []).length} item${result.created && result.created.length === 1 ? "" : "s"} to ${assignee}`, indicator: "green" });
    await this.loadProject(this.state.project);
    await this.openPlan(planId);
  }

  async shiftAction(shiftId, action) {
    if (action === "start") await this.call("vcl_pmo_doctypes.api.start_shift", { shift_id: shiftId });
    await this.loadProject(this.state.project);
    this.render();
  }

  async dispatchShift(shiftId) {
    const result = await this.call("vcl_pmo_doctypes.api.dispatch_shift", { shift_id: shiftId });
    if (result && result.ok) frappe.show_alert({ message: `Dispatched ${shiftId} to n8n (HTTP ${result.n8n_status}). Shift now In Progress.`, indicator: "green" });
    else frappe.show_alert({ message: `Dispatch failed: ${(result && result.error) || "unknown"}`, indicator: "red" });
    await this.loadProject(this.state.project);
    this.render();
  }

  async approvePlan(planId) {
    const result = await this.call("vcl_pmo_doctypes.api.approve_plan", { plan_id: planId });
    frappe.show_alert({ message: `${result.plan_id || planId} approved. Shift planning is unlocked.`, indicator: "green" }, 10);
    await this.loadProject(this.state.project);
    await this.openPlan(planId);
  }

  async sendPlanToSlack(planId) {
    frappe.show_alert({ message: `Rendering ${planId} as PDF and uploading to Slack…`, indicator: "blue" });
    const result = await this.call("vcl_pmo_doctypes.api.send_plan_to_slack", { plan_id: planId });
    if (result && result.ok) {
      const link = result.permalink ? ` <a href="${result.permalink}" target="_blank">Open in Slack</a>` : "";
      frappe.show_alert({ message: `Posted ${planId} to Slack ✓${link}`, indicator: "green" }, 12);
    } else {
      const err = (result && (result.error || result.step)) || "unknown error";
      frappe.show_alert({ message: `Slack post failed: ${err}. Check pmo_slack_bot_token in site_config.json.`, indicator: "red" }, 12);
    }
  }
}
