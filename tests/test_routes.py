import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from agent_resources import AGENT_RESOURCE_PAGES
from flask_app import app

PUBLIC_GET_ROUTES = [
    "/",
    "/defaultsite",
    "/why-urxion",
    "/rfp",
    "/compliance",
    "/sdr",
    "/athena-rfp",
    "/athena-compliance",
    "/athena-sdr",
    "/custom-agents",
    "/data-security",
    "/sample-outputs",
    "/demo-vs-production",
    "/resources/ai-agent-engineering",
    "/cold-calling-that-converts",
    "/business-assessment",
    "/cold-calling-assessment",
    "/sales-assessment",
    "/Knowledge-is-Power",
    "/demo",
    "/try-rfp",
    "/try-compliance",
    "/contact",
    "/privacy",
    "/terms",
    "/unsubscribe",
    "/blog/challenger",
    "/blog/sell",
    "/blog/cold_to_committed",
    "/blog/hacking_sales",
    "/blog/sales_eq",
    "/blog/break-even-point",
    "/robots.txt",
    "/sitemap.xml",
]


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def visible_text(body):
    return " ".join(body.split())


class FakeLLMResponse:
    def __init__(self, content, status_error=None):
        self.content = content
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


def test_llm_json_completion_uses_cerebras_before_groq(monkeypatch):
    import flask_app

    calls = []
    monkeypatch.setenv("CEREBRAS_API_KEY", "cerebras-key")
    monkeypatch.setenv("CEREBRAS_MODEL", "llama-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def fake_post(url, **kwargs):
        calls.append((url, kwargs["json"]["model"]))
        return FakeLLMResponse('{"ok": true}')

    monkeypatch.setattr(flask_app.requests, "post", fake_post)
    payload, model = flask_app._llm_json_completion("system", "user", temperature=0.1)
    assert payload == {"ok": True}
    assert model == "cerebras:llama-test"
    assert calls == [("https://api.cerebras.ai/v1/chat/completions", "llama-test")]


def test_llm_json_completion_falls_back_to_groq(monkeypatch):
    import flask_app

    calls = []
    monkeypatch.setenv("CEREBRAS_API_KEY", "cerebras-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def fake_post(url, **kwargs):
        calls.append((url, kwargs["json"]["model"]))
        if "cerebras" in url:
            raise RuntimeError("cerebras unavailable")
        return FakeLLMResponse('{"ok": true}')

    monkeypatch.setattr(flask_app.requests, "post", fake_post)
    payload, model = flask_app._llm_json_completion("system", "user", temperature=0.1)
    assert payload == {"ok": True}
    assert model == "groq:openai/gpt-oss-120b"
    assert calls[0][0] == "https://api.cerebras.ai/v1/chat/completions"
    assert calls[1] == (
        "https://api.groq.com/openai/v1/chat/completions",
        "openai/gpt-oss-120b",
    )


def test_llm_json_completion_falls_back_to_deepseek(monkeypatch):
    import flask_app

    calls = []
    monkeypatch.setenv("CEREBRAS_API_KEY", "cerebras-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")

    def fake_post(url, **kwargs):
        calls.append((url, kwargs["json"]["model"]))
        if "deepseek" not in url:
            raise RuntimeError("provider unavailable")
        return FakeLLMResponse('{"ok": true}')

    monkeypatch.setattr(flask_app.requests, "post", fake_post)
    payload, model = flask_app._llm_json_completion("system", "user", temperature=0.1)
    assert payload == {"ok": True}
    assert model == "deepseek:deepseek-chat"
    assert calls[0][0] == "https://api.cerebras.ai/v1/chat/completions"
    assert calls[1][0] == "https://api.groq.com/openai/v1/chat/completions"
    assert calls[2] == ("https://api.deepseek.com/chat/completions", "deepseek-chat")


@pytest.mark.parametrize("path", PUBLIC_GET_ROUTES)
def test_public_routes_render(client, path):
    response = client.get(path)
    assert response.status_code in {200, 301, 302}


@pytest.mark.parametrize("path", PUBLIC_GET_ROUTES)
def test_public_html_routes_get_global_contrast_fix(client, path):
    response = client.get(path)
    if response.status_code != 200 or not response.content_type.startswith("text/html"):
        return
    body = response.get_data(as_text=True)
    assert "urxion-global-contrast-fix" in body
    assert "body :where(h1, h2, h3, h4, h5, h6" in body
    assert "color: #0f172a !important" in body
    assert "body :where(p, li, dd, dt" in body
    assert "color: #334155 !important" in body


def test_sitemap_uses_canonical_https_domain(client):
    response = client.get("/sitemap.xml")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.content_type.startswith("application/xml")
    assert "https://www.urxion.com" in body
    assert "https://www.urxion.com/why-urxion" in body
    assert "https://www.urxion.com/rfp" in body
    assert "https://www.urxion.com/compliance" in body
    assert "https://www.urxion.com/sdr" in body
    assert "https://www.urxion.com/custom-agents" in body
    assert "https://www.urxion.com/data-security" in body
    assert "https://www.urxion.com/sample-outputs" in body
    assert "https://www.urxion.com/demo-vs-production" in body
    assert "https://www.urxion.com/resources/ai-agent-engineering" in body
    assert "https://www.urxion.com/resources/ai-agent-engineering/sources" in body
    assert (
        "https://www.urxion.com/resources/ai-agent-engineering/system-not-the-model"
        in body
    )
    assert "yourdomain.com" not in body
    assert "pythonanywhere" not in body


def test_agent_engineering_resource_hub_and_articles_render(client):
    hub_response = client.get("/resources/ai-agent-engineering")
    hub_body = hub_response.get_data(as_text=True)
    assert hub_response.status_code == 200
    assert "20 practical guides for production AI agents" in hub_body
    assert "Reliable AI agents are governed systems" in hub_body

    sources_response = client.get("/resources/ai-agent-engineering/sources")
    sources_body = sources_response.get_data(as_text=True)
    assert sources_response.status_code == 200
    assert "AI Agent Engineering source references" in sources_body
    assert "arXiv:" in sources_body

    content_dir = (
        Path(__file__).resolve().parents[1] / "content" / "ai-agent-engineering"
    )
    markdown_files = sorted(content_dir.glob("*.md"))
    assert len(AGENT_RESOURCE_PAGES) == 20
    assert len(markdown_files) == 20
    assert (content_dir / "system-not-the-model.md").exists()
    for page in AGENT_RESOURCE_PAGES:
        response = client.get(f"/resources/ai-agent-engineering/{page['slug']}")
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert page["h1"] in body
        assert "Research references" in body
        assert "https://arxiv.org/abs/" in body
        assert "FAQPage" in body
        assert f"By {page['author']}" in body
        assert f"Updated {page['updated']}" in body
        assert "Table of contents" in body
        for source, _note in page["sources"]:
            assert f"https://arxiv.org/abs/{source}" in body


def test_agent_engineering_markdown_pages_are_unique_and_deep():
    content_dir = (
        Path(__file__).resolve().parents[1] / "content" / "ai-agent-engineering"
    )
    framework_first_items = set()
    failure_first_items = set()
    checklist_first_items = set()
    for page in AGENT_RESOURCE_PAGES:
        path = content_dir / f"{page['slug']}.md"
        raw = path.read_text(encoding="utf-8")
        body = raw.split("\n---\n", 1)[1]
        assert len(body.split()) >= 600
        assert len(page["description"]) <= 160
        assert page["description"].endswith(".")
        assert "is part of a practical engineering framework" not in page["definition"]
        assert page["related"]
        for related_slug in page["related"]:
            assert related_slug in {item["slug"] for item in AGENT_RESOURCE_PAGES}
        framework_first_items.add(page["framework"][0])
        failure_first_items.add(page["failure_modes"][0])
        checklist_first_items.add(page["checklist"][0])
    assert len(framework_first_items) == len(AGENT_RESOURCE_PAGES)
    assert len(failure_first_items) == len(AGENT_RESOURCE_PAGES)
    assert len(checklist_first_items) == len(AGENT_RESOURCE_PAGES)


@pytest.mark.parametrize(
    "path",
    [
        "/DispatchAI",
        "/lastcall",
        "/business-assessment",
        "/cold-calling-assessment",
        "/sales-assessment",
        "/Knowledge-is-Power",
        "/blog/challenger",
        "/blog/break-even-point",
        "/unsubscribe",
    ],
)
def test_legacy_hidden_pages_are_noindexed_but_followed(client, path):
    response = client.get(path)
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert '<meta name="robots" content="noindex, follow"' in body


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/rfp",
        "/compliance",
        "/sdr",
        "/custom-agents",
        "/data-security",
        "/sample-outputs",
        "/resources/ai-agent-engineering",
        "/resources/ai-agent-engineering/system-not-the-model",
    ],
)
def test_current_public_pages_are_indexable(client, path):
    response = client.get(path)
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'name="robots" content="noindex' not in body


def test_robots_points_to_sitemap(client):
    response = client.get("/robots.txt")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Sitemap: https://www.urxion.com/sitemap.xml" in body


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/rfp", "Turn a Dense RFP Into a Review-Ready Proposal Package"),
        ("/compliance", "Every Subcontractor Package, Reviewed Before Day One"),
        ("/sdr", "Research the Account. Review the Message. Then Send"),
        ("/custom-agents", "Build the agent your workflow actually needs"),
    ],
)
def test_new_product_pages_render_conversion_copy(client, path, expected):
    response = client.get(path)
    body = response.get_data(as_text=True)
    text = visible_text(body)
    assert response.status_code == 200
    assert expected in text
    assert (
        "Book a call" in body
        or "Schedule My Free" in body
        or "Book a discovery call" in body
    )
    assert "URXION" in body
    assert "Athena" not in body


def test_homepage_has_diagnostic_headline_and_first_person_founder_copy(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert (
        "Review-ready RFP, compliance, and SDR work - without the back-office drag"
        in body
    )
    assert "I built URXION after 20 years across sales, operations" in body
    assert "View sample outputs" in body
    assert "SME pilot packages" in body
    assert "without a back-office department" in body
    assert "Not for unsupervised automation" in body
    assert "Founder-Led Workflow Pilot" in body
    assert "What happens on the call" in body
    assert "SME FAQ" in body


def test_homepage_product_cards_do_not_show_placeholder_letters(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert '<div class="icon">R</div>' not in body
    assert '<div class="icon">C</div>' not in body
    assert '<div class="icon">S</div>' not in body
    assert '<div class="icon">+</div>' not in body


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/rfp", "Your first RFP pilot includes"),
        ("/compliance", "Your first compliance pilot includes"),
        ("/sdr", "Your first SDR pilot includes"),
        ("/custom-agents", "Your first custom-agent pilot includes"),
    ],
)
def test_product_pages_explain_sme_pilot_packages(client, path, expected):
    response = client.get(path)
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert expected in body
    assert "Best fit" in body
    assert "Typical" in body
    assert "What to send us" in body
    assert "What happens before a pilot" in body


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (
            "/rfp",
            "Try It Free - See a Real Proposal",
        ),
        (
            "/compliance",
            "Try It Free - See a Real Compliance Review",
        ),
    ],
)
def test_demo_links_are_on_product_pages(client, path, expected):
    response = client.get(path)
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert expected in visible_text(body)


def test_demo_vs_production_page_renders(client):
    response = client.get("/demo-vs-production")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "What the public demo shows, and what production adds" in body
    assert "Public demo" in body
    assert "Production URXION" in body


def test_try_demo_routes_render(client):
    rfp_response = client.get("/try-rfp")
    rfp_body = rfp_response.get_data(as_text=True)
    assert rfp_response.status_code == 200
    assert "URXION RFP demo" in rfp_body
    assert "Find Real Cached RFPs" in rfp_body
    assert "No fake RFP opportunities" in rfp_body
    assert "Cerebras first, then Groq" in rfp_body
    assert "not the production URXION configuration" in visible_text(rfp_body)
    assert 'name="rfp_text"' not in rfp_body
    assert "Use construction example" in rfp_body

    compliance_response = client.get("/try-compliance")
    compliance_body = compliance_response.get_data(as_text=True)
    assert compliance_response.status_code == 200
    assert "URXION Compliance demo" in compliance_body
    assert "Run Compliance Demo" in compliance_body
    assert "Use built-in sample subcontractor package" in compliance_body
    assert "PDF and DOCX text extraction is limited" in compliance_body


def test_try_compliance_public_demo_can_run_and_download(client):
    response = client.post(
        "/try-compliance",
        data={
            "email": "demo@example.com",
            "subcontractor_name": "Demo Roofing Ltd.",
            "project_name": "Main Street Renovation",
            "project_location": "Toronto, Ontario",
            "planned_start_date": "2026-01-15",
            "work_type": "roofing",
            "documents": (
                BytesIO(
                    b"WSIB clearance expired. Insurance certificate name mismatch. No training records attached."
                ),
                "package.txt",
            ),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code == 302
    results_path = response.headers["Location"]

    results_response = client.get(results_path)
    results_body = results_response.get_data(as_text=True)
    assert results_response.status_code == 200
    assert "Your Compliance Review Packet Is Ready" in results_body
    assert "Generated by:" not in results_body
    assert "groq:" not in results_body.lower()
    assert "cerebras:" not in results_body.lower()
    assert "deepseek:" not in results_body.lower()
    assert "Expired" in results_body or "expired" in results_body
    assert "Download Compliance Packet" in results_body

    run_id = results_path.rstrip("/").split("/")[-1]
    download_response = client.get(f"/try-compliance/download/{run_id}")
    assert download_response.status_code == 200
    assert download_response.content_type == "application/zip"


def test_try_compliance_public_demo_can_run_with_sample_package(client):
    response = client.post(
        "/try-compliance",
        data={
            "email": "demo@example.com",
            "subcontractor_name": "Demo Roofing Ltd.",
            "project_name": "Main Street Renovation",
            "project_location": "Toronto, Ontario",
            "planned_start_date": "2026-01-15",
            "work_type": "roofing",
            "use_sample_package": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    results_response = client.get(response.headers["Location"])
    body = results_response.get_data(as_text=True)
    assert results_response.status_code == 200
    assert "Your Compliance Review Packet Is Ready" in body
    assert "WSIB clearance" in body
    assert "Insurance certificate" in body
    assert "Start-work blockers" in body


def test_try_rfp_opportunity_cache_date_is_displayed_without_timestamp(
    client, monkeypatch
):
    import flask_app

    monkeypatch.setattr(
        flask_app,
        "ranked_opportunities",
        lambda company_info, testing=False: (
            [
                {
                    "id": "real-1",
                    "title": "Real RFP",
                    "agency": "Public buyer",
                    "deadline": "See source",
                    "estimated_value": "See source",
                    "summary": "Real cached public listing.",
                    "requirements": ["Provide relevant experience."],
                    "source_name": "CanadaBuys",
                    "source_url": "https://example.com/rfp",
                    "source_status": "source_linked",
                    "fit_score": 10,
                    "fit_confidence": "weak",
                    "match_reasons": ["Low-confidence real listing."],
                }
            ],
            {
                "fetched_at": "2026-05-29T18:48:44.649099+00:00",
                "count": 1,
                "mode": "real_cached_public_listings",
                "limited_context": False,
                "guidance": "Recommendations are based on real cached public listings.",
            },
        ),
    )
    response = client.post(
        "/try-rfp",
        data={
            "email": "demo@example.com",
            "company_name": "Demo Co.",
            "company_info": "construction contractor",
        },
        follow_redirects=False,
    )
    body = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Last refreshed: 2026-05-29" in body
    assert "Opportunity cache last refreshed" not in body
    assert "18:48:44" not in body


def test_try_rfp_public_demo_can_run_and_download(client):
    response = client.post(
        "/try-rfp",
        data={
            "email": "demo@example.com",
            "company_name": "Demo Automation Co.",
            "company_info": "We build Flask and Python workflow automation for public-sector document review, evidence mapping, and approval gates.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    opportunities_path = response.headers["Location"]

    opportunities_response = client.get(opportunities_path)
    opportunities_body = opportunities_response.get_data(as_text=True)
    assert opportunities_response.status_code == 200
    assert "Choose a real cached public opportunity" in opportunities_body
    assert "Generate Package" in opportunities_body
    assert "Test fixture public listing" in opportunities_body
    assert "Optional full RFP text for this package" in opportunities_body
    assert "Recommendation confidence" in opportunities_body

    run_id = opportunities_path.rstrip("/").split("/")[-1]
    select_response = client.post(
        f"/try-rfp/select/{run_id}/sample-on-cloud-001", follow_redirects=False
    )
    assert select_response.status_code == 302
    results_path = select_response.headers["Location"]

    results_response = client.get(results_path)
    results_body = results_response.get_data(as_text=True)
    assert results_response.status_code == 200
    assert "Your Review-Ready Proposal Package Is Ready" in results_body
    assert "Download Proposal Package" in results_body
    assert "Generated by:" not in results_body
    assert "groq:" not in results_body.lower()
    assert "cerebras:" not in results_body.lower()
    assert "deepseek:" not in results_body.lower()
    assert "URXION Bid De-Risking Commentary" in results_body
    assert "Mandatory compliance watch" in results_body
    assert "Evaluation map" in results_body
    assert "Evidence gaps" in results_body
    assert "Clarification questions" in results_body

    download_response = client.get(f"/try-rfp/download/{run_id}")
    assert download_response.status_code == 200
    assert download_response.content_type == "application/zip"
    with zipfile.ZipFile(BytesIO(download_response.data)) as archive:
        assert "bid_derisking_commentary.txt" in archive.namelist()
        commentary = archive.read("bid_derisking_commentary.txt").decode()
        assert "URXION Bid De-Risking Commentary" in commentary
        assert "Mandatory compliance watch" in commentary


def test_try_rfp_public_demo_can_use_pasted_rfp_text(client):
    response = client.post(
        "/try-rfp",
        data={
            "email": "demo@example.com",
            "company_name": "Demo Construction Co.",
            "company_info": "We are a general contractor with WSIB, insurance, bonding, safety procedures, and municipal renovation experience.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    opportunities_path = response.headers["Location"]
    run_id = opportunities_path.rstrip("/").split("/")[-1]

    select_response = client.post(
        f"/try-rfp/select/{run_id}/sample-on-construction-004",
        data={
            "rfp_text": """Project: Community Centre Renovation\nDeadline: 2026-03-31\nThe bidder must provide WSIB clearance and insurance.\nThe bidder shall describe occupied facility renovation experience.\nSubmit construction schedule, safety plan, subcontractor management process, pricing, and references."""
        },
        follow_redirects=False,
    )
    assert select_response.status_code == 302
    results_response = client.get(select_response.headers["Location"])
    results_body = results_response.get_data(as_text=True)
    assert results_response.status_code == 200
    assert "Community Centre Renovation" in results_body
    assert "Construction compliance evidence" in results_body


def test_try_rfp_public_demo_can_generate_from_pasted_rfp_when_no_cached_listings(
    client, monkeypatch
):
    import flask_app

    monkeypatch.setattr(
        flask_app,
        "ranked_opportunities",
        lambda company_info, testing=False: (
            [],
            {
                "fetched_at": None,
                "count": 0,
                "mode": "real_cached_public_listings",
                "limited_context": False,
                "guidance": "No real cached public RFP listings are available right now.",
            },
        ),
    )
    response = client.post(
        "/try-rfp",
        data={
            "email": "demo@example.com",
            "company_name": "Demo Contractor",
            "company_info": "We are a construction contractor with WSIB and insurance.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    opportunities_path = response.headers["Location"]
    opportunities_body = client.get(opportunities_path).get_data(as_text=True)
    assert "Real cache unavailable" in opportunities_body
    assert "Paste a real RFP while the cache refreshes" in opportunities_body

    run_id = opportunities_path.rstrip("/").split("/")[-1]
    select_response = client.post(
        f"/try-rfp/select/{run_id}/pasted-rfp",
        data={
            "rfp_text": "Project: Real Road Repair RFP\nThe bidder must provide WSIB clearance and insurance.\nSubmit pricing and construction schedule."
        },
        follow_redirects=False,
    )
    assert select_response.status_code == 302
    results_body = client.get(select_response.headers["Location"]).get_data(
        as_text=True
    )
    assert "Real Road Repair RFP" in results_body


def test_rfp_matching_prioritizes_construction_for_construction_context():
    from rfp_opportunity_cache import ranked_opportunities

    opportunities, _ = ranked_opportunities(
        "construction contractor renovation WSIB insurance bonding safety concrete road drainage",
        testing=True,
    )
    titles = [item["title"] for item in opportunities[:2]]
    assert any("Renovation" in title or "Road" in title for title in titles)


def test_rfp_matching_prioritizes_it_for_it_context():
    from rfp_opportunity_cache import ranked_opportunities

    opportunities, _ = ranked_opportunities(
        "IT software cloud migration data analytics cybersecurity automation platform",
        testing=True,
    )
    titles = [item["title"] for item in opportunities[:2]]
    assert any("Cloud" in title or "Data" in title for title in titles)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/rfp", "We ran a 12-requirement Ontario RFP"),
        ("/compliance", "expired WSIB clearance"),
        ("/sdr", "We ran a 50-prospect list"),
    ],
)
def test_product_pages_have_real_result_boxes(client, path, expected):
    response = client.get(path)
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Real result" in body
    assert expected in visible_text(body)


def test_clean_product_routes_render_and_legacy_athena_routes_redirect(client):
    for path in ("/rfp", "/compliance", "/sdr"):
        assert client.get(path).status_code == 200

    expected_redirects = {
        "/athena-rfp": "/rfp",
        "/athena-compliance": "/compliance",
        "/athena-sdr": "/sdr",
    }
    for old_path, new_path in expected_redirects.items():
        response = client.get(old_path)
        assert response.status_code == 301
        assert response.headers["Location"].endswith(new_path)


def test_public_top_and_footer_navigation_links_engineering_resources_not_legacy_sales(
    client,
):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "AI Agent Engineering Guide" in body
    assert "Knowledge is Power</a" not in body
    assert "Sales resources" not in body
    assert "Legacy assessment" not in body


def test_active_redesigned_pages_do_not_render_em_dashes(client):
    for path in (
        "/",
        "/why-urxion",
        "/rfp",
        "/compliance",
        "/sdr",
        "/custom-agents",
        "/demo",
    ):
        response = client.get(path)
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "—" not in body


def test_footer_has_data_security_and_ownership(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert (
        "Uploaded documents are used only to generate the workflow output you request"
        in visible_text(body)
    )
    assert "Your documents are not used to train URXION models" in body


def test_data_security_page_explains_retention_and_provider_scope(client):
    response = client.get("/data-security")
    body = response.get_data(as_text=True)
    text = visible_text(body)
    assert response.status_code == 200
    assert "Clear data handling before automation" in text
    assert "deleted after 48 hours" in text
    assert "third-party AI or infrastructure providers" in text
    assert "Provider usage is disclosed before production" in text


def test_sample_outputs_page_shows_artifact_examples(client):
    response = client.get("/sample-outputs")
    body = response.get_data(as_text=True)
    text = visible_text(body)
    assert response.status_code == 200
    assert "Inspect the kind of work URXION prepares" in text
    assert "URXION RFP sample" in text
    assert "URXION Compliance sample" in text
    assert "URXION SDR sample" in text


def test_contact_form_accepts_valid_submission(client, tmp_path, monkeypatch):
    import flask_app

    monkeypatch.setattr(
        flask_app, "CONTACT_SUBMISSIONS_PATH", tmp_path / "contact.jsonl"
    )
    get_response = client.get("/contact")
    body = get_response.get_data(as_text=True)
    token_marker = 'name="csrf_token" value="'
    token = body.split(token_marker, 1)[1].split('"', 1)[0]

    response = client.post(
        "/contact",
        data={
            "csrf_token": token,
            "name": "Demo Buyer",
            "email": "buyer@example.com",
            "phone": "",
            "inquiry": "RFP response",
            "message": "We need help with RFP review.",
        },
    )
    response_body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Thanks. Your message was received" in response_body
    assert "buyer@example.com" in (tmp_path / "contact.jsonl").read_text()


def test_demo_page_embeds_calendar(client):
    response = client.get("/demo")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "See What URXION Can Do - One Free Run, No Account" in body
    assert "Try RFP Demo" in body
    assert "Try Compliance Demo" in body
    assert "Coming Soon" in body
    assert "Your data stays in a temporary workspace. Deleted after 48 hours." in body
    assert "https://calendly.com/sean-brennan-urxion/30min" in body
    assert "https://calendly.com/urxion/30min" not in body
    assert "Cold Calling That Converts" not in body
    assert "Business Assessment" not in body
    assert "Knowledge is Power</a>" not in body


def test_public_demo_forms_show_generation_feedback(client):
    rfp_body = client.get("/try-rfp").get_data(as_text=True)
    compliance_body = client.get("/try-compliance").get_data(as_text=True)
    assert 'data-loading-message="Finding real cached RFPs' in rfp_body
    assert "Please keep this page open" in rfp_body
    assert (
        'data-loading-message="Generating your compliance review packet'
        in compliance_body
    )
    assert "Please keep this page open" in compliance_body


def test_render_proposal_preview_formats_readable_html():
    import flask_app

    html = flask_app._render_proposal_preview(
        "# Title\n\n1. Executive summary\n\nParagraph with **bold** value.\n\n- one\n- two"
    )
    assert "<h2>Title</h2>" in html
    assert "<h3>Executive summary</h3>" in html
    assert "<strong>bold</strong>" in html
    assert "<ul><li>one</li><li>two</li></ul>" in html


def test_try_rfp_results_renders_formatted_proposal_preview(client):
    response = client.post(
        "/try-rfp",
        data={
            "email": "buyer@example.com",
            "company_name": "Demo Contractor",
            "company_info": "Ontario contractor with WSIB, insurance, municipal renovation work, and safety training.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    opportunities_url = response.headers["Location"]
    run_id = opportunities_url.rstrip("/").split("/")[-1]

    select_response = client.post(
        f"/try-rfp/select/{run_id}/pasted-rfp",
        data={
            "rfp_text": "Municipal renovation RFP requiring WSIB, insurance, safety plan, and project schedule."
        },
        follow_redirects=True,
    )
    body = select_response.get_data(as_text=True)
    assert select_response.status_code == 200
    assert "Proposal draft preview" in body
    assert "proposal-document" in body
    assert "<pre" not in body
    assert "Download Proposal Package" in body


def test_philosophy_page_renders_manifesto(client):
    response = client.get("/why-urxion")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Built for My Own Bottlenecks First" in body
    assert "Evidence first" in body
    assert "Fail closed" in body
    assert "AI should not be a novelty layer" in body


def test_philosophy_page_has_final_contrast_override_for_section_headings(client):
    response = client.get("/why-urxion")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Evidence first. Fail closed. Human approved." in body
    assert "body main .section-header h2" in body
    assert "color: #0f172a !important" in body
    assert "-webkit-text-fill-color: #0f172a !important" in body
    assert "Must come after all shared CSS" in body
