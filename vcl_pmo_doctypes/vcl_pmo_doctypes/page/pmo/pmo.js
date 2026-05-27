frappe.pages["pmo"].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "VCL PMO",
    single_column: true
  });

  page.main.addClass("vcl-pmo-page");
  page.set_primary_action("New Requirement", () => frappe.new_doc("PMO Requirement"));
  page.add_action_item("Projects", () => frappe.set_route("List", "PMO Project"));
  page.add_action_item("UAT", () => frappe.set_route("List", "PMO UAT Case"));
  page.add_action_item("OAT", () => frappe.set_route("List", "PMO OAT Check"));
  page.add_action_item("Sync Log", () => frappe.set_route("List", "PMO Sync Log"));

  const app = new VCLPMOPage(page);
  app.refresh();
};

class VCLPMOPage {
  constructor(page) {
    this.page = page;
    this.state = {
      summary: {},
      projects: [],
      requirements: [],
      oat: null
    };
    this.$root = $(`
      <div class="pmo-shell">
        <div class="pmo-ticker">
          <span class="live">LIVE</span>
          <span>UTC <b data-clock>--:--:--</b></span>
          <span>PROJECTS <b data-kpi="projects">0</b></span>
          <span>REQS <b data-kpi="requirements">0</b></span>
          <span>DONE <b data-kpi="done">0</b></span>
          <span>REVIEW <b data-kpi="in_review">0</b></span>
          <span>BLOCKED <b data-kpi="blocked">0</b></span>
        </div>
        <div class="pmo-tabs">
          <button data-view="inbox" class="active">Inbox</button>
          <button data-view="requirements">Requirements</button>
          <button data-view="projects">Projects</button>
          <button data-view="uat">UAT</button>
          <button data-view="oat">OAT</button>
          <button data-view="briefing">Briefing</button>
        </div>
        <div class="pmo-body" data-body></div>
      </div>
    `).appendTo(this.page.main);
    this.$body = this.$root.find("[data-body]");
    this.view = "inbox";
    this.bind();
    setInterval(() => this.tick(), 1000);
    this.tick();
  }

  bind() {
    this.$root.on("click", "[data-view]", (event) => {
      this.view = event.currentTarget.dataset.view;
      this.$root.find("[data-view]").removeClass("active");
      $(event.currentTarget).addClass("active");
      this.render();
    });
    this.$root.on("click", "[data-open-req]", (event) => {
      frappe.set_route("Form", "PMO Requirement", event.currentTarget.dataset.openReq);
    });
    this.$root.on("click", "[data-open-project]", (event) => {
      frappe.set_route("Form", "PMO Project", event.currentTarget.dataset.openProject);
    });
    this.$root.on("click", "[data-new-uat]", (event) => {
      frappe.new_doc("PMO UAT Case", { requirement: event.currentTarget.dataset.newUat });
    });
  }

  tick() {
    this.$root.find("[data-clock]").text(new Date().toISOString().slice(11, 19));
  }

  async refresh() {
    await Promise.all([this.loadSummary(), this.loadProjects(), this.loadRequirements(), this.loadOAT()]);
    this.render();
  }

  async call(method, args = {}) {
    const response = await frappe.call({ method, args });
    return response.message;
  }

  async loadSummary() {
    this.state.summary = await this.call("vcl_pmo_doctypes.api.summary");
    Object.entries(this.state.summary || {}).forEach(([key, value]) => {
      this.$root.find(`[data-kpi="${key}"]`).text(value || 0);
    });
  }

  async loadProjects() {
    this.state.projects = await frappe.db.get_list("PMO Project", {
      fields: ["name", "project_id", "project_name", "system", "status", "priority", "progress"],
      limit: 100,
      order_by: "project_id asc"
    });
  }

  async loadRequirements() {
    this.state.requirements = await frappe.db.get_list("PMO Requirement", {
      fields: ["name", "requirement_id", "project", "area", "requirement", "priority", "status", "owner", "uat_result", "needs_action"],
      limit: 500,
      order_by: "requirement_id asc"
    });
  }

  async loadOAT() {
    this.state.oat = await this.call("vcl_pmo_doctypes.api.oat_run");
  }

  chip(value) {
    const tone = value === "Done" || value === "Pass" ? "green" : value === "Blocked" || value === "Fail" ? "red" : value === "In Review" || value === "In Progress" ? "amber" : "blue";
    return `<span class="pmo-chip ${tone}">${frappe.utils.escape_html(value || "")}</span>`;
  }

  render() {
    if (this.view === "inbox") return this.renderInbox();
    if (this.view === "requirements") return this.renderRequirements();
    if (this.view === "projects") return this.renderProjects();
    if (this.view === "uat") return this.renderUAT();
    if (this.view === "oat") return this.renderOAT();
    return this.renderBriefing();
  }

  renderInbox() {
    const rows = this.state.requirements.filter((row) => row.needs_action || ["Blocked", "In Review"].includes(row.status));
    this.$body.html(`
      <div class="pmo-head"><h2>Inbox</h2><p>${rows.length} items need attention.</p></div>
      <div class="pmo-list">
        ${rows.map((row) => `
          <div class="pmo-row" data-open-req="${row.name}">
            <div class="pmo-dot">${frappe.utils.escape_html((row.requirement_id || "?").split("-").pop())}</div>
            <div>
              <b>${frappe.utils.escape_html(row.requirement)}</b>
              <small>${frappe.utils.escape_html(row.requirement_id)} · ${frappe.utils.escape_html(row.project)} · ${frappe.utils.escape_html(row.area || "")}</small>
            </div>
            ${this.chip(row.status)}
          </div>
        `).join("") || `<div class="pmo-card">Inbox clear.</div>`}
      </div>
    `);
  }

  renderRequirements() {
    this.$body.html(`
      <div class="pmo-head"><h2>Requirements</h2><p>Click a row to open the requirement form. Use the UAT button to add a test case.</p></div>
      <table class="pmo-table">
        <thead><tr><th>ID</th><th>Project</th><th>Area</th><th>Requirement</th><th>Owner</th><th>UAT</th><th>Status</th><th></th></tr></thead>
        <tbody>
          ${this.state.requirements.map((row) => `
            <tr>
              <td data-open-req="${row.name}" class="mono">${frappe.utils.escape_html(row.requirement_id)}</td>
              <td>${frappe.utils.escape_html(row.project)}</td>
              <td>${frappe.utils.escape_html(row.area || "")}</td>
              <td data-open-req="${row.name}">${frappe.utils.escape_html(row.requirement)}</td>
              <td>${frappe.utils.escape_html(row.owner || "")}</td>
              <td>${this.chip(row.uat_result)}</td>
              <td>${this.chip(row.status)}</td>
              <td><button class="pmo-small" data-new-uat="${row.name}">UAT</button></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `);
  }

  renderProjects() {
    this.$body.html(`
      <div class="pmo-head"><h2>Projects</h2><p>Portfolio view from PMO Project.</p></div>
      <div class="pmo-grid">
        ${this.state.projects.map((row) => `
          <div class="pmo-card" data-open-project="${row.name}">
            <div class="pmo-card-title">${frappe.utils.escape_html(row.project_name || row.name)}</div>
            <div class="pmo-muted mono">${frappe.utils.escape_html(row.project_id || row.name)}</div>
            <p>${frappe.utils.escape_html(row.system || "")}</p>
            <div class="pmo-progress"><i style="width:${Number(row.progress || 0)}%"></i></div>
            <div>${this.chip(row.status)} ${this.chip(row.priority)}</div>
          </div>
        `).join("")}
      </div>
    `);
  }

  renderUAT() {
    this.$body.html(`
      <div class="pmo-head"><h2>UAT</h2><p>User acceptance testing is recorded in PMO UAT Case.</p></div>
      <div class="pmo-actions">
        <button class="btn btn-primary" onclick="frappe.new_doc('PMO UAT Case')">New UAT Case</button>
        <button class="btn btn-default" onclick="frappe.set_route('List', 'PMO UAT Case')">Open UAT List</button>
      </div>
      <div class="pmo-card">
        <b>UAT rule</b>
        <p>Create one UAT case per user-visible behaviour. Mark Pass/Fail with evidence before cutover.</p>
      </div>
    `);
  }

  renderOAT() {
    const oat = this.state.oat || { total: 0, passed: 0, failed: 0, checks: [] };
    this.$body.html(`
      <div class="pmo-head"><h2>OAT</h2><p>Operational acceptance: permissions, n8n, Excel mirror, agent webhook, sync logs.</p></div>
      <div class="pmo-grid">
        <div class="pmo-card"><span>Total</span><b>${oat.total}</b></div>
        <div class="pmo-card"><span>Passed</span><b>${oat.passed}</b></div>
        <div class="pmo-card"><span>Failed</span><b>${oat.failed}</b></div>
      </div>
      <div class="pmo-actions">
        <button class="btn btn-primary" onclick="frappe.new_doc('PMO OAT Check')">New OAT Check</button>
        <button class="btn btn-default" onclick="frappe.set_route('List', 'PMO OAT Check')">Open OAT List</button>
      </div>
      <table class="pmo-table">
        <thead><tr><th>ID</th><th>Area</th><th>Check</th><th>Status</th></tr></thead>
        <tbody>${(oat.checks || []).map((row) => `<tr><td>${frappe.utils.escape_html(row.check_id)}</td><td>${frappe.utils.escape_html(row.area)}</td><td>${frappe.utils.escape_html(row.check)}</td><td>${this.chip(row.status)}</td></tr>`).join("")}</tbody>
      </table>
    `);
  }

  renderBriefing() {
    this.$body.html(`
      <div class="pmo-head"><h2>Briefing</h2><p>Frappe-native PMO migration state.</p></div>
      <div class="pmo-card pmo-brief">
        <h3>VCL PMO</h3>
        <p>PMO data and workflow live in Frappe Cloud. Excel is mirrored through n8n. The local FastAPI build remains reference/fallback until UAT and OAT pass.</p>
        <button class="btn btn-primary" onclick="window.print()">Print / PDF</button>
        <button class="btn btn-default" onclick="frappe.set_route('List', 'PMO Sync Log')">Sync Log</button>
      </div>
    `);
  }
}
