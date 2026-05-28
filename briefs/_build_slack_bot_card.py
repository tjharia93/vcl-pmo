#!/usr/bin/env python3
"""One-page A4 setup card: install the VCL PMO Slack bot.

Same VCL Brand v1.1 chrome as the status report. Self-contained HTML
with Manrope + JetBrains Mono base64-embedded + the VCL stamp.
"""
from pathlib import Path
import base64

REPO = Path('/home/tanujharia/projects/vcl-pmo')
B64 = Path('/tmp/b64')

def lb(n): return B64.joinpath(n).read_text()

STAMP = lb('stamp.b64')
MR_400, MR_600, MR_700, MR_800 = lb('manrope-400.b64'), lb('manrope-600.b64'), lb('manrope-700.b64'), lb('manrope-800.b64')
JB_400, JB_700 = lb('jbmono-400.b64'), lb('jbmono-700.b64')

CSS = r"""
@font-face{font-family:'Manrope';font-weight:400;src:url(data:font/ttf;base64,__MR_400__) format('truetype')}
@font-face{font-family:'Manrope';font-weight:600;src:url(data:font/ttf;base64,__MR_600__) format('truetype')}
@font-face{font-family:'Manrope';font-weight:700;src:url(data:font/ttf;base64,__MR_700__) format('truetype')}
@font-face{font-family:'Manrope';font-weight:800;src:url(data:font/ttf;base64,__MR_800__) format('truetype')}
@font-face{font-family:'JetBrains Mono';font-weight:400;src:url(data:font/ttf;base64,__JB_400__) format('truetype')}
@font-face{font-family:'JetBrains Mono';font-weight:700;src:url(data:font/ttf;base64,__JB_700__) format('truetype')}
:root{
  --vcl-blue:#2B3990;--vcl-navy:#1D2766;--vcl-blue-mid:#5C6DBE;
  --vcl-blue-light:#D6DBF5;--vcl-blue-pale:#EEF0FB;
  --vcl-sage:#5A9367;--vcl-green:#1B7A45;--vcl-green-light:#D4EDE0;
  --vcl-amber:#B86B00;--vcl-amber-light:#FFF0CC;
  --vcl-red:#C0392B;--vcl-red-light:#FADBD8;
  --vcl-ink:#1C1C1E;--vcl-mid:#4A4F5C;--vcl-muted:#8A909E;
  --vcl-rule:#CBD2E0;--vcl-surface:#F4F5F8;--vcl-white:#FFFFFF;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;font-family:'Manrope',-apple-system,system-ui,sans-serif;color:var(--vcl-ink);background:var(--vcl-white);font-size:9.5pt;line-height:1.4;letter-spacing:-0.005em}
.mono,code,kbd{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:8.5pt}
@page{size:A4 portrait;margin:0}
.page{width:210mm;height:297mm;padding:0;page-break-after:always;overflow:hidden;display:flex;flex-direction:column}
.bar{background:var(--vcl-navy);color:white;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:3px solid var(--vcl-sage);font-size:9.5pt;font-weight:600;letter-spacing:0.08em;flex-shrink:0}
.bar .left{text-transform:uppercase;color:var(--vcl-sage)}
.bar .right{color:var(--vcl-blue-light);font-family:'JetBrains Mono',monospace;font-size:8.5pt;font-weight:400;letter-spacing:0.04em}
.foot{background:var(--vcl-navy);color:var(--vcl-blue-light);padding:6px 16px;display:flex;align-items:center;justify-content:space-between;border-top:3px solid var(--vcl-sage);font-size:8pt;font-family:'JetBrains Mono',monospace;letter-spacing:0.04em;flex-shrink:0}
.foot .stamp-mini{width:26px;height:26px;opacity:0.95}
.inner{padding:10mm 14mm 8mm 14mm;flex:1}

.title-row{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:8px}
.title-row .stamp img{width:62px;height:62px}
h1{font-family:'Manrope',sans-serif;font-weight:800;font-size:20pt;color:var(--vcl-navy);letter-spacing:-0.015em;margin:0 0 3px 0;line-height:1.05}
.sub{color:var(--vcl-mid);font-size:10pt;font-weight:400}
.lede{background:var(--vcl-blue-pale);border-left:4px solid var(--vcl-blue);padding:9px 13px;margin:8px 0 10px 0;border-radius:4px;font-size:9.5pt;color:var(--vcl-ink);line-height:1.45}
.lede b{color:var(--vcl-navy)}

.steps{counter-reset:s}
.step{display:grid;grid-template-columns:30px 1fr;gap:11px;margin:6px 0;padding:7px 12px;background:var(--vcl-white);border:1px solid var(--vcl-rule);border-left:4px solid var(--vcl-blue);border-radius:5px}
.step .num{counter-increment:s;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:17pt;color:var(--vcl-blue);line-height:1;text-align:center}
.step .num::before{content:counter(s, decimal-leading-zero)}
.step h3{margin:0 0 3px 0;font-size:10.5pt;color:var(--vcl-navy);font-weight:700;letter-spacing:-0.005em}
.step .body{color:var(--vcl-ink);font-size:9.5pt;line-height:1.4}
.step code{background:var(--vcl-surface);padding:0px 5px;border-radius:3px;color:var(--vcl-blue);border:1px solid var(--vcl-rule);font-size:8.5pt}
.step .cmd{display:block;background:var(--vcl-navy);color:#D6DBF5;padding:6px 10px;border-radius:4px;margin-top:4px;font-family:'JetBrains Mono',monospace;font-size:8pt;line-height:1.55;white-space:pre-wrap}

.troubleshoot{margin-top:10px}
.troubleshoot h2{font-family:'Manrope',sans-serif;font-weight:700;font-size:11pt;color:var(--vcl-blue);margin:4px 0 4px 0;padding-bottom:3px;border-bottom:2px solid var(--vcl-blue);letter-spacing:-0.01em}
.troubleshoot p{margin:3px 0 5px 0;font-size:9pt}
table.tbl{width:100%;border-collapse:separate;border-spacing:0;background:var(--vcl-white);border:1px solid var(--vcl-rule);border-radius:5px;overflow:hidden;font-size:8.5pt;margin:3px 0}
table.tbl th{background:var(--vcl-blue);color:white;font-weight:700;font-size:8pt;text-transform:uppercase;letter-spacing:0.06em;text-align:left;padding:6px 10px}
table.tbl td{padding:5px 10px;border-top:1px solid var(--vcl-rule);color:var(--vcl-ink);vertical-align:top}
table.tbl tr:first-child td{border-top:0}
table.tbl tr:nth-child(even) td{background:var(--vcl-surface)}
@media print{
  body{background:white;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .bar,.foot{background:var(--vcl-navy)!important;color:white!important}
  table.tbl th{background:var(--vcl-blue)!important;color:white!important}
}
"""

HTML = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>VCL PMO Slack Bot — Setup Card</title>
<style>{CSS.replace('__MR_400__',MR_400).replace('__MR_600__',MR_600).replace('__MR_700__',MR_700).replace('__MR_800__',MR_800).replace('__JB_400__',JB_400).replace('__JB_700__',JB_700)}</style>
</head><body>

<section class="page">
  <div class="bar"><span class="left">VCL PMO · Setup Card</span><span class="right">28 may 2026 · 1 page · A4</span></div>
  <div class="inner">

    <div class="title-row">
      <div>
        <h1>Slack bot — install in 10 minutes</h1>
        <div class="sub">Turns on the <b>Send PDF to Slack</b> button in /app/pmo so plans land in <code>#ai-pmo-plans</code> as VCL-branded PDFs.</div>
      </div>
      <div class="stamp"><img src="data:image/png;base64,{STAMP}" alt="VCL"/></div>
    </div>

    <div class="lede">
      <b>What you're setting up.</b> A Slack app named <i>VCL PMO Bot</i> with two
      bot scopes (<code>chat:write</code> + <code>files:write</code>) installed to the
      Vimit Converters workspace. Its <code>xoxb-…</code> token goes into Frappe Cloud's
      site_config. The PMO page uses Slack's external-upload flow to render any
      plan as a VCL-branded A4 PDF and post it into <code>#ai-pmo-plans</code> (channel
      ID <code>C0B5DA141MM</code>).
    </div>

    <div class="steps">

      <div class="step">
        <div class="num"></div>
        <div>
          <h3>Create the Slack app</h3>
          <div class="body">Go to <code>api.slack.com/apps</code> → <b>Create New App</b> → <b>From scratch</b>. Name it <i>VCL PMO Bot</i>. Pick the <i>Vimit Converters</i> workspace as the development workspace.</div>
        </div>
      </div>

      <div class="step">
        <div class="num"></div>
        <div>
          <h3>Add bot scopes</h3>
          <div class="body">In the app sidebar → <b>OAuth &amp; Permissions</b>. Under <i>Scopes → Bot Token Scopes</i> add both: <code>chat:write</code> (post the initial comment) and <code>files:write</code> (upload the PDF). Save.</div>
        </div>
      </div>

      <div class="step">
        <div class="num"></div>
        <div>
          <h3>Install + copy the token</h3>
          <div class="body">Top of the same page → <b>Install to Workspace</b> → <b>Allow</b>. Copy the <i>Bot User OAuth Token</i> — it starts with <code>xoxb-…</code> Keep it on screen.</div>
        </div>
      </div>

      <div class="step">
        <div class="num"></div>
        <div>
          <h3>Invite the bot to the channel</h3>
          <div class="body">In Slack, open <code>#ai-pmo-plans</code> and type: <code>/invite @VCL PMO Bot</code>. Confirm. The bot must be a channel member or <code>files.completeUploadExternal</code> returns <code>not_in_channel</code>.</div>
        </div>
      </div>

      <div class="step">
        <div class="num"></div>
        <div>
          <h3>Drop the token into Frappe Cloud site_config</h3>
          <div class="body">SSH to the Frappe Cloud bench shell (or use the Bench → Site → Site Config UI). Run:
            <span class="cmd">bench --site vimitconverters.frappe.cloud set-config pmo_slack_bot_token "xoxb-…"
bench --site vimitconverters.frappe.cloud set-config pmo_slack_plans_channel "C0B5DA141MM"</span>
            The second line is optional — the default already points to <code>#ai-pmo-plans</code>.</div>
        </div>
      </div>

    </div>

    <div class="troubleshoot">
      <h2>Verify + troubleshoot</h2>
      <p style="margin:4px 0 8px 0;font-size:10pt;">Open any plan in <code>/app/pmo</code> → click <b>Send PDF to Slack</b>. A green toast with a Slack permalink means it worked.</p>
      <table class="tbl">
        <thead><tr><th>Toast says</th><th>What it means / fix</th></tr></thead>
        <tbody>
          <tr><td><code>pmo_slack_bot_token not set</code></td><td>The site_config key is missing. Re-run step 5.</td></tr>
          <tr><td><code>Slack post failed: not_in_channel</code></td><td>Bot isn't a member of <code>#ai-pmo-plans</code>. Re-run step 4.</td></tr>
          <tr><td><code>Slack post failed: invalid_auth</code></td><td>Token was revoked or is the wrong type. Must be <code>xoxb-…</code> (Bot User), not <code>xoxp-…</code> (User).</td></tr>
          <tr><td><code>Slack post failed: getUploadURL</code></td><td>Network egress from Frappe Cloud is blocked, or <code>files:write</code> scope is missing. Re-check step 2.</td></tr>
        </tbody>
      </table>
    </div>

  </div>
  <div class="foot"><span>VCL PMO · Slack Bot Setup · v1 · 28 May 2026</span><img class="stamp-mini" src="data:image/png;base64,{STAMP}" alt="VCL"/></div>
</section>

</body></html>
"""

out = REPO / 'briefs/VCL-PMO_slack_bot_setup_card.html'
out.write_text(HTML)
print(f'wrote {out} ({len(HTML):,} bytes)')
