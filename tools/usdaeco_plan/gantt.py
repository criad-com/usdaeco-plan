"""Small standalone SVG schedule drawn from composed activity prims."""
from datetime import date
from html import escape
from pathlib import Path
from .validation import activities, value, window


def draw(programme, output, label):
    epoch = date.fromisoformat(value(programme, "aeco:plan:epoch"))
    rows = sorted(activities(programme), key=lambda p: (window(p)[0], p.GetDisplayName()))
    width, left, top, row_height = 1200, 340, 110, 42
    height = top + len(rows) * row_height + 65
    day_width = (width - left - 40) / 84
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#101a2b"/>',
             '<g font-family="system-ui,sans-serif" fill="#e8edf4">',
             f'<text x="28" y="43" font-size="26" font-weight="700">Programme {escape(label)} · office fit-out</text>',
             '<text x="28" y="71" font-size="14" fill="#adbbcd">demo-datacentre-01 · illustrative dates · stored programme drivers</text>']
    for week in range(12):
        x = left + week * 7 * day_width
        lines.extend([f'<line x1="{x:.2f}" y1="94" x2="{x:.2f}" y2="{height-45}" stroke="#314056"/>',
                      f'<text x="{x+6:.2f}" y="99" font-size="12">W{week+1}</text>'])
    for i, prim in enumerate(rows):
        y = top + i * row_height
        start, finish = window(prim)
        x = left + (start - epoch).days * day_width
        span = max(day_width, ((finish - start).days + 1) * day_width)
        kind = value(prim, "aeco:plan:taskType")
        color = {'attendance': '#f6ca72', 'logistic': '#ee9869', 'removal': '#c3a7e8', 'construction': '#87aee8'}.get(kind, '#6fd1c0')
        lines.extend([f'<text x="28" y="{y+23}" font-size="14">{escape(prim.GetDisplayName())}</text>',
                      f'<rect x="{x:.2f}" y="{y+5}" width="{span:.2f}" height="25" rx="4" fill="{color}">',
                      f'<title>{escape(prim.GetDisplayName())}: {start} to {finish}</title></rect>'])
    lines.extend([f'<text x="28" y="{height-20}" font-size="12" fill="#adbbcd">Epoch {epoch} · 1 time code per calendar day · dependency lags retained; no CPM calculation</text>', '</g></svg>'])
    Path(output).write_text('\n'.join(lines) + '\n')
