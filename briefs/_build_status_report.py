#!/usr/bin/env python3
"""
Build the VCL-DEV-PMO-002 status report HTML using the verified VCL Brand v1.1
palette and screenshots from the actually deployed /app/pmo.

Palette source: VCL Brand & Visual Identity Standards v1.1 (May 2026), confirmed
against the deployed pmo.css `--vcl-*` tokens.

  VCL Blue    #2B3990   primary, table headers, links, buttons
  VCL Navy    #1D2766   H1, document titles
  VCL Blue Mid #5C6DBE  dividers
  VCL Blue Light #D6DBF5
  VCL Blue Pale #EEF0FB
  VCL Sage    #5A9367   brand accent (logo, user pill, active nav)
  VCL Green   #1B7A45   Complete, positive KPIs
  VCL Green Light #D4EDE0
  VCL Amber   #B86B00   In Progress, warnings (replaces red)
  VCL Amber Light #FFF0CC
  VCL Red     #C0392B   restricted — errors only
  VCL Red Light #FADBD8
  Ink #1C1C1E, Mid Grey #4A4F5C, Muted #8A909E, Rule #CBD2E0
  Surface #F4F5F8, White #FFFFFF

Typography:
  Manrope (400/600/700/800) + JetBrains Mono (400/700), base64-embedded.
"""
from pathlib import Path
import base64

REPO = Path('/home/tanujharia/projects/vcl-pmo')
B64 = Path('/tmp/b64')

def load_b64(name):
    return B64.joinpath(name).read_text()

def img_b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()

STAMP = load_b64('stamp.b64')
MR_400 = load_b64('manrope-400.b64')
MR_600 = load_b64('manrope-600.b64')
MR_700 = load_b64('manrope-700.b64')
MR_800 = load_b64('manrope-800.b64')
JB_400 = load_b64('jbmono-400.b64')
JB_700 = load_b64('jbmono-700.b64')

SHOT_DIR = REPO / 'briefs/screenshots'
def shot(name):
    p = SHOT_DIR / f'{name}.png'
    return img_b64(p) if p.exists() else ''

SHOT_INBOX    = shot('pmo-deployed-inbox')
SHOT_PROJECTS = shot('pmo-deployed-projects')
SHOT_OVERVIEW = shot('pmo-deployed-project-overview')
SHOT_PLANS    = shot('pmo-deployed-plans-tab')
SHOT_PLAN     = shot('pmo-deployed-plan-detail')

CSS = r"""
@font-face { font-family: 'Manrope'; font-weight: 400; src: url(data:font/ttf;base64,__MR_400__) format('truetype'); }
@font-face { font-family: 'Manrope'; font-weight: 600; src: url(data:font/ttf;base64,__MR_600__) format('truetype'); }
@font-face { font-family: 'Manrope'; font-weight: 700; src: url(data:font/ttf;base64,__MR_700__) format('truetype'); }
@font-face { font-family: 'Manrope'; font-weight: 800; src: url(data:font/ttf;base64,__MR_800__) format('truetype'); }
@font-face { font-family: 'JetBrains Mono'; font-weight: 400; src: url(data:font/ttf;base64,__JB_400__) format('truetype'); }
@font-face { font-family: 'JetBrains Mono'; font-weight: 700; src: url(data:font/ttf;base64,__JB_700__) format('truetype'); }

:root {
  /* VCL Brand v1.1 — verified against deployed pmo.css */
  --vcl-blue: #2B3990;
  --vcl-navy: #1D2766;
  --vcl-blue-mid: #5C6DBE;
  --vcl-blue-light: #D6DBF5;
  --vcl-blue-pale: #EEF0FB;
  --vcl-sage: #5A9367;
  --vcl-sage-soft: rgba(90,147,103,0.22);
  --vcl-green: #1B7A45;
  --vcl-green-light: #D4EDE0;
  --vcl-amber: #B86B00;
  --vcl-amber-light: #FFF0CC;
  --vcl-red: #C0392B;
  --vcl-red-light: #FADBD8;
  --vcl-ink: #1C1C1E;
  --vcl-mid: #4A4F5C;
  --vcl-muted: #8A909E;
  --vcl-rule: #CBD2E0;
  --vcl-surface: #F4F5F8;
  --vcl-white: #FFFFFF;
}

* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  font-family: 'Manrope', -apple-system, system-ui, sans-serif;
  color: var(--vcl-ink); background: var(--vcl-white);
  font-size: 11pt; line-height: 1.5;
  letter-spacing: -0.005em;
}
.mono, code, kbd { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 10pt; }

@page { size: A4 portrait; margin: 15mm 15mm 18mm 15mm; }
.page { page-break-after: always; padding: 0; }
.page:last-of-type { page-break-after: auto; }

/* HEADER BAR */
.bar {
  background: var(--vcl-navy); color: white;
  padding: 12px 18px; display: flex; align-items: center; justify-content: space-between;
  border-bottom: 3px solid var(--vcl-sage);
  font-size: 10pt; font-weight: 600; letter-spacing: 0.08em;
}
.bar .left { text-transform: uppercase; color: var(--vcl-sage); }
.bar .right { color: var(--vcl-blue-light); font-family: 'JetBrains Mono', monospace; font-size: 9pt; font-weight: 400; letter-spacing: 0.04em; }

/* FOOTER */
.foot {
  background: var(--vcl-navy); color: var(--vcl-blue-light);
  padding: 8px 18px; display: flex; align-items: center; justify-content: space-between;
  border-top: 3px solid var(--vcl-sage);
  font-size: 8.5pt; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.04em;
  margin-top: 18px;
}
.foot .stamp-mini { width: 32px; height: 32px; opacity: 0.95; }

/* COVER — VCL Navy bleed */
.cover {
  background: var(--vcl-navy); color: white;
  min-height: 268mm;
  padding: 24mm 18mm 18mm 18mm;
  display: flex; flex-direction: column; justify-content: space-between;
  margin: -15mm;
  position: relative;
}
.cover-stripe-top { height: 6px; background: var(--vcl-sage); margin: -24mm -18mm 24mm -18mm; }
.cover .org-line {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 16mm;
}
.cover .org-line .caps {
  color: var(--vcl-sage);
  font-family: 'Manrope', sans-serif;
  font-weight: 700;
  font-size: 10.5pt;
  letter-spacing: 0.32em;
  text-transform: uppercase;
}
.cover .org-line .stamp img { width: 120px; height: 120px; }
.cover .title { font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 56pt; line-height: 1.0; letter-spacing: -0.02em; color: white; }
.cover .lede { font-size: 16pt; color: rgba(255,255,255,0.82); line-height: 1.45; max-width: 520px; margin-top: 14px; font-weight: 400; }
.cover .accent-rule { height: 4px; background: var(--vcl-sage); width: 80px; margin: 28px 0; }
.cover .meta-grid {
  display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 22px 32px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(90,147,103,0.4);
  border-radius: 8px;
  padding: 22px 24px;
  margin-top: 24px;
}
.cover .meta-grid .k {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9pt;
  color: var(--vcl-sage);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 600;
  margin-bottom: 4px;
}
.cover .meta-grid .v {
  font-family: 'Manrope', sans-serif;
  font-size: 13pt; color: white; font-weight: 600;
}
.cover .cover-foot {
  margin-top: auto;
  border-top: 1px solid rgba(90,147,103,0.4);
  padding-top: 14px;
  display: flex; justify-content: space-between; align-items: center;
  color: rgba(255,255,255,0.75);
  font-family: 'JetBrains Mono', monospace;
  font-size: 9pt; letter-spacing: 0.06em;
}
.cover .cover-foot .confidential { color: var(--vcl-amber-light); font-weight: 700; }

/* BODY */
h1 { font-family: 'Manrope', sans-serif; font-weight: 800; font-size: 24pt; color: var(--vcl-navy); letter-spacing: -0.015em; margin: 18px 0 6px 0; line-height: 1.1; }
h2 { font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 14pt; color: var(--vcl-blue); margin: 22px 0 8px 0; padding-bottom: 6px; border-bottom: 2px solid var(--vcl-blue); letter-spacing: -0.01em; }
h3 { font-family: 'Manrope', sans-serif; font-weight: 700; font-size: 11.5pt; color: var(--vcl-ink); margin: 14px 0 6px 0; }
.sub { color: var(--vcl-muted); font-size: 11pt; margin-top: -2px; }
p { margin: 8px 0; }
ul, ol { margin: 8px 0 12px 22px; padding: 0; }
li { margin: 4px 0; }

/* KPI / STATUS CARDS (mix-a pattern, VCL palette) */
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 14px 0 22px 0; }
.kpi {
  background: var(--vcl-white);
  border: 1px solid var(--vcl-rule);
  border-top: 3px solid var(--vcl-blue);
  border-radius: 8px;
  padding: 16px 18px;
  page-break-inside: avoid;
}
.kpi .l { font-size: 9pt; text-transform: uppercase; letter-spacing: 0.1em; color: var(--vcl-muted); font-weight: 700; }
.kpi .v { font-family: 'JetBrains Mono', monospace; font-size: 30pt; font-weight: 500; color: var(--vcl-navy); letter-spacing: -0.02em; margin-top: 6px; line-height: 1; }
.kpi .d { font-size: 10pt; color: var(--vcl-mid); margin-top: 6px; }
.kpi.green { border-top-color: var(--vcl-green); }
.kpi.green .v { color: var(--vcl-green); }
.kpi.amber { border-top-color: var(--vcl-amber); }
.kpi.amber .v { color: var(--vcl-amber); }
.kpi.sage  { border-top-color: var(--vcl-sage); }
.kpi.sage  .v { color: var(--vcl-sage); }
.kpi.slate { border-top-color: var(--vcl-muted); }
.kpi.slate .v { color: var(--vcl-mid); }

/* CHIPS */
.chip { display: inline-flex; align-items: center; gap: 5px; font-size: 9.5pt; font-weight: 700; padding: 2px 9px; border-radius: 11px; letter-spacing: 0.02em; border: 1px solid transparent; }
.chip i { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.chip.green { background: var(--vcl-green-light); color: var(--vcl-green); border-color: #bfe2cd; } .chip.green i { background: var(--vcl-green); }
.chip.amber { background: var(--vcl-amber-light); color: var(--vcl-amber); border-color: #f0d28b; } .chip.amber i { background: var(--vcl-amber); }
.chip.muted { background: var(--vcl-surface); color: var(--vcl-mid); border-color: var(--vcl-rule); } .chip.muted i { background: var(--vcl-muted); }
.chip.blue  { background: var(--vcl-blue-light); color: var(--vcl-blue); border-color: #bec7ea; } .chip.blue i { background: var(--vcl-blue); }
.chip.red   { background: var(--vcl-red-light); color: var(--vcl-red); border-color: #f1bcb4; } .chip.red i { background: var(--vcl-red); }

/* BUTTONS */
.btn { font-size: 10pt; font-weight: 600; padding: 6px 12px; border-radius: 5px; border: 1px solid var(--vcl-rule); color: var(--vcl-ink); background: var(--vcl-white); display: inline-flex; align-items: center; gap: 6px; letter-spacing: -0.005em; }
.btn.primary { background: var(--vcl-blue); color: white; border-color: var(--vcl-blue); }
.btn.amber   { background: var(--vcl-amber); color: white; border-color: var(--vcl-amber); }
.btn.ghost   { border-color: transparent; color: var(--vcl-muted); }

/* TABLE */
table.tbl { width: 100%; border-collapse: separate; border-spacing: 0; background: var(--vcl-white); border: 1px solid var(--vcl-rule); border-radius: 8px; overflow: hidden; font-size: 10.5pt; margin: 10px 0 16px 0; }
table.tbl th { background: var(--vcl-blue); color: white; font-weight: 700; font-size: 9pt; text-transform: uppercase; letter-spacing: 0.06em; text-align: left; padding: 9px 13px; }
table.tbl td { padding: 10px 13px; border-top: 1px solid var(--vcl-rule); color: var(--vcl-ink); vertical-align: top; }
table.tbl tr:nth-child(even) td { background: var(--vcl-surface); }
table.tbl tr:first-child td { border-top: 0; }
table.tbl td.id-cell { font-family: 'JetBrains Mono', monospace; font-size: 10pt; color: var(--vcl-blue); font-weight: 700; }
table.tbl td.who { color: var(--vcl-mid); font-style: italic; width: 100px; }
table.tbl td.when { width: 80px; color: var(--vcl-muted); font-family: 'JetBrains Mono', monospace; font-size: 10pt; }

/* CARDS */
.card { background: var(--vcl-white); border: 1px solid var(--vcl-rule); border-radius: 8px; padding: 16px 18px; margin: 12px 0; }
.summary-box {
  border-left: 4px solid var(--vcl-blue);
  background: var(--vcl-blue-pale);
  padding: 14px 18px;
  margin: 14px 0 18px 0;
  border-radius: 4px;
}
.summary-box b { color: var(--vcl-navy); }

/* QA */
.qa { background: var(--vcl-surface); border-left: 4px solid var(--vcl-blue-mid); padding: 11px 14px; border-radius: 4px; margin: 8px 0; font-size: 11pt; }
.qa b { color: var(--vcl-navy); margin-right: 4px; }

/* DIAGRAMS */
svg.diagram { display: block; margin: 14px auto; max-width: 100%; height: auto; }
.caption { font-size: 9.5pt; color: var(--vcl-muted); text-align: center; margin-top: -2px; font-style: italic; }

/* SCREENSHOTS */
.screenshot {
  background: var(--vcl-white);
  border: 1px solid var(--vcl-rule);
  border-radius: 8px;
  overflow: hidden;
  margin: 14px 0;
  page-break-inside: avoid;
}
.screenshot .frame { padding: 8px 12px; background: var(--vcl-navy); color: white; font-size: 10pt; display: flex; justify-content: space-between; align-items: center; }
.screenshot .frame b { color: var(--vcl-sage); }
.screenshot .frame .url { font-family: 'JetBrains Mono', monospace; font-size: 9pt; color: var(--vcl-blue-light); }
.screenshot img { display: block; width: 100%; height: auto; }
.screenshot .caption-row { padding: 8px 12px; font-size: 10pt; color: var(--vcl-mid); border-top: 1px solid var(--vcl-rule); background: var(--vcl-surface); }

/* SIGNOFF */
.signature { margin-top: 30px; padding-top: 16px; border-top: 1px solid var(--vcl-rule); font-size: 10.5pt; color: var(--vcl-muted); display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }
.signature .slot { border-bottom: 1px solid var(--vcl-ink); padding-bottom: 32px; margin-bottom: 6px; }

/* Palette legend */
.palette-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 12px 0; }
.swatch-row { display: grid; grid-template-columns: 56px 1fr 110px; gap: 12px; align-items: center; padding: 8px 10px; border: 1px solid var(--vcl-rule); border-radius: 6px; background: var(--vcl-white); }
.swatch { height: 36px; border-radius: 5px; border: 1px solid rgba(0,0,0,0.08); }
.swatch-row .nm { font-weight: 700; color: var(--vcl-navy); font-size: 11pt; }
.swatch-row .ds { font-size: 9.5pt; color: var(--vcl-mid); }
.swatch-row .hex { font-family: 'JetBrains Mono', monospace; font-size: 10pt; color: var(--vcl-blue); text-align: right; font-weight: 700; }
.swatch-row.restricted .nm { color: var(--vcl-red); }

/* PRINT */
@media print {
  body { background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .cover { color: white; background: var(--vcl-navy) !important; }
  .bar, .foot { background: var(--vcl-navy) !important; color: white !important; }
  table.tbl th { background: var(--vcl-blue) !important; color: white !important; }
  h1, h2, h3 { page-break-after: avoid; }
  p, li { orphans: 3; widows: 3; }
  .kpi, .card, .screenshot, .qa, .summary-box, table.tbl tr, .swatch-row { page-break-inside: avoid; }
}
"""

def bar(left, right):
    return f'<div class="bar"><span class="left">{left}</span><span class="right">{right}</span></div>'

def foot(left):
    return f'<div class="foot"><span>{left}</span><img class="stamp-mini" src="data:image/png;base64,{STAMP}" alt="VCL"/></div>'

def screenshot_block(label, url, b64, caption):
    if not b64: return ''
    return f"""
<div class="screenshot">
  <div class="frame"><span><b>{label}</b></span><span class="url">{url}</span></div>
  <img src="data:image/png;base64,{b64}" alt="{label}"/>
  <div class="caption-row">{caption}</div>
</div>"""

AGENT_LOOP_SVG = r"""
<svg class="diagram" viewBox="0 0 720 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Agent loop swimlane">
  <defs>
    <marker id="arrA" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="9" markerHeight="9" orient="auto">
      <path d="M0,0 L12,6 L0,12 z" fill="#1D2766"/>
    </marker>
  </defs>
  <rect x="0" y="0"   width="720" height="76"  fill="#F4F5F8" stroke="#CBD2E0"/>
  <rect x="0" y="76"  width="720" height="76"  fill="#FFFFFF" stroke="#CBD2E0"/>
  <rect x="0" y="152" width="720" height="76"  fill="#F4F5F8" stroke="#CBD2E0"/>
  <rect x="0" y="228" width="720" height="76"  fill="#FFFFFF" stroke="#CBD2E0"/>
  <rect x="0" y="304" width="720" height="76"  fill="#F4F5F8" stroke="#CBD2E0"/>
  <g font-family="Manrope, sans-serif" font-weight="700" font-size="11" fill="#1D2766">
    <text x="12" y="44">Tanuj</text>
    <text x="12" y="120">PMO system</text>
    <text x="12" y="196">Agent (Claude / Codex)</text>
    <text x="12" y="272">UAT / OAT</text>
    <text x="12" y="348">Slack / Excel</text>
  </g>
  <g font-family="Manrope, sans-serif" font-size="11" text-anchor="middle">
    <rect x="120" y="14" width="120" height="48" fill="#2B3990" rx="6"/>
    <text x="180" y="38" fill="white" font-weight="700">1. Write plan</text>
    <text x="180" y="54" fill="#D6DBF5" font-size="10">in /app/pmo</text>

    <rect x="280" y="90" width="120" height="48" fill="#5A9367" rx="6"/>
    <text x="340" y="114" fill="white" font-weight="700">2. Allocate items</text>
    <text x="340" y="130" fill="white" font-size="10">claude / codex / human</text>

    <rect x="440" y="90" width="120" height="48" fill="#2B3990" rx="6"/>
    <text x="500" y="114" fill="white" font-weight="700">3. Dispatch shift</text>
    <text x="500" y="130" fill="#D6DBF5" font-size="10">via n8n webhook</text>

    <rect x="440" y="166" width="120" height="48" fill="#1D2766" rx="6"/>
    <text x="500" y="190" fill="white" font-weight="700">4. Agent works</text>
    <text x="500" y="206" fill="#D6DBF5" font-size="10">commits + writes notes</text>

    <rect x="280" y="166" width="120" height="48" fill="#5A9367" rx="6"/>
    <text x="340" y="190" fill="white" font-weight="700">5. Complete shift</text>
    <text x="340" y="206" fill="white" font-size="10">writes UAT/OAT runs</text>

    <rect x="280" y="242" width="120" height="48" fill="#2B3990" rx="6"/>
    <text x="340" y="266" fill="white" font-weight="700">6. UAT walk</text>
    <text x="340" y="282" fill="#D6DBF5" font-size="10">Tanuj signs off</text>

    <rect x="440" y="318" width="120" height="48" fill="#5A9367" rx="6"/>
    <text x="500" y="342" fill="white" font-weight="700">7. Slack mirror</text>
    <text x="500" y="358" fill="white" font-size="10">plan PDF posted</text>

    <rect x="120" y="318" width="120" height="48" fill="#1D2766" rx="6"/>
    <text x="180" y="342" fill="white" font-weight="700">Excel mirror</text>
    <text x="180" y="358" fill="#D6DBF5" font-size="10">via n8n</text>
  </g>
  <g stroke="#1D2766" stroke-width="1.5" fill="none" marker-end="url(#arrA)">
    <line x1="240" y1="38" x2="340" y2="86"/>
    <line x1="400" y1="114" x2="438" y2="114"/>
    <line x1="500" y1="138" x2="500" y2="164"/>
    <line x1="440" y1="190" x2="402" y2="190"/>
    <line x1="340" y1="214" x2="340" y2="240"/>
    <line x1="400" y1="266" x2="500" y2="316"/>
    <line x1="180" y1="62"  x2="180" y2="316"/>
  </g>
</svg>"""

ARCH_SVG = r"""
<svg class="diagram" viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two anchor model">
  <defs>
    <marker id="arrB" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="9" markerHeight="9" orient="auto">
      <path d="M0,0 L12,6 L0,12 z" fill="#8A909E"/>
    </marker>
  </defs>
  <g font-family="Manrope, sans-serif" font-size="11" text-anchor="middle">
    <rect x="60"  y="60" width="220" height="120" rx="10" fill="#1D2766" stroke="#5A9367" stroke-width="2"/>
    <text x="170" y="94" fill="white" font-weight="800" font-size="14">ERPNext (Frappe Cloud)</text>
    <text x="170" y="116" fill="#D6DBF5">PMO doctypes · /app/pmo</text>
    <text x="170" y="134" fill="#D6DBF5">Plans · Shifts · Tasks</text>
    <text x="170" y="152" fill="#D6DBF5">UAT · OAT · RAID · Notes</text>
    <rect x="80" y="160" width="180" height="20" rx="4" fill="#5A9367"/>
    <text x="170" y="174" fill="white" font-weight="800" font-size="10" letter-spacing="0.15em">SOURCE OF TRUTH</text>

    <rect x="440" y="20" width="220" height="80" rx="10" fill="#2B3990"/>
    <text x="550" y="50" fill="white" font-weight="800" font-size="14">Slack #ai-pmo-plans</text>
    <text x="550" y="70" fill="#D6DBF5">Plan PDFs · approvals</text>
    <text x="550" y="86" fill="#D6DBF5">read on reMarkable / Boox</text>

    <rect x="440" y="140" width="220" height="80" rx="10" fill="#FFFFFF" stroke="#1D2766" stroke-width="2"/>
    <text x="550" y="170" fill="#1D2766" font-weight="800" font-size="14">Excel mirror</text>
    <text x="550" y="190" fill="#4A4F5C">monthly slice on the share</text>
    <text x="550" y="206" fill="#4A4F5C">written by n8n, read-only</text>
  </g>
  <g stroke="#8A909E" stroke-width="1.5" fill="none" marker-end="url(#arrB)">
    <line x1="280" y1="100" x2="438" y2="60"/>
    <line x1="280" y1="140" x2="438" y2="180"/>
  </g>
</svg>"""

BUTTON_FLOW_SVG = r"""
<svg class="diagram" viewBox="0 0 720 560" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Button flow in /app/pmo — plan-level vs shift-level">
  <defs>
    <style>
      .btn-pri  { fill: #2B3990; }
      .btn-amb  { fill: #B86B00; }
      .btn-sage { fill: #5A9367; }
      .btn-out  { fill: #FFFFFF; stroke: #CBD2E0; stroke-width: 1.2; }
      .btn-txt   { fill: white; font: 600 11px Manrope, sans-serif; }
      .btn-txt-d { fill: #1D2766; font: 600 11px Manrope, sans-serif; }
      .num       { fill: #2B3990; font: 700 12px 'JetBrains Mono', monospace; }
    </style>
  </defs>

  <!-- LANE 1: PLAN LEVEL -->
  <line x1="40" y1="44" x2="700" y2="44" stroke="#5A9367" stroke-width="1.5"/>
  <text x="40" y="36" fill="#5A9367" font-family="Manrope, sans-serif" font-weight="700" font-size="10.5" letter-spacing="2.5">PLAN-LEVEL — ONE PLAN, FOUR BUTTONS (INDEPENDENT)</text>

  <text x="60"  y="74" fill="#2B3990" font-family="JetBrains Mono, monospace" font-weight="700" font-size="12">01</text>
  <text x="90"  y="74" fill="#1D2766" font-family="Manrope, sans-serif" font-weight="600" font-size="11.5">Open /app/pmo and pick the project</text>
  <rect x="60"  y="86" width="180" height="30" rx="5" class="btn-out"/>
  <text x="150" y="106" class="btn-txt-d" text-anchor="middle">VCL PMO System</text>
  <text x="60"  y="132" fill="#8A909E" font-family="Manrope, sans-serif" font-size="10.5">Lands on the project page with all the tabs across the top.</text>

  <text x="60"  y="160" fill="#2B3990" font-family="JetBrains Mono, monospace" font-weight="700" font-size="12">02</text>
  <text x="90"  y="160" fill="#1D2766" font-family="Manrope, sans-serif" font-weight="600" font-size="11.5">Plans tab — start a new plan</text>
  <rect x="60"  y="172" width="130" height="30" rx="5" class="btn-pri"/>
  <text x="125" y="192" class="btn-txt" text-anchor="middle">+ New Plan</text>
  <text x="60"  y="218" fill="#8A909E" font-family="Manrope, sans-serif" font-size="10.5">Modal opens. You type a title + description, click Save.</text>

  <text x="60"  y="246" fill="#2B3990" font-family="JetBrains Mono, monospace" font-weight="700" font-size="12">03</text>
  <text x="90"  y="246" fill="#1D2766" font-family="Manrope, sans-serif" font-weight="600" font-size="11.5">Add items + send the brief to Slack (independent of allocation)</text>
  <rect x="60"  y="258" width="130" height="30" rx="5" class="btn-pri"/>
  <text x="125" y="278" class="btn-txt" text-anchor="middle">+ Add Item</text>
  <rect x="210" y="258" width="180" height="30" rx="5" class="btn-amb"/>
  <text x="300" y="278" class="btn-txt" text-anchor="middle">Send PDF to Slack</text>
  <text x="60"  y="304" fill="#8A909E" font-family="Manrope, sans-serif" font-size="10.5">Add Item builds the proposed-item list. Send PDF renders the plan and posts it to #ai-pmo-plans — does NOT change the plan's status.</text>

  <text x="60"  y="332" fill="#2B3990" font-family="JetBrains Mono, monospace" font-weight="700" font-size="12">04</text>
  <text x="90"  y="332" fill="#1D2766" font-family="Manrope, sans-serif" font-weight="600" font-size="11.5">Tick items + allocate to an agent or human (the act of allocating IS the approval)</text>
  <rect x="60"  y="344" width="160" height="30" rx="5" class="btn-out"/>
  <text x="140" y="364" class="btn-txt-d" text-anchor="middle">Allocate to Claude</text>
  <rect x="230" y="344" width="160" height="30" rx="5" class="btn-out"/>
  <text x="310" y="364" class="btn-txt-d" text-anchor="middle">Allocate to Codex</text>
  <rect x="400" y="344" width="160" height="30" rx="5" class="btn-out"/>
  <text x="480" y="364" class="btn-txt-d" text-anchor="middle">Allocate to Human</text>
  <text x="60"  y="390" fill="#8A909E" font-family="Manrope, sans-serif" font-size="10.5">Items become Shifts. Each Shift auto-creates UAT/OAT records, bucketed under the shift.</text>

  <!-- LANE 2: SHIFT LEVEL -->
  <line x1="40" y1="430" x2="700" y2="430" stroke="#5A9367" stroke-width="1.5"/>
  <text x="40" y="422" fill="#5A9367" font-family="Manrope, sans-serif" font-weight="700" font-size="10.5" letter-spacing="2.5">SHIFT-LEVEL — PER-SHIFT AFTER ALLOCATION</text>

  <text x="60"  y="454" fill="#2B3990" font-family="JetBrains Mono, monospace" font-weight="700" font-size="12">05</text>
  <text x="90"  y="454" fill="#1D2766" font-family="Manrope, sans-serif" font-weight="600" font-size="11.5">On each shift row, dispatch the work</text>
  <rect x="60"  y="466" width="160" height="30" rx="5" class="btn-pri"/>
  <text x="140" y="486" class="btn-txt" text-anchor="middle">Execute via n8n</text>
  <rect x="230" y="466" width="90" height="30" rx="5" class="btn-out"/>
  <text x="275" y="486" class="btn-txt-d" text-anchor="middle">Start</text>
  <rect x="330" y="466" width="110" height="30" rx="5" class="btn-out"/>
  <text x="385" y="486" class="btn-txt-d" text-anchor="middle">Complete</text>
  <rect x="450" y="466" width="90" height="30" rx="5" class="btn-out"/>
  <text x="495" y="486" class="btn-txt-d" text-anchor="middle">Block</text>
  <text x="60"  y="518" fill="#8A909E" font-family="Manrope, sans-serif" font-size="10.5">Execute via n8n posts to the webhook → agent runs → calls Complete back into ERPNext, which logs the UAT/OAT runs.</text>
</svg>"""

# Figure 4 — Tanuj's page-4 hand-written flow (auto plan-review loop)
REVIEW_FLOW_SVG = r"""
<svg class="diagram" viewBox="0 0 720 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Auto plan-review loop (Tanuj's page-4 sketch)">
  <defs>
    <marker id="arrR" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="9" markerHeight="9" orient="auto">
      <path d="M0,0 L12,6 L0,12 z" fill="#1D2766"/>
    </marker>
    <style>
      .nd-tanuj  { fill: #5A9367; }
      .nd-system { fill: #2B3990; }
      .nd-agent  { fill: #1D2766; }
      .nd-slack  { fill: #B86B00; }
      .lbl       { fill: white; font: 700 12px Manrope, sans-serif; }
      .sub       { fill: #D6DBF5; font: 10px Manrope, sans-serif; }
      .num       { fill: #5A9367; font: 700 12px 'JetBrains Mono', monospace; }
    </style>
  </defs>

  <g text-anchor="middle">
    <!-- 1. Tanuj: rough plan -->
    <text x="120" y="26" class="num">01</text>
    <rect x="40" y="36" width="160" height="60" rx="8" class="nd-tanuj"/>
    <text x="120" y="60" class="lbl">Tanuj writes a rough plan</text>
    <text x="120" y="80" class="sub">title + 1-line direction</text>

    <!-- 2. Scheduler picks it up -->
    <text x="360" y="26" class="num">02</text>
    <rect x="280" y="36" width="160" height="60" rx="8" class="nd-system"/>
    <text x="360" y="60" class="lbl">Scheduler picks it up</text>
    <text x="360" y="80" class="sub">nightly cron — capacity-aware</text>

    <!-- 3. Codex or Claude reads -->
    <text x="600" y="26" class="num">03</text>
    <rect x="520" y="36" width="160" height="60" rx="8" class="nd-agent"/>
    <text x="600" y="60" class="lbl">Codex (or Claude)</text>
    <text x="600" y="80" class="sub">based on token / usage</text>

    <!-- 4. Drafts plan + sends to Slack -->
    <text x="600" y="146" class="num">04</text>
    <rect x="520" y="156" width="160" height="60" rx="8" class="nd-slack"/>
    <text x="600" y="180" class="lbl">Agent drafts the plan</text>
    <text x="600" y="200" class="sub">posts PDF + Approve button</text>

    <!-- 5. Tanuj approves -->
    <text x="360" y="146" class="num">05</text>
    <rect x="280" y="156" width="160" height="60" rx="8" class="nd-tanuj"/>
    <text x="360" y="180" class="lbl">Tanuj approves on Slack</text>
    <text x="360" y="200" class="sub">one click on reMarkable</text>

    <!-- 6. System bulk-allocates -->
    <text x="120" y="146" class="num">06</text>
    <rect x="40" y="156" width="160" height="60" rx="8" class="nd-system"/>
    <text x="120" y="180" class="lbl">System bulk-allocates</text>
    <text x="120" y="200" class="sub">calls allocate_plan_items</text>

    <!-- 7. Shifts flow into Figure 1 -->
    <text x="360" y="256" class="num">→</text>
    <rect x="160" y="266" width="400" height="40" rx="6" class="nd-agent"/>
    <text x="360" y="290" class="lbl">From here, Figure 1 takes over — Execute via n8n, Start, Complete</text>
  </g>

  <g stroke="#1D2766" stroke-width="1.5" fill="none" marker-end="url(#arrR)">
    <line x1="200" y1="66" x2="278" y2="66"/>
    <line x1="440" y1="66" x2="518" y2="66"/>
    <line x1="600" y1="96" x2="600" y2="154"/>
    <line x1="520" y1="186" x2="442" y2="186"/>
    <line x1="280" y1="186" x2="202" y2="186"/>
    <line x1="120" y1="216" x2="360" y2="264"/>
  </g>
</svg>"""

COVER = f"""
<section class="page">
  <div class="cover">
    <div class="cover-stripe-top"></div>
    <div class="org-line">
      <div class="caps">Vimit Converters Limited</div>
      <div class="stamp"><img src="data:image/png;base64,{STAMP}" alt="VCL Stamp"/></div>
    </div>
    <div>
      <div class="title">VCL PMO System</div>
      <div class="lede">A single, plain-English status pack for the project we are using to build the system that runs all our other projects.</div>
      <div class="accent-rule"></div>
      <div class="meta-grid">
        <div><div class="k">Project ID</div><div class="v">VCL-DEV-PMO-002</div></div>
        <div><div class="k">Sponsor</div><div class="v">Tanuj Haria</div></div>
        <div><div class="k">Phase</div><div class="v">Phase 2 — Build</div></div>
        <div><div class="k">Started</div><div class="v">27 May 2026</div></div>
        <div><div class="k">Target finish</div><div class="v">7 June 2026</div></div>
        <div><div class="k">This report</div><div class="v">28 May 2026</div></div>
      </div>
    </div>
    <div class="cover-foot">
      <span>Prepared by Claude · review on reMarkable / Boox Air 5 · VCL Brand v1.1</span>
      <span class="confidential">CONFIDENTIAL · VCL INTERNAL</span>
    </div>
  </div>
</section>"""

P_STATUS = f"""
<section class="page">
  {bar('VCL PMO · Status Report', 'page 02 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>Where we are today</h1>
  <div class="sub">Status as at 21:30 EAT, 28 May 2026.</div>

  <div class="kpis">
    <div class="kpi green"><div class="l">Done</div><div class="v">2</div><div class="d">work blocks shipped</div></div>
    <div class="kpi amber"><div class="l">In flight</div><div class="v">1</div><div class="d">waiting on one setup step</div></div>
    <div class="kpi amber"><div class="l">Waiting</div><div class="v">1</div><div class="d">design write-up pending</div></div>
    <div class="kpi sage"><div class="l">Health</div><div class="v" style="font-size:18pt;">On track</div><div class="d">target 7 Jun stands</div></div>
  </div>

  <div class="summary-box">
    <b>One sentence:</b> The PMO is being built inside ERPNext as the new home for all VCL development work — so plans, tasks, agents, testing and approvals all live in one place. As of today, four of the four planned work blocks are either shipped or coded; the only remaining steps before the system is end-to-end operational are one Slack token install and one design write-up.
  </div>

  <h2>What we just finished</h2>
  <table class="tbl">
    <thead><tr><th style="width:32%;">What</th><th>Why it matters</th><th style="width:90px;">Status</th></tr></thead>
    <tbody>
      <tr><td><b>Back button works everywhere</b></td><td>Pressing browser Back from any sub-page now returns to the right tab instead of landing on a "page not available" error. Reload and pasted links also work.</td><td><span class="chip green"><i></i>DONE</span></td></tr>
      <tr><td><b>Tests grouped by what they test</b></td><td>Instead of one long flat list of UAT/OAT items, each shift's tests sit under a clear header showing pass/fail/blocked counts. Easier to walk through, easier to sign off.</td><td><span class="chip green"><i></i>DONE</span></td></tr>
    </tbody>
  </table>

  <h2>Built but waiting on one setup step</h2>
  <table class="tbl">
    <thead><tr><th style="width:32%;">What</th><th>Why it matters</th><th style="width:32%;">What it needs</th></tr></thead>
    <tbody>
      <tr><td><b>Plans go to Slack as PDFs</b></td><td>One click renders any plan as a clean, A4, VCL-branded PDF and drops it in <code>#ai-pmo-plans</code>. Sized for reMarkable / Boox.</td><td>Install a Slack bot token in the site settings, invite the bot to the channel. About 10 minutes of admin.</td></tr>
    </tbody>
  </table>

  <h2>Still on the drawing board</h2>
  <table class="tbl">
    <thead><tr><th style="width:32%;">What</th><th>Why it matters</th><th style="width:30%;">Owner</th></tr></thead>
    <tbody>
      <tr><td><b>Auto-review of new plans by agents</b></td><td>Today every new plan needs Tanuj to manually choose Claude / Codex / human per item. The design will let an agent draft the proposed allocation overnight and send Tanuj a single Approve button.</td><td>Codex — design only, by 30 May</td></tr>
    </tbody>
  </table>
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

P_WORKFLOW = f"""
<section class="page">
  {bar('VCL PMO · How it works', 'page 03 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>How it works — the buttons in order</h1>
  <div class="sub">Two lanes: plan-level (four buttons, independent) and shift-level (per-shift after allocation). Blue = primary action; amber = brand action; outline = secondary.</div>

  {BUTTON_FLOW_SVG}
  <p class="caption">Figure 1. Plan-level vs shift-level — the four plan-level buttons act on a plan but don't change its status; the act of allocating IS the approval. The shift-level row only appears once items become shifts.</p>

  <h2>Then the agent loop fires</h2>
  <p>Once a shift is dispatched, the rest of the cycle runs without you. Each lane is one actor; arrows show the handover.</p>

  {AGENT_LOOP_SVG}
  <p class="caption">Figure 2. One full loop from plan to signed-off tests, mirrored to Slack and Excel.</p>
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

# New page — auto plan-review flow (Tanuj's page-4 sketch turned into a diagram)
P_REVIEW_FLOW = f"""
<section class="page">
  {bar('VCL PMO · Auto plan-review (proposed)', 'page 04 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>The auto plan-review loop</h1>
  <div class="sub">Direct from Tanuj's hand-written page-4 annotation on the v4 review. This is the design SHIFT-0002 (Codex) is now writing up as a spec.</div>

  {REVIEW_FLOW_SVG}
  <p class="caption">Figure 3. The six-step auto-review loop. Tanuj's rough plan → agent drafts → Slack approval → bulk-allocate. After step 6, control returns to Figure 1 (Execute via n8n → Start → Complete).</p>

  <h2>What changes in /app/pmo</h2>
  <ul>
    <li><b>Inbox becomes the queue.</b> The Inbox tab gets filtered to "needs Tanuj" — plans waiting for approval, shifts waiting for UAT sign-off, blocked requirements. Today it shows too much.</li>
    <li><b>New Plan stays the entry point.</b> Tanuj writes a one-line direction in /app/pmo (same modal as today) — no need to leave for Slack.</li>
    <li><b>The agent drafts.</b> Codex (default) or Claude (fallback when Codex is at quota) reads the rough plan + project context + the last 5 approved plans on the same project, expands the items, hints assignees.</li>
    <li><b>The PDF lands in Slack.</b> Same <code>Send PDF to Slack</code> button — but now with an "Approve all to Claude / Codex / Human" Block-Kit button below the file.</li>
    <li><b>One click bulk-allocates.</b> The button calls <code>slack_approve_plan(plan_id, allocate_to)</code> which delegates to the existing <code>allocate_plan_items</code> and stamps <code>approved_by</code> + <code>approved_at</code>.</li>
  </ul>

  <h3>What stays the same</h3>
  <ul>
    <li>You can still allocate manually in /app/pmo whenever you want. The auto-loop is an option, not a replacement.</li>
    <li>Execute via n8n + Complete are unchanged.</li>
    <li>UAT/OAT records auto-create on allocation, same as today.</li>
  </ul>
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

# New page — FAQ-style answers to Tanuj's 7 annotations on v4
P_FAQ = f"""
<section class="page">
  {bar('VCL PMO · Your questions, answered', 'page 05 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>Your review questions, answered</h1>
  <div class="sub">All seven annotations from the v4 reMarkable review (archived at <code>briefs/review/2026-05-28_status_report_v4_annotated.pdf</code>).</div>

  <div class="qa"><b>Q1. How do we install the Slack bot?</b> See the separate one-page setup card (<code>VCL-PMO_slack_bot_setup_card.pdf</code>). Five steps: create app → add <code>chat:write</code> + <code>files:write</code> scopes → install → invite to <code>#ai-pmo-plans</code> → drop the <code>xoxb-…</code> token into Frappe Cloud's site_config via <code>bench set-config</code>. About 10 minutes.</div>

  <div class="qa"><b>Q2. What about new projects?</b> Today the SPA has no "New Project" button — you have to use the bare Desk form at <code>/app/pmo-project/new</code>. Codex is adding a <code>+ New Project</code> button to the portfolio toolbar (next to "New Requirement"), wired to a new <code>create_project</code> API. Codex Item B in the review-response brief.</div>

  <div class="qa"><b>Q3. Who approves new plans?</b> Today: nothing. A new Plan sits at <code>status=Draft</code> until you click "Allocate selected to …" — the act of allocating IS the approval. Auto-review (Figure 3 above, SHIFT-0002) introduces a Slack-based approval button so you can approve without opening /app/pmo.</div>

  <div class="qa"><b>Q4. How are Send PDF / Allocate / Execute via n8n linked?</b> They're not — they're independent. <b>Send PDF</b> renders + posts and does NOT change plan state. <b>Allocate</b> promotes ticked items into Shifts (status = Allocated). <b>Execute via n8n</b> is per-shift, fires the agent webhook. Figure 1 on page 3 has been split into plan-level vs shift-level lanes to make this obvious.</div>

  <div class="qa"><b>Q5. What does the agent do, and how does it fire up?</b> (1) <code>dispatch_shift(shift_id)</code> reads <code>pmo_n8n_dispatch_url</code> from site_config; (2) POSTs the shift payload to n8n; (3) n8n routes by <code>assigned_to</code> (claude / codex) — currently designed to trigger a CLI runner on the dev machine; (4) the agent works, commits, then POSTs back to <code>/api/method/.../complete_shift</code> with output notes + UAT/OAT results; (5) ERPNext flips status → Done, stamps <code>actual_end</code>, logs the UAT/OAT runs. The n8n routing layer is the gap to close.</div>

  <div class="qa"><b>Q6. The plan-review flow you sketched.</b> That's SHIFT-0002 — Codex's allocated planning shift. Captured exactly as you wrote it, drawn as Figure 3 above. Codex is finishing the spec (<code>briefs/2026-05-28_SCHEDULED_PLAN_REVIEW_SPEC.md</code>) covering: scheduler trigger, capacity probe (<code>pmo_codex_available</code> site_config flag), reviewer payload, Slack-Block-Kit approval surface, action on approve, failure modes.</div>

  <div class="qa"><b>Q7. Inbox first-page UX.</b> Agreed — Inbox is too noisy. Codex is filtering Inbox to "needs Tanuj" only: plans waiting for allocation, shifts waiting for UAT sign-off, blocked requirements, plan reviews pending (once SHIFT-0002 ships). Codex Item C in the review-response brief.</div>

  <h2>Where the work is now</h2>
  <table class="tbl">
    <thead><tr><th>Owner</th><th>Item</th><th class="when" style="width:90px;">Status</th></tr></thead>
    <tbody>
      <tr><td class="who">Claude</td><td>This v5 status report — incorporates all 7 answers, adds Figure 3 (auto-review), splits Figure 1 lanes.</td><td><span class="chip green"><i></i>DONE</span></td></tr>
      <tr><td class="who">Claude</td><td>Slack bot setup card (one-page A4).</td><td><span class="chip green"><i></i>DONE</span></td></tr>
      <tr><td class="who">Codex</td><td>SHIFT-0002 spec from Tanuj's page-4 flow (Item A).</td><td><span class="chip amber"><i></i>ASSIGNED</span></td></tr>
      <tr><td class="who">Codex</td><td>+ New Project button on portfolio toolbar (Item B).</td><td><span class="chip amber"><i></i>ASSIGNED</span></td></tr>
      <tr><td class="who">Codex</td><td>Inbox filter — "needs Tanuj" only (Item C).</td><td><span class="chip amber"><i></i>ASSIGNED</span></td></tr>
      <tr><td class="who">Tanuj</td><td>Install Slack bot per the setup card.</td><td><span class="chip muted"><i></i>READY</span></td></tr>
      <tr><td class="who">Tanuj</td><td>UAT walk SHIFT-0001 (back-nav fix already shipped).</td><td><span class="chip muted"><i></i>READY</span></td></tr>
    </tbody>
  </table>
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

P_ARCH = f"""
<section class="page">
  {bar('VCL PMO · Architecture', 'page 06 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>Where each piece lives</h1>
  <p>We deliberately do <i>not</i> try to put everything in one tool. Two anchors: ERPNext is the operational source of truth, Slack + Excel are downstream review surfaces that already work for the team.</p>

  {ARCH_SVG}
  <p class="caption">Figure 3. One source of truth, two downstream review surfaces. No reverse writes from Slack or Excel back into ERPNext.</p>

  <h3>What that means in practice</h3>
  <ul>
    <li><b>You edit in ERPNext.</b> Everything else mirrors automatically.</li>
    <li><b>Slack is for reading and annotating.</b> Plans land there as PDFs; nothing in Slack writes back.</li>
    <li><b>Excel is for the monthly slice.</b> n8n writes a workbook per project on the share; you never edit it directly.</li>
    <li><b>Agents talk to ERPNext directly</b> via whitelisted API methods. n8n is the routing layer, not a data store.</li>
  </ul>
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

P_SHOTS = f"""
<section class="page">
  {bar('VCL PMO · The deployed UI', 'page 07 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>What you actually see at /app/pmo</h1>
  <p>Captured today against the live site (<code>https://vimitconverters.frappe.cloud/app/pmo</code>) using a Playwright headless browser with API-token auth. These are the screens you sign in to.</p>

  {screenshot_block('Portfolio · Inbox', '/app/pmo', SHOT_INBOX, 'The Inbox view — top: live KPI ticker (UTC, projects, requirements done, in review, RAID open). Below: portfolio-level requirements that need attention right now. Status chips match Brand v1.1 (Green = Done, Amber = In Review, Sage / Blue = brand accents).')}

  {screenshot_block('Portfolio · Projects', '/app/pmo (Projects tab)', SHOT_PROJECTS, 'Two projects currently live: VCL PMO System (this one) and Production Log & Job Card System. Progress bars + status chips. Click a card to drop into the project workspace.')}
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

P_SHOTS_2 = f"""
<section class="page">
  {bar('VCL PMO · Project workspace', 'page 08 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>Inside the project workspace</h1>
  <p>Clicking the project card opens its full workspace: 13 sub-tabs across the top, project meta on the side panel, breadcrumb navigation. This is where plans get written and shifts get allocated.</p>

  {screenshot_block('VCL PMO System · Overview', '/app/pmo#p/VCL-DEV-PMO-002', SHOT_OVERVIEW, 'Project Overview tab. Title, current phase, progress card (35%), open milestones (1), open RAID items (1). Sub-tabs: Overview · Timeline · Open Items · Plans · Shifts · Milestones · RAID · UAT · OAT · Test History · Documentation · Activity.')}

  {screenshot_block('VCL PMO System · Plan PLAN-0002', '/app/pmo#p/VCL-DEV-PMO-002/plans/PLAN-0002', SHOT_PLAN, 'A specific plan opened: PLAN-0002 "Slack Integration" — Allocated status, 1 proposed item. Description card with the full plan text including the target Slack channel URL. Below: bulk-action buttons (Add Item, Allocate to Claude / Codex / Human) and the items table showing SHIFT-0003 promoted from this plan.')}
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

def swatch(name, hex_, desc, restricted=False):
    cls = ' restricted' if restricted else ''
    return f'<div class="swatch-row{cls}"><div class="swatch" style="background:{hex_};"></div><div><div class="nm">{name}</div><div class="ds">{desc}</div></div><div class="hex">{hex_}</div></div>'

P_BRAND = f"""
<section class="page">
  {bar('VCL PMO · Brand reference', 'page 09 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>VCL Brand v1.1 — the colours we use</h1>
  <p>Every colour in this report comes from VCL Brand & Visual Identity Standards v1.1 (May 2026). Verified against the deployed <code>pmo.css</code> tokens at <code>/app/pmo</code>. No invented hexes.</p>

  <h2>Primary identity</h2>
  <div class="palette-grid">
    {swatch('VCL Navy',       '#1D2766', 'H1, document titles, cover page')}
    {swatch('VCL Blue',       '#2B3990', 'Primary action, links, H2, table header')}
    {swatch('VCL Blue Mid',   '#5C6DBE', 'Dividers, secondary icons, chart lines')}
    {swatch('VCL Blue Light', '#D6DBF5', 'Callout fills, info backgrounds')}
    {swatch('VCL Blue Pale',  '#EEF0FB', 'Page tints, hover states')}
    {swatch('VCL Sage',       '#5A9367', 'Brand accent — logo, user pill, active nav')}
  </div>

  <h2>Status colours</h2>
  <div class="palette-grid">
    {swatch('VCL Green',       '#1B7A45', 'Pricing, Complete status, positive KPIs')}
    {swatch('VCL Green Light', '#D4EDE0', 'Complete row fills')}
    {swatch('VCL Amber',       '#B86B00', 'Warnings, In Progress, AR overdue <90d')}
    {swatch('VCL Amber Light', '#FFF0CC', 'Warning row fills')}
    {swatch('VCL Red',         '#C0392B', 'RESTRICTED · errors only, 90+ day AR', restricted=True)}
    {swatch('VCL Red Light',   '#FADBD8', 'RESTRICTED · error row fills only', restricted=True)}
  </div>

  <h2>Neutrals</h2>
  <div class="palette-grid">
    {swatch('Ink',     '#1C1C1E', 'Body text, H3+')}
    {swatch('Mid Grey','#4A4F5C', 'Secondary text, captions')}
    {swatch('Muted',   '#8A909E', 'Footnotes, metadata, helper labels')}
    {swatch('Rule',    '#CBD2E0', 'All borders / dividers')}
    {swatch('Surface', '#F4F5F8', 'Alt table rows, page tints')}
    {swatch('White',   '#FFFFFF', 'Page background')}
  </div>

  <h2>Rules of use</h2>
  <ul>
    <li><b>Blue is primary.</b> Not navy-black. Not orange-amber. Buttons, links, table headers — all VCL Blue <code>#2B3990</code>.</li>
    <li><b>Sage is the brand accent.</b> Logo mark, user-pill avatar, active nav indicator. NOT for status colour.</li>
    <li><b>Green is for money + complete.</b> Pricing figures and "Done" — never use blue for these.</li>
    <li><b>Amber replaces red for most warnings.</b> Red is restricted to system errors and 90+ day AR overdue.</li>
    <li><b>Typography:</b> Manrope (UI), JetBrains Mono (IDs, code). Embedded as base64 in this PDF; no CDN.</li>
  </ul>
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

P_NEXT = f"""
<section class="page">
  {bar('VCL PMO · What comes next', 'page 10 · 28 may 2026')}
  <div style="padding:0 6mm;">
  <h1>What comes next</h1>

  <h2>Before this Friday (29–30 May)</h2>
  <table class="tbl">
    <thead><tr><th class="who" style="width:110px;">Owner</th><th>Action</th><th class="when">By</th></tr></thead>
    <tbody>
      <tr><td class="who">Tanuj</td><td>Install a Slack bot in the workspace, drop its token into the PMO site settings, invite it to <b>#ai-pmo-plans</b>.</td><td class="when">29 May</td></tr>
      <tr><td class="who">Tanuj</td><td>Walk the back-button fix on three real flows (Plans → Plan, Shifts → Shift, UAT case detail). Sign off SHIFT-0001.</td><td class="when">29 May</td></tr>
      <tr><td class="who">Tanuj</td><td>Once the bot is in: click <b>Send PDF to Slack</b> on one plan. Confirm it lands and reads cleanly on reMarkable. Sign off SHIFT-0003.</td><td class="when">29 May</td></tr>
      <tr><td class="who">Codex</td><td>Write the spec for "auto-review of new plans" — six points, no code. Lands as a markdown doc in the repo.</td><td class="when">30 May</td></tr>
    </tbody>
  </table>

  <h2>Following week (2–7 June)</h2>
  <table class="tbl">
    <thead><tr><th class="who" style="width:140px;">Owner</th><th>Action</th><th class="when">By</th></tr></thead>
    <tbody>
      <tr><td class="who">Tanuj</td><td>Review the auto-review spec, mark it Pass, hand off to Claude or Codex to build.</td><td class="when">2 Jun</td></tr>
      <tr><td class="who">Tanuj</td><td>Close the Phase 2 Foundation milestone (MS-PMO-001). System officially the master for development work.</td><td class="when">3 Jun</td></tr>
      <tr><td class="who">Claude or Codex</td><td>Build the scheduled plan-review job (nightly sweep, capacity-aware routing, single approve action).</td><td class="when">5 Jun</td></tr>
      <tr><td class="who">Tanuj</td><td>UAT the scheduled job end-to-end. Mark project Done.</td><td class="when">7 Jun</td></tr>
    </tbody>
  </table>

  <h2>Open questions for Tanuj</h2>
  <div class="qa"><b>Q1.</b> Slack bot — new <i>VCL PMO Bot</i> or reuse an existing workspace bot? (Recommend new, scopes stay minimal.)</div>
  <div class="qa"><b>Q2.</b> Auto-review trigger — every 6 hours, nightly at 23:00, or hourly when an unallocated plan appears? (Recommend nightly 23:00.)</div>
  <div class="qa"><b>Q3.</b> Capacity probe for Codex — manual flag in site settings, or external monitor file? (Recommend manual flag this round.)</div>
  <div class="qa"><b>Q4.</b> Where do approvals live — Slack with a button, Telegram with a reply, or just the Plans tab? (Recommend Slack permalink back to /app/pmo.)</div>

  <div class="signature">
    <div><div class="slot">&nbsp;</div><div>Tanuj Haria — Sponsor</div></div>
    <div><div class="slot">&nbsp;</div><div>Date</div></div>
  </div>
  </div>
  {foot('VCL PMO · VCL-DEV-PMO-002 · 28 May 2026')}
</section>"""

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>VCL PMO System — Status Report</title>
<style>{CSS
  .replace('__MR_400__', MR_400)
  .replace('__MR_600__', MR_600)
  .replace('__MR_700__', MR_700)
  .replace('__MR_800__', MR_800)
  .replace('__JB_400__', JB_400)
  .replace('__JB_700__', JB_700)
}</style>
</head>
<body>
{COVER}
{P_STATUS}
{P_WORKFLOW}
{P_REVIEW_FLOW}
{P_FAQ}
{P_ARCH}
{P_SHOTS}
{P_SHOTS_2}
{P_BRAND}
{P_NEXT}
</body>
</html>
"""

out = REPO / 'briefs/VCL-DEV-PMO-002_status_report.html'
out.write_text(HTML)
print(f"wrote {out} ({len(HTML):,} bytes)")
