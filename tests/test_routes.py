from io import BytesIO

import pytest

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
    assert "yourdomain.com" not in body
    assert "pythonanywhere" not in body


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
    assert "https://www.urxion.com/demo" in body
    assert "URXION" in body
    assert "Athena" not in body


def test_homepage_has_diagnostic_headline_and_first_person_founder_copy(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Turn Your RFP, Compliance, and SDR Workflows into Review-Ready Work" in body
    assert "I built URXION because I spent 20 years" in body


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


def test_try_demo_routes_render(client):
    rfp_response = client.get("/try-rfp")
    rfp_body = rfp_response.get_data(as_text=True)
    assert rfp_response.status_code == 200
    assert "URXION RFP demo" in rfp_body
    assert "Find Matching RFPs" in rfp_body

    compliance_response = client.get("/try-compliance")
    compliance_body = compliance_response.get_data(as_text=True)
    assert compliance_response.status_code == 200
    assert "URXION Compliance demo" in compliance_body
    assert "Run Compliance Demo" in compliance_body


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
    assert "Expired" in results_body or "expired" in results_body
    assert "Download Compliance Packet" in results_body

    run_id = results_path.rstrip("/").split("/")[-1]
    download_response = client.get(f"/try-compliance/download/{run_id}")
    assert download_response.status_code == 200
    assert download_response.content_type == "application/zip"


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
    assert "Choose One Matched Public Opportunity" in opportunities_body
    assert "Generate Package" in opportunities_body
    assert "Sample fallback" in opportunities_body

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

    download_response = client.get(f"/try-rfp/download/{run_id}")
    assert download_response.status_code == 200
    assert download_response.content_type == "application/zip"


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


def test_public_top_and_footer_navigation_do_not_link_resources(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Resources</a" not in body
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
    assert "Your documents stay in your workspace" in body
    assert "You own your data. Export everything at any time." in body


def test_demo_page_embeds_calendar(client):
    response = client.get("/demo")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "See What URXION Can Do - One Free Run, No Account" in body
    assert "Try RFP Demo" in body
    assert "Try Compliance Demo" in body
    assert "Coming Soon" in body
    assert "Your data stays in a temporary workspace. Deleted after 48 hours." in body
    assert "Cold Calling That Converts" not in body
    assert "Business Assessment" not in body
    assert "Knowledge is Power</a>" not in body


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
