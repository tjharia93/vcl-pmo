# PMO → Slack Integration

Renders a `PMO Plan` as a VCL-branded A4 PDF (sized for Boox Air 5 / reMarkable) and
uploads it to the **#ai-pmo-plans** Slack channel.

Built for SHIFT-0003 / PLAN-0002.

## How it works

1. User clicks **Send PDF to Slack** on the Plan sub-page in `/app/pmo`.
2. `vcl_pmo_doctypes.api.send_plan_to_slack(plan_id)` builds an HTML
   document (`_vcl_brand_html`) with the VCL brand palette
   (blue `#1F4E79`, slate ink, white background), 14pt body for high-contrast
   e-ink reading, and an A4 page box.
3. `frappe.utils.pdf.get_pdf(html, options)` (wkhtmltopdf on Frappe Cloud)
   renders the bytes.
4. The PDF is uploaded to Slack via the modern external-upload flow:
   - `files.getUploadURLExternal` — request a one-shot upload URL
   - `POST upload_url` — push the bytes
   - `files.completeUploadExternal` — attach to the channel with an
     `initial_comment` linking back to `/app/pmo`
5. Response surfaces the file `permalink` in the success toast.

## Required `site_config.json` keys

```json
{
  "pmo_slack_bot_token":     "xoxb-...",        // bot token — chat:write + files:write
  "pmo_slack_plans_channel": "C0B5DA141MM"      // optional override; defaults to #ai-pmo-plans
}
```

Set these via the Frappe Cloud bench shell (Tanuj-owned):

```bash
bench --site vimitconverters.frappe.cloud set-config pmo_slack_bot_token "xoxb-XXXXX"
bench --site vimitconverters.frappe.cloud set-config pmo_slack_plans_channel "C0B5DA141MM"
```

## Slack app setup

Create a Slack app in the **Vimit Converters** workspace with these scopes
on the **Bot User**:

- `chat:write` — to post the initial comment
- `files:write` — to upload the PDF

Install the app to the workspace, copy the **Bot User OAuth Token** (starts
with `xoxb-`) into `pmo_slack_bot_token`, then invite the bot to
`#ai-pmo-plans` (`/invite @vcl-pmo-bot` or equivalent).

## Manual test (after deploy + token install)

1. Open https://vimitconverters.frappe.cloud/app/pmo, choose any project.
2. Plans tab → click any plan → **Send PDF to Slack**.
3. Confirm: success toast with link, file lands in `#ai-pmo-plans`,
   PDF opens cleanly on Boox / reMarkable / desktop.

## Failure modes

| Toast says | Likely cause |
|---|---|
| `pmo_slack_bot_token not set in site_config.json` | site_config key missing — install token |
| `Slack post failed: not_in_channel` | bot not invited to target channel |
| `Slack post failed: invalid_auth` | token revoked or wrong type (needs xoxb, not xoxp) |
| `Slack post failed: getUploadURL` | network egress blocked or scope missing |

## Future hooks (deferred)

- Auto-post when `PMO Plan.status` transitions Draft → Allocated
  (add `doc_events["PMO Plan"]["on_update"]` in `hooks.py`).
- Per-project channel routing (`PMO Project.slack_channel` field).
- Render Shifts and UAT/OAT Runs to the same channel with their own
  branded templates.
