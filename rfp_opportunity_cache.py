from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin

import requests

ROOT = Path(__file__).resolve().parent
CACHE_PATH = ROOT / "demo_runs" / "rfp_opportunities.json"
SEED_CACHE_PATH = ROOT / "articles" / "rfp_opportunities_seed.json"
CACHE_TTL = timedelta(hours=24)
USER_AGENT = "URXION-RFP-Demo/1.0 (+https://www.urxion.com)"

TEST_OPPORTUNITIES: list[dict[str, Any]] = [
    {
        "id": "sample-on-cloud-001",
        "title": "Cloud Migration and Modernization Services",
        "agency": "Ontario Ministry of Public and Business Service Delivery",
        "deadline": "2026-09-30",
        "estimated_value": "$5M - $10M",
        "summary": "Migration planning, application assessment, phased modernization, governance, reporting, and secure cloud transition support.",
        "requirements": [
            "Describe cloud migration methodology and delivery governance.",
            "Provide relevant public-sector project experience.",
            "Explain security, privacy, and risk controls.",
            "Submit project plan, pricing assumptions, and transition approach.",
        ],
        "source_name": "Test fixture public listing",
        "source_url": "https://www.ontario.ca/page/tenders-and-procurement",
        "source_status": "source_linked",
        "fetched_at": None,
    },
    {
        "id": "sample-on-data-002",
        "title": "Healthcare Data Analytics Platform",
        "agency": "Ontario Health / Ministry of Health",
        "deadline": "2026-10-15",
        "estimated_value": "$10M - $25M",
        "summary": "Analytics platform support for data ingestion, reporting, population health monitoring, and evidence-based decision workflows.",
        "requirements": [
            "Summarize data platform and analytics experience.",
            "Address privacy, security, and auditability.",
            "Provide implementation plan and support model.",
            "Identify evidence gaps before final submission.",
        ],
        "source_name": "Test fixture public listing",
        "source_url": "https://www.ontario.ca/page/tenders-and-procurement",
        "source_status": "source_linked",
        "fetched_at": None,
    },
    {
        "id": "sample-on-learning-003",
        "title": "Digital Learning Platform Modernization",
        "agency": "Ontario Ministry of Education",
        "deadline": "2026-12-01",
        "estimated_value": "$8M - $15M",
        "summary": "Modernization of digital learning workflows with accessibility, bilingual support, integrations, training, and reporting.",
        "requirements": [
            "Describe platform modernization approach.",
            "Explain accessibility and user-support controls.",
            "Provide delivery timeline and stakeholder plan.",
            "Map claims to evidence and flag unsupported statements.",
        ],
        "source_name": "Test fixture public listing",
        "source_url": "https://www.ontario.ca/page/tenders-and-procurement",
        "source_status": "source_linked",
        "fetched_at": None,
    },
    {
        "id": "sample-on-construction-004",
        "title": "Municipal Facility Renovation and Accessibility Upgrades",
        "agency": "Ontario municipal buyer",
        "deadline": "2026-08-20",
        "estimated_value": "$1M - $3M",
        "summary": "General contractor services for interior renovation, accessibility improvements, site safety, scheduling, subcontractor coordination, bonding, insurance, WSIB clearance, and closeout documentation.",
        "requirements": [
            "Provide construction project experience for occupied public facilities.",
            "Submit health and safety plan, WSIB clearance, insurance, and bonding evidence.",
            "Describe subcontractor management, schedule control, and deficiency closeout process.",
            "Provide references, pricing breakdown, and project delivery schedule.",
        ],
        "source_name": "Test fixture public listing",
        "source_url": "https://www.ontario.ca/page/tenders-and-procurement",
        "source_status": "source_linked",
        "fetched_at": None,
    },
    {
        "id": "sample-on-roadworks-005",
        "title": "Road Reconstruction, Drainage, and Concrete Works",
        "agency": "Ontario regional municipality",
        "deadline": "2026-07-18",
        "estimated_value": "$2M - $6M",
        "summary": "Civil construction for road resurfacing, stormwater drainage, concrete sidewalks, traffic control, environmental controls, equipment planning, and construction schedule management.",
        "requirements": [
            "Describe roadworks, drainage, asphalt, concrete, and traffic-control experience.",
            "Provide equipment list, staffing plan, safety procedures, and quality-control approach.",
            "Submit insurance, WSIB, bonding, environmental controls, and references.",
            "Explain schedule, phasing, public communication, and deficiency resolution.",
        ],
        "source_name": "Test fixture public listing",
        "source_url": "https://www.ontario.ca/page/tenders-and-procurement",
        "source_status": "source_linked",
        "fetched_at": None,
    },
]

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "your",
    "you",
    "our",
    "are",
    "was",
    "were",
    "can",
    "will",
    "public",
    "sector",
    "company",
    "services",
    "service",
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _strip_html(value: str) -> str:
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"&nbsp;", " ", value, flags=re.I)
    value = re.sub(r"&amp;", "&", value, flags=re.I)
    return " ".join(value.split())


def _keywords(text: str) -> list[str]:
    terms = re.findall(r"[a-z][a-z0-9-]{2,}", text.lower())
    result: list[str] = []
    for term in terms:
        if term in STOPWORDS or term in result:
            continue
        result.append(term)
        if len(result) >= 40:
            break
    return result


def _opportunity_id(source_name: str, source_url: str, title: str) -> str:
    digest = hashlib.sha1(
        f"{source_name}|{source_url}|{title}".encode("utf-8")
    ).hexdigest()[:12]
    return f"src-{digest}"


def _requirements_from_text(title: str, summary: str) -> list[str]:
    text = f"{title} {summary}".lower()
    requirements = [
        "Summarize relevant experience and delivery approach.",
        "Provide implementation plan, governance, timeline, and support model.",
        "Map claims to supplied evidence and flag unsupported statements.",
        "Confirm pricing, legal, and submission requirements before final approval.",
    ]
    if any(term in text for term in ("security", "privacy", "data", "cloud", "cyber")):
        requirements.insert(
            2, "Address security, privacy, data handling, and risk controls."
        )
    if any(term in text for term in ("accessibility", "aoda", "learning", "student")):
        requirements.insert(
            2, "Describe accessibility, user support, and adoption controls."
        )
    return requirements[:5]


def _normalize(
    *,
    source_name: str,
    source_url: str,
    title: str,
    agency: str = "See source posting",
    deadline: str = "See source posting",
    estimated_value: str = "See source posting",
    summary: str = "See source posting for details.",
    source_status: str = "source_linked",
    fetched_at: str | None = None,
) -> dict[str, Any]:
    title = _strip_html(title)[:220] or "Untitled opportunity"
    summary = _strip_html(summary)[:1200] or "See source posting for details."
    source_url = source_url.strip()
    return {
        "id": _opportunity_id(source_name, source_url, title),
        "title": title,
        "agency": _strip_html(agency)[:180] or "See source posting",
        "deadline": _strip_html(deadline)[:80] or "See source posting",
        "estimated_value": _strip_html(estimated_value)[:80] or "See source posting",
        "summary": summary,
        "requirements": _requirements_from_text(title, summary),
        "source_name": source_name,
        "source_url": source_url,
        "source_status": source_status,
        "fetched_at": fetched_at or _now_iso(),
    }


def _fetch_canadabuys() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    urls = [
        "https://canadabuys.canada.ca/en/tender-opportunities?items_per_page=100",
        "https://canadabuys.canada.ca/en/tender-opportunities?items_per_page=100&sort_by=field_tender_closing_date",
    ]
    queries = (
        "construction",
        "renovation",
        "building",
        "road",
        "concrete",
        "software",
        "cloud",
        "data",
        "cleaning",
        "consulting",
        "security",
        "maintenance",
    )
    urls.extend(
        f"https://canadabuys.canada.ca/en/tender-opportunities?search_api_fulltext={quote_plus(query)}&items_per_page=100"
        for query in queries
    )
    for listing_url in urls:
        try:
            resp = requests.get(listing_url, headers={"User-Agent": USER_AGENT}, timeout=20)
            resp.raise_for_status()
        except Exception:
            continue

        anchors = re.findall(r'href="([^"]*?/en/tender-opportunities/tender-notice/[^"]+)"[^>]*>(.*?)</a>', resp.text, re.S | re.I)
        for href, label_html in anchors:
            title = _strip_html(label_html)
            if not title or len(title) < 8 or title.lower() in seen:
                continue
            source_url = href if href.startswith("http") else urljoin("https://canadabuys.canada.ca", href)
            seen.add(title.lower())
            results.append(
                _normalize(
                    source_name="CanadaBuys",
                    source_url=source_url,
                    title=title,
                    agency="CanadaBuys tendering organization",
                    summary=f"CanadaBuys public tender notice for {title}. Open the source posting for official scope, deadlines, amendments, attachments, and submission details.",
                    source_status="source_linked",
                )
            )
            if len(results) >= 150:
                return results
    return results


def _fetch_merx() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in ("software", "cloud", "data", "digital transformation", "construction", "renovation", "road", "concrete", "cleaning", "security", "consulting"):
        url = f"https://www.merx.com/public/solicitations/open?keywords={quote_plus(query)}"
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
            resp.raise_for_status()
        except Exception:
            continue
        titles = re.findall(
            r'<a[^>]+href="([^"]+)"[^>]*>([^<]{12,220})</a>', resp.text, re.I
        )
        for href, label in titles:
            title = _strip_html(label)
            if not title or title.lower() in seen:
                continue
            if not any(
                term in title.lower()
                for term in (
                    "software",
                    "cloud",
                    "data",
                    "digital",
                    "platform",
                    "system",
                    "construction",
                    "renovation",
                    "road",
                    "concrete",
                    "cleaning",
                    "janitorial",
                    "security",
                    "consulting",
                    "maintenance",
                    "facility",
                )
            ):
                continue
            source_url = (
                href
                if href.startswith("http")
                else urljoin("https://www.merx.com", href)
            )
            seen.add(title.lower())
            results.append(
                _normalize(
                    source_name="MERX public solicitations",
                    source_url=source_url,
                    title=title,
                    agency="MERX posting organization",
                    summary=f"MERX public solicitation matching {query}. Open the source posting for official requirements and submission details.",
                    source_status="source_linked",
                )
            )
            if len(results) >= 20:
                return results
    return results


def refresh_opportunity_cache() -> dict[str, Any]:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    opportunities: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for fetcher in (_fetch_canadabuys, _fetch_merx):
        for opportunity in fetcher():
            source_url = opportunity.get("source_url") or ""
            if not source_url or source_url in seen_urls:
                continue
            seen_urls.add(source_url)
            opportunities.append(opportunity)
    payload = {
        "version": 1,
        "fetched_at": _now_iso(),
        "count": len(opportunities),
        "opportunities": opportunities,
    }
    CACHE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_opportunity_cache(*, refresh_if_stale: bool = True) -> dict[str, Any]:
    if CACHE_PATH.exists():
        try:
            payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            fetched_at = payload.get("fetched_at")
            if not refresh_if_stale or not fetched_at:
                return payload
            age = datetime.now(UTC) - datetime.fromisoformat(fetched_at)
            if age < CACHE_TTL:
                return payload
        except Exception:
            pass
    if refresh_if_stale:
        try:
            refreshed = refresh_opportunity_cache()
            if refreshed.get("opportunities"):
                return refreshed
        except Exception:
            pass
    if SEED_CACHE_PATH.exists():
        try:
            seed = json.loads(SEED_CACHE_PATH.read_text(encoding="utf-8"))
            if seed.get("opportunities"):
                return {**seed, "seeded": True}
        except Exception:
            pass
    return {"version": 1, "fetched_at": None, "count": 0, "opportunities": []}


def _score(opportunity: dict[str, Any], company_info: str) -> tuple[int, list[str]]:
    company_terms = set(_keywords(company_info))
    opp_text = " ".join(
        str(opportunity.get(key, ""))
        for key in ("title", "agency", "summary", "requirements")
    ).lower()
    opp_terms = set(_keywords(opp_text))
    overlap = sorted(company_terms & opp_terms)
    score = len(overlap) * 8
    priority_terms = {
        "ai",
        "automation",
        "workflow",
        "document",
        "data",
        "cloud",
        "software",
        "platform",
        "python",
        "flask",
        "compliance",
        "construction",
        "contractor",
        "renovation",
        "building",
        "facility",
        "facilities",
        "road",
        "roads",
        "asphalt",
        "concrete",
        "drainage",
        "civil",
        "wsib",
        "insurance",
        "bonding",
        "safety",
        "janitorial",
        "cleaning",
    }
    domain_groups = {
        "construction": {
            "construction",
            "contractor",
            "renovation",
            "building",
            "facility",
            "facilities",
            "subcontractor",
            "site",
            "safety",
            "wsib",
            "insurance",
            "bonding",
        },
        "civil roadworks": {
            "road",
            "roads",
            "roadworks",
            "asphalt",
            "concrete",
            "drainage",
            "stormwater",
            "traffic",
            "civil",
        },
        "technology": {
            "ai",
            "automation",
            "workflow",
            "document",
            "data",
            "cloud",
            "software",
            "platform",
            "python",
            "flask",
            "cyber",
        },
        "facility services": {
            "janitorial",
            "cleaning",
            "custodial",
            "facility",
            "facilities",
        },
    }
    priority_overlap = sorted((company_terms & priority_terms) & opp_terms)
    score += len(priority_overlap) * 12
    domain_reasons = []
    for label, terms in domain_groups.items():
        domain_overlap = sorted((company_terms & terms) & opp_terms)
        if domain_overlap:
            score += len(domain_overlap) * 18
            domain_reasons.append(
                f"Domain fit ({label}): {', '.join(domain_overlap[:3])}"
            )
    if opportunity.get("source_status") == "source_linked" and score > 0:
        score += 10
    reasons = domain_reasons + [
        f"Keyword match: {term}" for term in (priority_overlap or overlap)[:4]
    ]
    if not reasons:
        reasons = ["No strong keyword match. Add more company details or paste the full RFP for a better recommendation."]
    return score, reasons[:5]


def ranked_opportunities(
    company_info: str, *, testing: bool = False, limit: int = 6
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if testing:
        payload = {
            "version": 1,
            "fetched_at": None,
            "count": len(TEST_OPPORTUNITIES),
            "opportunities": TEST_OPPORTUNITIES,
            "mode": "test_source_linked_fixtures",
        }
    else:
        payload = load_opportunity_cache(refresh_if_stale=True)
        opportunities = [
            opportunity
            for opportunity in payload.get("opportunities", [])
            if opportunity.get("source_status") == "source_linked" and opportunity.get("source_url")
        ]
        payload = {**payload, "opportunities": opportunities, "count": len(opportunities), "mode": "real_cached_public_listings"}

    company_terms = set(_keywords(company_info))
    limited_context = len(company_terms) < 4
    ranked = []
    for opportunity in payload.get("opportunities", []):
        item = dict(opportunity)
        score, reasons = _score(item, company_info)
        item["fit_score"] = score
        if score >= 80:
            item["fit_confidence"] = "strong"
        elif score >= 30:
            item["fit_confidence"] = "possible"
        else:
            item["fit_confidence"] = "weak"
        item["match_reasons"] = reasons
        ranked.append(item)
    ranked.sort(key=lambda item: item.get("fit_score", 0), reverse=True)

    if not ranked:
        guidance = "The real public opportunity cache is empty. Refresh the cache or paste an RFP to generate from your own source material."
    elif limited_context:
        guidance = "Only a few keywords were supplied. These are real cached public listings, but some may be low-confidence because URXION needs more company detail to rank them well."
    else:
        guidance = "Recommendations are based on real cached public listings and the company context supplied. Low-confidence listings are still real opportunities; paste the full RFP before generating for the best demo."

    meta = {
        **payload,
        "limited_context": limited_context,
        "context_terms_count": len(company_terms),
        "guidance": guidance,
    }
    return ranked[:limit], meta
