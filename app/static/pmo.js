const API = "/pmo/api";
const state = {projects: [], requirements: [], summary: {}, feed: [], active: "inbox", drawer: null};
const statuses = ["Not Started", "In Progress", "In Review", "Blocked", "Done"];
const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

async function get(path){ const r = await fetch(API + path); if(!r.ok) throw new Error(await r.text()); return r.json(); }
async function send(path, method, body){ const r = await fetch(API + path,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); if(!r.ok) throw new Error(await r.text()); return r.json(); }

function chip(status){
  const c = status === "Done" ? "green" : status === "Blocked" ? "red" : status === "In Review" || status === "In Progress" ? "amber" : "blue";
  return `<span class="chip ${c}" data-status="${esc(status)}">${esc(status)}</span>`;
}

function clock(){
  $("#clock").textContent = new Date().toISOString().slice(11,19);
}

async function load(){
  const [health, projects, reqs, summary, feed] = await Promise.all([get("/health"), get("/projects"), get("/requirements"), get("/summary"), get("/feed")]);
  state.projects = projects; state.requirements = reqs; state.summary = summary; state.feed = feed;
  $("#t-erp").textContent = String(health.frappe || "").startsWith("ok") ? "OK" : "CACHE";
  $("#t-excel").textContent = (health.excel || "").toUpperCase();
  $("#stale").classList.toggle("show", !String(health.frappe || "").startsWith("ok"));
  render();
}

function render(){
  $("#cnt-proj").textContent = state.projects.length;
  $("#cnt-req").textContent = state.requirements.length;
  $("#cnt-inbox").textContent = state.summary.inbox || 0;
  $("#t-projects").textContent = state.summary.projects || 0;
  $("#t-reqs").textContent = state.summary.requirements || 0;
  $("#t-done").textContent = state.summary.done || 0;
  $("#t-review").textContent = state.summary.in_review || 0;
  $("#t-blocked").textContent = state.summary.blocked || 0;
  renderInbox(); renderReqs(); renderProjects(); renderMission(); renderTimeline(); renderPalette("");
}

function projectName(id){ return (state.projects.find(p => p.id === id) || {}).name || id; }

function renderInbox(){
  const rows = state.requirements.filter(r => r.needs_action || ["Blocked","In Review"].includes(r.status));
  $("#inbox-sub").textContent = `${rows.length} items need Tanuj`;
  $("#inbox-list").innerHTML = rows.map(r => `<div class="queue-row" data-open="${esc(r.id)}"><div class="dot ${r.status === "Blocked" ? "blk" : "warn"}">${esc(r.id.split("-").pop())}</div><div><div class="ttl">${esc(r.requirement)}</div><div class="meta">${esc(r.id)} · ${esc(projectName(r.project_id))} · ${esc(r.area)}</div></div>${chip(r.status)}<button class="btn primary" data-open="${esc(r.id)}">Open</button></div>`).join("") || `<div class="card">Inbox clear.</div>`;
}

function renderReqs(){
  $("#req-tbody").innerHTML = state.requirements.map(r => `<tr data-open="${esc(r.id)}"><td class="id-cell">${esc(r.id)}</td><td>${esc(r.project_id)}</td><td>${esc(r.area)}</td><td>${esc(r.requirement)}</td><td>${esc(r.owner)}</td><td>${esc(r.uat_result)}</td><td data-req="${esc(r.id)}">${chip(r.status)}</td></tr>`).join("");
}

function renderProjects(){
  $("#proj-grid").innerHTML = state.projects.map(p => `<div class="card" data-project="${esc(p.id)}"><div style="display:flex;justify-content:space-between;gap:12px"><div><div class="ttl">${esc(p.name)}</div><div class="meta">${esc(p.id)} · ${esc(p.system)}</div></div>${chip(p.status)}</div><div class="progress"><i style="width:${Number(p.progress||0)}%"></i></div><div class="meta" style="margin-top:8px">${p.done_count || 0}/${p.req_count || 0} requirements done · ${esc(p.priority)}</div></div>`).join("");
}

function spark(color="var(--sage)"){ return `<div class="spark"><svg viewBox="0 0 100 30" preserveAspectRatio="none"><polyline points="0,26 14,23 28,20 42,19 56,14 70,12 84,8 100,5" fill="none" stroke="${color}" stroke-width="1.6"/></svg></div>`; }
function renderMission(){
  $("#kpis").innerHTML = [
    ["Active projects", state.summary.projects || 0, "Portfolio register", ""],
    ["Requirements done", state.summary.done || 0, "Completed across all projects", "green"],
    ["Blocked", state.summary.blocked || 0, "Needs intervention", "red"],
    ["Inbox", state.summary.inbox || 0, "Action queue", "amber"],
  ].map(([l,v,d,c]) => `<div class="card kpi ${c}"><h3>${l}</h3><div class="v">${v}</div><div class="meta">${d}</div>${spark()}</div>`).join("");
  $("#feed").innerHTML = state.feed.slice(0,12).map(f => `<div class="field"><div class="k">${esc((f.ts||"").slice(11,19) || f.kind)}</div><div>${esc(f.verb || f.status || f.kind)} <code>${esc(f.target || f.req_id || "")}</code></div></div>`).join("") || "No activity yet.";
}

function renderTimeline(){
  $("#timeline").innerHTML = state.projects.map(p => `<div class="field"><div class="k">${esc(p.id)}</div><div>${esc(p.name)}<div class="progress"><i style="width:${Number(p.progress||0)}%"></i></div></div></div>`).join("");
}

async function setStatus(reqId, current){
  const next = prompt(`Status for ${reqId}`, current);
  if(!next || !statuses.includes(next)) return;
  const req = state.requirements.find(r => r.id === reqId);
  const old = req.status; req.status = next; render();
  try { Object.assign(req, await send(`/requirements/${encodeURIComponent(reqId)}`, "PATCH", {status: next})); await load(); }
  catch(e){ req.status = old; render(); alert(e.message); }
}

async function openDrawer(id){
  const req = await get(`/requirements/${encodeURIComponent(id)}`);
  state.drawer = req;
  $("#drawer-id").textContent = req.id;
  $("#drawer-title").textContent = req.requirement;
  $("#drawer-sub").textContent = `${req.project_id} · ${req.area} · ${req.priority}`;
  $("#drawer-bg").classList.add("show"); $("#drawer").classList.add("show");
  renderDrawer("detail");
}

async function renderDrawer(tab){
  $$(".drawer .tabs button").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
  const r = state.drawer;
  if(tab === "detail") $("#drawer-body").innerHTML = ["project_id","area","priority","status","owner","uat_result","note","md_path"].map(k => `<div class="field"><div class="k">${k}</div><div>${esc(r[k])}</div></div>`).join("");
  if(tab === "links") {
    $("#drawer-body").innerHTML = `<button class="btn primary" id="add-link">+ Add link</button><div id="links">${(r.erpnext_links||[]).map(l => `<div class="link-card"><div class="ttl">${esc(l.doctype)}</div><div class="meta">${esc(l.name)}</div><div id="preview-${l.id}">Loading preview...</div></div>`).join("") || "<p>No ERPNext links yet.</p>"}</div>`;
    $("#add-link").onclick = addLink;
    (r.erpnext_links||[]).forEach(async l => { const p = await get(`/erpnext/preview?doctype=${encodeURIComponent(l.doctype)}&name=${encodeURIComponent(l.name)}`); $(`#preview-${l.id}`).textContent = Object.entries(p).filter(([k,v]) => v && !["doctype","name"].includes(k)).map(([k,v]) => `${k}: ${v}`).join(" · "); });
  }
  if(tab === "activity") $("#drawer-body").innerHTML = state.feed.filter(f => JSON.stringify(f).includes(r.id)).map(f => `<div class="field"><div class="k">${esc(f.kind)}</div><div>${esc(f.verb || f.status)} ${esc(f.notes || f.diff || "")}</div></div>`).join("") || "No activity.";
  if(tab === "agent") $("#drawer-body").innerHTML = `<button class="btn primary" id="agent-done">Mark Done via webhook</button><pre class="card mono">${esc(JSON.stringify({req_id:r.id,status:"Done",agent:"codex-cli",notes:"Completed from PMO drawer",files_changed:[]},null,2))}</pre>`;
  const done = $("#agent-done"); if(done) done.onclick = async () => { await send("/agent/complete","POST",{req_id:r.id,status:"Done",agent:"codex-cli",notes:"Completed from PMO drawer",files_changed:[]}); await load(); openDrawer(r.id); };
}

async function addLink(){
  const doctype = prompt("ERPNext doctype", "Project"); if(!doctype) return;
  const name = prompt("ERPNext document name"); if(!name) return;
  await send("/erpnext/link", "POST", {req_id: state.drawer.id, doctype, name, label: name});
  state.drawer = await get(`/requirements/${encodeURIComponent(state.drawer.id)}`);
  renderDrawer("links");
}

function showView(view){
  state.active = view; $$(".view").forEach(v => v.classList.toggle("show", v.dataset.view === view));
  $$(".primary a").forEach(a => a.classList.toggle("active", a.dataset.view === view));
  $("#crumb").textContent = view[0].toUpperCase() + view.slice(1); $("#crumb-detail").textContent = view === "inbox" ? "Needs action" : "Live";
  history.pushState({}, "", "/pmo/");
}

function renderPalette(q){
  const s = q.toLowerCase();
  const items = [
    ...state.requirements.map(r => ({kind:"REQ", id:r.id, label:r.requirement, sub:r.project_id, open:() => openDrawer(r.id)})),
    ...state.projects.map(p => ({kind:"PRJ", id:p.id, label:p.name, sub:p.status, open:() => showView("projects")})),
  ].filter(i => !s || `${i.id} ${i.label} ${i.sub}`.toLowerCase().includes(s)).slice(0,30);
  $("#pal-list").innerHTML = items.map(i => `<div class="pal-item" data-pal="${esc(i.id)}"><span class="id-cell">${esc(i.kind)}</span><div><div>${esc(i.label)}</div><div class="meta">${esc(i.id)} · ${esc(i.sub)}</div></div><span>↵</span></div>`).join("");
}

document.addEventListener("click", e => {
  const nav = e.target.closest(".primary a"); if(nav) showView(nav.dataset.view);
  const open = e.target.closest("[data-open]"); if(open) openDrawer(open.dataset.open);
  const status = e.target.closest("[data-status]"); if(status){ const cell = status.closest("[data-req]"); if(cell) setStatus(cell.dataset.req, status.dataset.status); e.stopPropagation(); }
  const tab = e.target.closest(".drawer .tabs button"); if(tab) renderDrawer(tab.dataset.tab);
});
$("#drawer-bg").onclick = () => { $("#drawer-bg").classList.remove("show"); $("#drawer").classList.remove("show"); };
$("#open-pal").onclick = () => { $("#pal").classList.add("show"); $("#pal-input").focus(); };
$("#pal").onclick = e => { if(e.target.id === "pal") $("#pal").classList.remove("show"); const item = e.target.closest("[data-pal]"); if(item){ const found = state.requirements.find(r => r.id === item.dataset.pal); if(found) openDrawer(found.id); $("#pal").classList.remove("show"); } };
$("#pal-input").oninput = e => renderPalette(e.target.value);
document.addEventListener("keydown", e => { if((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k"){ e.preventDefault(); $("#open-pal").click(); } if(e.key === "Escape") $("#pal").classList.remove("show"); if(e.key === "g") window._g = true; else if(window._g){ const map={i:"inbox",r:"requirements",p:"projects",m:"mission",t:"timeline",b:"briefing"}; if(map[e.key]) showView(map[e.key]); window._g=false; } });
$("#pdf").onclick = () => window.print();
$("#telegram").onclick = async () => { await send("/agent/complete","POST",{req_id:"PMO-002-10",status:"In Progress",agent:"codex-cli",notes:"Briefing sent to Telegram from PMO UI.",files_changed:[]}); await load(); };
setInterval(clock, 1000); clock(); load().catch(e => alert(e.message));
