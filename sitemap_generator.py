#!/usr/bin/env python3
"""
Generate sitemap.xml for urxion.com including:
- Core pages
- AI agent engineering resource pages
- All old sales book summary blog pages (86+ files)
"""

import os
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom

# Configuration
BASE_URL = "https://www.urxion.com"
BLOG_DIR = Path(__file__).parent / "templates" / "blog"
OUTPUT_FILE = Path(__file__).parent / "sitemap.xml"

# Core pages (from your existing sitemap)
CORE_PAGES = [
    "/",
    "/why-urxion",
    "/rfp",
    "/compliance",
    "/sdr",
    "/custom-agents",
    "/data-security",
    "/sample-outputs",
    "/demo-vs-production",
    "/resources/founder-led-workflow-pilot",
    "/resources/rfp-intake-checklist",
    "/resources/compliance-package-checklist",
    "/demo",
    "/try-rfp",
    "/try-compliance",
    "/contact",
    "/privacy",
    "/terms",
]

# AI agent engineering resource slugs (from your sitemap)
RESOURCE_SLUGS = [
    "system-not-the-model",
    "grounding-beats-guessing",
    "prompts-do-not-enforce-safety",
    "minimum-viable-agent",
    "ai-agent-memory-state-design",
    "source-linked-agent-memory",
    "agent-retrieval-precision",
    "multi-agent-orchestration",
    "document-worker-agents",
    "agent-evaluation-trajectory-testing",
    "agent-regression-testing",
    "llm-judge-calibration",
    "cost-aware-model-routing",
    "when-to-use-bigger-model",
    "agent-observability-traces",
    "human-in-the-loop-agent-design",
    "approval-workflows-for-agents",
    "tool-use-governance",
    "rag-security-prompt-injection",
    "agent-pr-review-checklist",
]

def get_blog_routes():
    """Scan templates/blog/ for all .html files and return /blog/... routes."""
    if not BLOG_DIR.exists():
        print(f"Warning: Blog directory not found at {BLOG_DIR}")
        return []
    routes = []
    for file_path in BLOG_DIR.glob("*.html"):
        # Remove .html extension
        slug = file_path.stem
        routes.append(f"/blog/{slug}")
    return sorted(routes)

def generate_sitemap():
    """Create the sitemap.xml file."""
    # Collect all URLs
    urls = []
    urls.extend(CORE_PAGES)
    urls.extend([f"/resources/ai-agent-engineering/{slug}" for slug in RESOURCE_SLUGS])
    urls.extend(get_blog_routes())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    # Build XML
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in unique_urls:
        url_elem = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url_elem, "loc")
        loc.text = f"{BASE_URL}{url}"
        # Optional: add lastmod, changefreq, priority here if desired
    
    # Pretty print
    rough_string = ET.tostring(urlset, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    
    # Remove the XML declaration if Flask's route will add its own? Keep it; it's fine.
    # Write to file
    OUTPUT_FILE.write_text(pretty_xml, encoding="utf-8")
    
    print(f"Sitemap generated with {len(unique_urls)} URLs.")
    print(f"Blog pages included: {len(get_blog_routes())}")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_sitemap()