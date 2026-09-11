"""Unified export service supporting TXT, JSON, CSV, HTML.

All data is real – whatever the caller passes in gets exported.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from io import StringIO
from pathlib import Path

from config.settings import REPORTS_DIR, EXPORT_FORMATS


def export_data(
    data: dict | list,
    filename_stem: str,
    fmt: str = "json",
    title: str = "",
) -> Path | None:
    """Export data to a file. Returns the path or None on error."""
    if fmt not in EXPORT_FORMATS:
        return None

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = REPORTS_DIR / f"{filename_stem}_{ts}.{fmt}"

    try:
        if fmt == "json":
            _write_json(data, filepath)
        elif fmt == "csv":
            _write_csv(data, filepath)
        elif fmt == "txt":
            _write_txt(data, filepath, title)
        elif fmt == "html":
            _write_html(data, filepath, title)
        return filepath
    except Exception:
        return None


def _write_json(data: dict | list, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _write_csv(data: dict | list, path: Path) -> None:
    rows = data if isinstance(data, list) else [data]
    if not rows:
        return
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _write_txt(data: dict | list, path: Path, title: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        if title:
            f.write(f"{'=' * 60}\n{title}\n{'=' * 60}\n\n")
        f.write(_format_data_txt(data, indent=0))


def _write_html(data: dict | list, path: Path, title: str) -> None:
    html = _build_html(data, title)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def _format_data_txt(data, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.append(_format_data_txt(v, indent + 1))
            else:
                lines.append(f"{pad}{k}: {v}")
        return "\n".join(lines)
    elif isinstance(data, list):
        lines = []
        for i, item in enumerate(data):
            if isinstance(item, dict):
                lines.append(f"{pad}[{i + 1}]:")
                lines.append(_format_data_txt(item, indent + 1))
            else:
                lines.append(f"{pad}- {item}")
        return "\n".join(lines)
    return str(data)


def _build_html(data, title: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = data if isinstance(data, list) else [data]
    headers = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
    table_rows = ""
    for r in rows:
        if isinstance(r, dict):
            cells = "".join(f"<td>{_esc(str(r.get(h, '')))}</td>" for h in headers)
            table_rows += f"<tr>{cells}</tr>"

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="utf-8"><title>{_esc(title)}</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#0d1321;color:#e2e8f0;padding:20px;}}
table{{border-collapse:collapse;width:100%;margin-top:20px;}}
th,td{{border:1px solid #1e293b;padding:8px 12px;text-align:right;}}
th{{background:#141b2d;color:#94a3b8;}}
h1{{color:#38bdf8;}}h2{{color:#e2e8f0;}}
</style></head>
<body><h1>{_esc(title)}</h1>
<p>Generated: {ts}</p>
<table><thead><tr>{''.join(f'<th>{_esc(h)}</th>' for h in headers)}</tr></thead>
<tbody>{table_rows}</tbody></table></body></html>"""


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
