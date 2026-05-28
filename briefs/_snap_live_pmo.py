#!/usr/bin/env python3
"""Capture deployed /app/pmo screenshots — proper selectors this time."""
from pathlib import Path
from playwright.sync_api import sync_playwright

env = {}
for line in open('/opt/vcl/config/.env'):
    if '=' in line and not line.strip().startswith('#'):
        k, _, v = line.strip().partition('=')
        env[k] = v
KEY, SECRET, URL = env['ERPNEXT_API_KEY'], env['ERPNEXT_API_SECRET'], env['ERPNEXT_URL']

REPO = Path('/home/tanujharia/projects/vcl-pmo')
OUT = REPO / 'briefs/screenshots'

def snap(page, name):
    out = OUT / f'{name}.png'
    page.screenshot(path=str(out), full_page=True)
    print(f'{name}: {out.stat().st_size:,} bytes')

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(
        viewport={'width': 1440, 'height': 900},
        device_scale_factor=2,
        extra_http_headers={'Authorization': f'token {KEY}:{SECRET}'},
    )
    page = ctx.new_page()
    page.goto(f'{URL}/app/pmo', wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(2500)
    snap(page, 'pmo-deployed-inbox')

    # Projects tab
    page.locator('button[data-view="projects"]').click()
    page.wait_for_timeout(1500)
    snap(page, 'pmo-deployed-projects')

    # Click VCL PMO System project card
    try:
        # Try various selectors
        clicked = page.evaluate('''() => {
          const cards = document.querySelectorAll('[data-project]');
          for (const c of cards) {
            if (c.innerText.includes('VCL-DEV-PMO-002') || c.innerText.includes('VCL PMO System')) {
              c.click(); return true;
            }
          }
          return false;
        }''')
        print('project clicked:', clicked)
        page.wait_for_timeout(2000)
        snap(page, 'pmo-deployed-project-overview')
    except Exception as e:
        print('project click error:', e)

    # Plans sub-tab
    try:
        page.locator('button[data-subtab="plans"]').click()
        page.wait_for_timeout(1500)
        snap(page, 'pmo-deployed-plans-tab')
    except Exception as e:
        print('plans sub-tab error:', e)

    # Click PLAN-0002 row (Slack Integration)
    try:
        clicked = page.evaluate('''() => {
          const rows = document.querySelectorAll('[data-plan]');
          for (const r of rows) {
            if (r.innerText.includes('Slack Integration') || r.innerText.includes('PLAN-0002')) {
              r.click(); return true;
            }
          }
          return false;
        }''')
        print('plan clicked:', clicked)
        page.wait_for_timeout(2000)
        snap(page, 'pmo-deployed-plan-detail')
    except Exception as e:
        print('plan detail error:', e)

    # Shifts tab
    try:
        page.go_back()
        page.wait_for_timeout(800)
        page.locator('button[data-subtab="shifts"]').click()
        page.wait_for_timeout(1500)
        snap(page, 'pmo-deployed-shifts-tab')
    except Exception as e:
        print('shifts tab error:', e)

    browser.close()
