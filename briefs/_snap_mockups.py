#!/usr/bin/env python3
"""Snapshot the two mockup HTML files to PNG at 1280x900 viewport."""
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path('/home/tanujharia/projects/vcl-pmo')
OUT = REPO / 'briefs/screenshots'
OUT.mkdir(parents=True, exist_ok=True)

targets = [
    ('mix-a', REPO / 'mockups/mix-a.html'),
    ('mix-c', REPO / 'mockups/mix-c.html'),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900}, device_scale_factor=2)
    for name, html in targets:
        page = ctx.new_page()
        page.goto(f'file://{html}', wait_until='networkidle')
        page.wait_for_timeout(800)  # let any JS settle
        out = OUT / f'{name}.png'
        page.screenshot(path=str(out), full_page=True)
        print(f'{name}: {out} ({out.stat().st_size:,} bytes)')
        page.close()
    browser.close()
