from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTENT_DIR = Path(__file__).resolve().parent / "content" / "ai-agent-engineering"


def _load_markdown_resource(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"Missing JSON frontmatter in {path}")
    _start, rest = raw.split("---\n", 1)
    frontmatter_raw, body = rest.split("\n---\n", 1)
    data = json.loads(frontmatter_raw)
    data["body"] = body.strip()
    return data


def load_agent_resource_pages() -> list[dict[str, Any]]:
    pages = [_load_markdown_resource(path) for path in CONTENT_DIR.glob("*.md")]
    return sorted(pages, key=lambda page: (page.get("order", 999), page["slug"]))


AGENT_RESOURCE_PAGES = load_agent_resource_pages()
AGENT_RESOURCE_BY_SLUG = {page["slug"]: page for page in AGENT_RESOURCE_PAGES}
