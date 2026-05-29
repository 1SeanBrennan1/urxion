from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

CONTENT_DIR = Path(__file__).resolve().parent / "content" / "ai-agent-engineering"


def slugify_heading(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def extract_toc(body: str) -> list[dict[str, str]]:
    headings = []
    for line in body.splitlines():
        if not line.startswith("## ") or line.startswith("### "):
            continue
        title = line.replace("## ", "", 1).strip()
        if title and title.lower() not in {"faq"}:
            headings.append({"title": title, "id": slugify_heading(title)})
    return headings


def _load_markdown_resource(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"Missing JSON frontmatter in {path}")
    _start, rest = raw.split("---\n", 1)
    frontmatter_raw, body = rest.split("\n---\n", 1)
    data = json.loads(frontmatter_raw)
    data["body"] = body.strip()
    data["toc"] = extract_toc(data["body"])
    return data


def load_agent_resource_pages() -> list[dict[str, Any]]:
    pages = [_load_markdown_resource(path) for path in CONTENT_DIR.glob("*.md")]
    return sorted(pages, key=lambda page: (page.get("order", 999), page["slug"]))


AGENT_RESOURCE_PAGES = load_agent_resource_pages()
AGENT_RESOURCE_BY_SLUG = {page["slug"]: page for page in AGENT_RESOURCE_PAGES}


def agent_resource_sources() -> list[dict[str, Any]]:
    usage: dict[str, dict[str, Any]] = {}
    page_map: dict[str, set[str]] = defaultdict(set)
    notes: dict[str, set[str]] = defaultdict(set)
    for page in AGENT_RESOURCE_PAGES:
        for source, note in page.get("sources", []):
            usage.setdefault(
                source,
                {
                    "source": source,
                    "url": f"https://arxiv.org/abs/{source}",
                    "title": f"arXiv:{source}",
                    "link_status": "linked",
                    "support_level": "conceptual reference",
                },
            )
            page_map[source].add(page["slug"])
            notes[source].add(note)
    rows = []
    for source in sorted(usage):
        rows.append(
            {
                **usage[source],
                "notes": sorted(notes[source]),
                "pages": sorted(page_map[source]),
            }
        )
    return rows


AGENT_RESOURCE_SOURCES = agent_resource_sources()
