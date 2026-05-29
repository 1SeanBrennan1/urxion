"""Export visible website wording into one Markdown document.

Run from the repo root:
    python scripts/export_site_wording.py

Output:
    articles/site_wording_export.md
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_resources import AGENT_RESOURCE_PAGES  # noqa: E402
from flask_app import app  # noqa: E402

OUTPUT_PATH = ROOT / "articles" / "site_wording_export.md"


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0
        self.block_tags = {
            "address",
            "article",
            "aside",
            "blockquote",
            "br",
            "dd",
            "div",
            "dl",
            "dt",
            "figcaption",
            "footer",
            "form",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "header",
            "hr",
            "li",
            "main",
            "nav",
            "ol",
            "p",
            "pre",
            "section",
            "table",
            "td",
            "th",
            "tr",
            "ul",
        }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")
        if tag == "input":
            attrs_dict = dict(attrs)
            placeholder = attrs_dict.get("placeholder")
            if placeholder:
                self.parts.append(f" {placeholder} ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        raw = " ".join(self.parts)
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        raw = re.sub(r" *\n *", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def visible_text(html: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html)
    return parser.text()


def public_paths() -> list[str]:
    ignored_endpoints = {
        "static",
        "robots_txt",
        "sitemap_xml",
        "slots",
        "book_meeting",
        "process_unsubscribe",
        "cold_calling_results",
        "serve_ms_identity",
        "serve_ms_identity2",
    }
    paths: set[str] = set()
    for rule in app.url_map.iter_rules():
        if rule.endpoint in ignored_endpoints:
            continue
        if "GET" not in (rule.methods or set()):
            continue
        if rule.arguments:
            continue
        if rule.rule.startswith("/.well-known"):
            continue
        paths.add(rule.rule)

    for page in AGENT_RESOURCE_PAGES:
        paths.add(f"/resources/ai-agent-engineering/{page['slug']}")

    return sorted(paths, key=lambda path: (path != "/", path))


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sections: list[str] = [
        "# URXION Website Wording Export",
        "",
        "Generated from rendered Flask pages. Script/style/svg content is excluded.",
        "",
    ]

    with app.test_client() as client:
        for path in public_paths():
            response = client.get(path)
            if response.status_code != 200:
                continue
            if not response.content_type.startswith("text/html"):
                continue
            text = visible_text(response.get_data(as_text=True))
            if not text:
                continue
            sections.extend([f"## {path}", "", text, ""])

    OUTPUT_PATH.write_text("\n".join(sections).strip() + "\n", encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
