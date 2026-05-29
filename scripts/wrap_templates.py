#!/usr/bin/env python3
"""Wrap legacy templates with the shared base template.

The script archives originals under archive/templates_pre_migration/ and converts
HTML templates that do not already extend base.html into content-only templates.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
ARCHIVE = ROOT / "archive" / "templates_pre_migration"
SKIP_NAMES = {"base.html"}
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
BODY_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.IGNORECASE | re.DOTALL)
SCRIPT_RE = re.compile(r"<script\b.*?</script>", re.IGNORECASE | re.DOTALL)


def clean_title(raw: str, fallback: str) -> str:
    text = re.sub(r"\s+", " ", raw).strip()
    return text or fallback


def strip_outer_html(source: str) -> tuple[str, str | None]:
    title_match = TITLE_RE.search(source)
    title = clean_title(title_match.group(1), "Urxion") if title_match else None
    body_match = BODY_RE.search(source)
    if body_match:
        body = body_match.group(1).strip()
    else:
        body = source.strip()
    body = re.sub(r"<!doctype[^>]*>", "", body, flags=re.IGNORECASE).strip()
    body = re.sub(r"</?html[^>]*>", "", body, flags=re.IGNORECASE).strip()
    body = re.sub(
        r"<head\b.*?</head>", "", body, flags=re.IGNORECASE | re.DOTALL
    ).strip()
    body = SCRIPT_RE.sub("", body).strip()
    return body, title


def wrap(path: Path) -> str:
    rel = path.relative_to(TEMPLATES)
    source = path.read_text(encoding="utf-8", errors="ignore")
    if "{% extends" in source or rel.name in SKIP_NAMES:
        return f"SKIP {rel}"

    archive_path = ARCHIVE / rel
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if not archive_path.exists():
        shutil.copy2(path, archive_path)

    body, title = strip_outer_html(source)
    if not body:
        body = '<section class="section"><div class="container"><p>Legacy page content is being updated.</p></div></section>'
    title = title or f"{path.stem} | Urxion"
    wrapped = (
        '{% extends "base.html" %}\n'
        f"{{% block title %}}{title}{{% endblock %}}\n"
        "{% block content %}\n"
        '<section class="section legacy-page">\n'
        '    <div class="container legacy-content">\n'
        f"{body}\n"
        "    </div>\n"
        "</section>\n"
        "{% endblock %}\n"
    )
    path.write_text(wrapped, encoding="utf-8")
    return f"WRAP {rel}"


def main() -> int:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    log_path = (
        ROOT
        / "archive"
        / f"template_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    results: list[str] = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        results.append(wrap(path))
    log_path.write_text("\n".join(results) + "\n", encoding="utf-8")
    for line in results:
        print(line)
    print(f"Log: {log_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
