import gzip
import json
import logging
import math
import os
import re
import secrets
import zipfile
from datetime import UTC, datetime, timedelta
from functools import wraps
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from rfp_opportunity_cache import ranked_opportunities

GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxveq1SuTzj9PPBF5BKgFwF5DxHs7BmLLXLQPL8yV00Ryb9ORjT_K185Q7itjvgvVAm/exec"
CANONICAL_HOST = os.environ.get("CANONICAL_HOST", "www.urxion.com")
CANONICAL_BASE_URL = os.environ.get(
    "CANONICAL_BASE_URL", f"https://{CANONICAL_HOST}"
).rstrip("/")


def _load_local_env_files() -> None:
    for env_path in (
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parents[1] / "Athena" / ".env",
    ):
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_local_env_files()


def _llm_json_completion(
    system_prompt: str, user_prompt: str, *, temperature: float
) -> tuple[dict, str]:
    groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()
    openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    azure_api_key = os.environ.get("AZURE_OPENAI_KEY", "").strip()
    azure_endpoint = os.environ.get("AZURE_ENDPOINT", "").strip().rstrip("/")
    azure_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "").strip()
    azure_api_version = os.environ.get(
        "AZURE_OPENAI_API_VERSION", "2024-02-15-preview"
    ).strip()

    payload = {
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    if groq_api_key:
        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            },
            json={**payload, "model": model, "temperature": temperature},
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content), f"groq:{model}"

    if azure_api_key and azure_endpoint and azure_deployment:
        url = f"{azure_endpoint}/openai/deployments/{azure_deployment}/chat/completions?api-version={azure_api_version}"
        response = requests.post(
            url,
            headers={"api-key": azure_api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content), f"azure:{azure_deployment}"

    if openai_api_key:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json",
            },
            json={**payload, "model": model, "temperature": temperature},
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content), model

    raise RuntimeError(
        "No LLM API key is configured. Set GROQ_API_KEY, AZURE_OPENAI_KEY with AZURE_ENDPOINT and AZURE_OPENAI_DEPLOYMENT_NAME, or OPENAI_API_KEY."
    )


FOUNDATION_CSS_LINK = ""
GLOBAL_CONTRAST_STYLE = """
<style id="urxion-global-contrast-fix">
    /* Site-wide emergency readability guardrail.
       This is injected into every HTML page so legacy templates cannot hide text. */
    html,
    body {
        background: #ffffff !important;
        color: #0f172a !important;
    }
    main,
    section,
    article,
    aside,
    .container,
    .container-fluid,
    .section,
    .card,
    .hero-panel,
    .founder-card,
    .proof-card,
    .pricing-card,
    .resource-card,
    .feature-card,
    .legacy-content,
    .tm-bg-white,
    .tm-bg-gray,
    .tm-bg-gray-dark,
    .tm-box,
    .tm-box-2,
    .tm-box-3,
    .tm-content-box,
    .tm-contact-form-box,
    .tos-container,
    .results-container {
        color: #0f172a !important;
        text-shadow: none !important;
    }
    .card,
    .hero-panel,
    .founder-card,
    .proof-card,
    .pricing-card,
    .resource-card,
    .feature-card,
    .legacy-content,
    .tm-bg-white,
    .tm-bg-gray,
    .tm-bg-gray-dark,
    .tm-box,
    .tm-box-2,
    .tm-box-3,
    .tm-content-box,
    .tm-contact-form-box,
    .tos-container,
    .results-container {
        background-color: #ffffff !important;
    }
    body :where(h1, h2, h3, h4, h5, h6, strong, b, .metric, .tm-h3, .tm-text-primary) {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        opacity: 1 !important;
        visibility: visible !important;
        text-shadow: none !important;
    }
    body :where(p, li, dd, dt, label, small, span, pre, code, blockquote, figcaption, td, th, .lead, .muted, .text-muted, .text-white, .text-light, .text-white-50, .tm-text-gray, .principle-code) {
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
        opacity: 1 !important;
        visibility: visible !important;
        text-shadow: none !important;
    }
    body :where(pre, code, .principle-code) {
        display: block;
        background: #f8fafc !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        border-color: rgba(30, 58, 95, 0.18) !important;
    }
    body :where(.eyebrow, a:not(.btn):not(.btn-primary):not(.btn-secondary):not(.nav-call)) {
        color: #1d4ed8 !important;
        -webkit-text-fill-color: #1d4ed8 !important;
    }
    body :where(.btn-primary, .nav-call, .btn-primary *, .nav-call *) {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }
    body :where(.btn-secondary, .btn-secondary *) {
        color: #1e3a5f !important;
        -webkit-text-fill-color: #1e3a5f !important;
        background-color: #ffffff !important;
        border-color: rgba(30, 58, 95, 0.28) !important;
    }
    header,
    nav,
    .site-header,
    .site-header *,
    .nav-wrap,
    .nav-wrap * {
        opacity: 1 !important;
        visibility: visible !important;
        text-shadow: none !important;
    }
    footer,
    .site-footer {
        background: #f8fafc !important;
        color: #334155 !important;
    }
    footer :where(p, li, span, div, small, a),
    .site-footer :where(p, li, span, div, small, a) {
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
    }
</style>
"""


# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config.update(
    SEND_FILE_MAX_AGE_DEFAULT=31536000,
    JSONIFY_PRETTYPRINT_REGULAR=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")


def no_store(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        response = app.make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response

    return wrapped


def should_compress(response):
    if (
        response.direct_passthrough
        or response.status_code < 200
        or response.status_code >= 300
    ):
        return False
    if (
        response.headers.get("Content-Encoding")
        or "gzip" not in request.headers.get("Accept-Encoding", "").lower()
    ):
        return False
    if response.mimetype not in {
        "text/html",
        "text/css",
        "application/javascript",
        "application/json",
        "application/xml",
        "text/plain",
    }:
        return False
    return (
        response.calculate_content_length()
        and response.calculate_content_length() > 1024
    )


@app.after_request
def optimize_response(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
    )

    if response.mimetype == "text/html" and response.status_code == 200:
        body = response.get_data(as_text=True)
        if "urxion-global-contrast-fix" not in body:
            if "</body>" in body:
                body = body.replace("</body>", f"{GLOBAL_CONTRAST_STYLE}</body>", 1)
            else:
                body = f"{body}{GLOBAL_CONTRAST_STYLE}"
            response.set_data(body)
            response.headers.pop("Content-Length", None)
        response.headers.setdefault("Cache-Control", "public, max-age=300")
    elif request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif response.mimetype in {"application/xml", "text/plain"}:
        response.headers.setdefault("Cache-Control", "public, max-age=3600")

    if should_compress(response):
        gzip_buffer = BytesIO()
        with gzip.GzipFile(mode="wb", fileobj=gzip_buffer) as gzip_file:
            gzip_file.write(response.get_data())
        response.set_data(gzip_buffer.getvalue())
        response.headers["Content-Encoding"] = "gzip"
        response.headers["Content-Length"] = len(response.get_data())
        response.headers.add("Vary", "Accept-Encoding")

    return response


# Route for the new DispatchAI Landing Page
@app.route("/DispatchAI")
def DispatchAI():
    return render_template("DispatchAI.html")


@app.route("/dispatchai")
def dispatchai():
    return render_template("DispatchAI.html")


@app.route("/lastcall")
def lastcall():
    return render_template("LastCall.html")


@app.route("/LastCall")
def LastCall():
    return render_template("LastCall.html")


def should_refresh_slots():
    """Check if slots should be refreshed based on last update time"""
    last_update = session.get("slots_last_update")
    if not last_update:
        return True

    last_update = datetime.fromisoformat(last_update)
    return datetime.now() - last_update > timedelta(
        minutes=15
    )  # Refresh every 15 minutes


def fetch_available_slots():
    """Fetch available time slots and store in session"""
    if not should_refresh_slots():
        return

    try:
        response = requests.get(GOOGLE_APPS_SCRIPT_URL + "?action=getSlots")
        available_slots = response.json()
        session["available_slots"] = available_slots
        session["slots_last_update"] = datetime.now().isoformat()
    except Exception as e:
        if "available_slots" not in session:
            session["available_slots"] = {"success": False, "error": str(e)}


def log_session_data(step):
    """Logs the current session data."""
    data = session.get("data", {})
    logging.info(f"Session data at {step}: {json.dumps(data, indent=4)}")


def create_data_dictionary():
    """Creates a dictionary with all necessary keys."""
    return {
        "price_per_unit": None,
        "variable_cost_per_unit": None,
        "ae_commission_rate": None,
        "commission_per_meeting": None,
        "avg_units_per_order": None,
        "total_revenue_per_order": None,
        "variable_cost_per_order": None,
        "best_cold_call_to_lead": None,
        "best_lead_to_qualified": None,
        "best_qualified_to_client": None,
        "worst_cold_call_to_lead": None,
        "worst_lead_to_qualified": None,
        "worst_qualified_to_client": None,
        "best_cold_calls_needed": None,
        "worst_cold_calls_needed": None,
        "num_ae": None,
        "avg_salary_ae": None,
        "annual_benefits_ae": None,
        "sales_team_overhead": None,
        "company_fixed_costs": None,
        "cold_calls_per_sdr_per_week": None,
        "avg_salary_sdr": None,
        "annual_benefits_sdr": None,
        "num_sdrs": 1,
        "sdr_cost_per_closed_deal_best": None,
        "sdr_cost_per_closed_deal_worst": None,
        "total_variable_cost_internal_best": None,
        "total_variable_cost_internal_worst": None,
        "total_contribution_margin_internal_best": None,
        "total_contribution_margin_internal_worst": None,
        "break_even_orders_internal_best": None,
        "break_even_orders_internal_worst": None,
        "sales_needed_for_100k": None,
        "sales_needed_for_1M": None,
        # Add the new variables here
        "num_sdrs_best_internal": None,
        "break_even_orders_best_internal": None,
        "num_sdrs_worst_internal": None,
        "break_even_orders_worst_internal": None,
        "num_sdrs_best_urxion": None,
        "break_even_orders_best_urxion": None,
        "num_sdrs_worst_urxion": None,
        "break_even_orders_worst_urxion": None,
        "urxion_commission_per_meeting": 75,  # You'll need to define this somewhere, maybe ask for it in step 1
    }


def format_number(value):
    """Format numbers with commas and two decimal places."""
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        if math.isinf(value):
            return "Infinity"
        elif math.isnan(value):
            return "NaN"
        else:
            return f"{value:,.2f}"
    return str(value)


@app.route("/.well-known/microsoft-identity-association")
def serve_ms_identity():
    return send_from_directory(
        os.path.join(app.root_path, "templates", ".well-known"),
        "microsoft-identity-association.json",
        mimetype="application/json",
    )


@app.route("/.well-known/microsoft-identity-association.json")
def serve_ms_identity2():
    return send_from_directory(
        os.path.join(app.root_path, "templates", ".well-known"),
        "microsoft-identity-association.json",
        mimetype="application/json",
    )


# Centralized input validation function
def validate_positive_inputs(data, fields):
    return all(data[field] > 0 for field in fields)


# --- Step 1 ---
@app.route("/step_1", methods=["GET", "POST"])
def step_1():
    if "data" not in session:
        session["data"] = create_data_dictionary()

    if request.method == "POST":
        data = session["data"]
        try:
            price_per_unit = float(request.form["price_per_unit"])
            variable_cost_per_unit = float(request.form["variable_cost_per_unit"])
            ae_commission_rate = float(request.form["ae_commission_rate"])
            commission_per_meeting = float(request.form["commission_per_meeting"])
            avg_units_per_order = float(request.form["avg_units_per_order"])

            # Input validation
            if validate_positive_inputs(
                locals(),
                [
                    "price_per_unit",
                    "variable_cost_per_unit",
                    "ae_commission_rate",
                    "commission_per_meeting",
                    "avg_units_per_order",
                ],
            ):
                data.update(
                    {
                        "price_per_unit": price_per_unit,
                        "variable_cost_per_unit": variable_cost_per_unit,
                        "ae_commission_rate": ae_commission_rate,
                        "commission_per_meeting": commission_per_meeting,
                        "avg_units_per_order": avg_units_per_order,
                    }
                )
                data["total_revenue_per_order"] = (
                    data["price_per_unit"] * data["avg_units_per_order"]
                )
                data["variable_cost_per_order"] = (
                    data["variable_cost_per_unit"] * data["avg_units_per_order"]
                    + (data["ae_commission_rate"] / 100)
                    * data["total_revenue_per_order"]
                )
                session["data"] = data
                log_session_data("step_1")
                return redirect(url_for("step_2"))
            else:
                logging.warning(
                    "Input validation failed: All input values must be positive."
                )
                return render_template(
                    "step_1.html", error_message="All input values must be positive."
                )

        except ValueError:
            return render_template(
                "step_1.html",
                error_message="Invalid input. Please enter numeric values.",
            )

    return render_template("step_1.html", **session.get("data", {}))


# --- Step 2 ---
@app.route("/step_2", methods=["GET", "POST"])
def step_2():
    if request.method == "POST":
        data = session["data"]
        try:
            # Collect conversion rates
            for key in [
                "best_cold_call_to_lead",
                "best_lead_to_qualified",
                "best_qualified_to_client",
                "worst_cold_call_to_lead",
                "worst_lead_to_qualified",
                "worst_qualified_to_client",
            ]:
                data[key] = float(request.form[key]) / 100

            # Input validation for conversion rates
            if not validate_positive_inputs(
                data,
                [
                    "best_cold_call_to_lead",
                    "best_lead_to_qualified",
                    "best_qualified_to_client",
                    "worst_cold_call_to_lead",
                    "worst_lead_to_qualified",
                    "worst_qualified_to_client",
                ],
            ):
                logging.error("Conversion rates must be greater than zero.")
                return render_template(
                    "step_2.html",
                    error_message="Conversion rates must be greater than zero.",
                )

            # Calculate activities needed per stage
            for key in ["best", "worst"]:
                data[f"{key}_cold_calls_per_lead"] = (
                    1 / data[f"{key}_cold_call_to_lead"]
                )
                data[f"{key}_leads_per_qualified"] = (
                    1 / data[f"{key}_lead_to_qualified"]
                )
                data[f"{key}_qualified_per_client"] = (
                    1 / data[f"{key}_qualified_to_client"]
                )
                data[f"{key}_cold_calls_needed"] = (
                    data[f"{key}_cold_calls_per_lead"]
                    * data[f"{key}_leads_per_qualified"]
                    * data[f"{key}_qualified_per_client"]
                )

            # Ensure SDR cost per closed deal calculation
            data["sdr_cost_per_closed_deal_best"] = (
                data["commission_per_meeting"] * data["best_qualified_per_client"]
            )
            data["sdr_cost_per_closed_deal_worst"] = (
                data["commission_per_meeting"] * data["worst_qualified_per_client"]
            )

            session["data"] = data
            log_session_data("step_2")
            return redirect(url_for("step_3"))

        except ValueError:
            return render_template(
                "step_2.html",
                error_message="Invalid input. Please enter numeric values.",
            )

    return render_template("step_2.html", **session.get("data", {}))


@app.route("/step_3", methods=["GET", "POST"])
def step_3():
    if request.method == "POST":
        data = session.get("data", {})
        try:
            # Get input values from the form
            # Removed default values for variables that were already calculated
            data["num_ae"] = int(float(request.form["num_ae"]))
            data["avg_salary_ae"] = float(request.form["avg_salary_ae"])
            data["annual_benefits_ae"] = float(request.form["annual_benefits_ae"])
            data["sales_team_overhead"] = float(request.form["sales_team_overhead"])
            data["company_fixed_costs"] = float(request.form["company_fixed_costs"])
            data["cold_calls_per_sdr_per_week"] = float(
                request.form["cold_calls_per_sdr_per_week"]
            )
            data["avg_salary_sdr"] = float(request.form["avg_salary_sdr"])
            data["annual_benefits_sdr"] = float(request.form["annual_benefits_sdr"])

            # Do not overwrite calculated values with defaults
            # Ensure these values are pulled from previous steps instead
            if "price_per_unit" not in data or data["price_per_unit"] is None:
                return render_template(
                    "step_3.html", error_message="Missing price per unit."
                )
            if (
                "variable_cost_per_order" not in data
                or data["variable_cost_per_order"] is None
            ):
                return render_template(
                    "step_3.html", error_message="Missing variable cost per order."
                )
            if (
                "total_revenue_per_order" not in data
                or data["total_revenue_per_order"] is None
            ):
                return render_template(
                    "step_3.html", error_message="Missing total revenue per order."
                )

            # Log session data after collecting inputs
            logging.debug("Session Data:")
            for key, value in data.items():
                logging.debug(f"{key}: {value}")

            # Validate inputs
            input_fields = [
                "num_ae",
                "avg_salary_ae",
                "annual_benefits_ae",
                "sales_team_overhead",
                "company_fixed_costs",
                "cold_calls_per_sdr_per_week",
                "avg_salary_sdr",
                "annual_benefits_sdr",
            ]
            if not validate_positive_inputs(data, input_fields):
                logging.warning("Validation failed: All input values must be positive.")
                return render_template(
                    "step_3.html", error_message="All input values must be positive."
                )

            # Check for required prior calculations
            required_fields = [
                "sdr_cost_per_closed_deal_best",
                "sdr_cost_per_closed_deal_worst",
                "urxion_commission_per_meeting",
            ]
            if any(
                field not in data or data[field] is None for field in required_fields
            ):
                logging.error(
                    "Missing calculated values: " + ", ".join(required_fields)
                )
                return render_template(
                    "step_3.html", error_message="Required calculations are missing."
                )

            urxion_commission_per_meeting = data["urxion_commission_per_meeting"]
            sdr_capacity_per_year = data["cold_calls_per_sdr_per_week"] * 52
            profit_target = 100000  # Specify your profit target for calculations

            # --- Best Internal Scenario ---
            bi_num_sdrs = 1
            bi_break_even_orders = None  # Initialize bi_break_even_orders
            max_iterations = 100
            for _ in range(max_iterations):
                bi_total_fixed_costs = (
                    bi_num_sdrs * (data["avg_salary_sdr"] + data["annual_benefits_sdr"])
                    + data["num_ae"]
                    * (data["avg_salary_ae"] + data["annual_benefits_ae"])
                    + data["sales_team_overhead"]
                    + data["company_fixed_costs"]
                )

                bi_total_variable_cost = (
                    data["variable_cost_per_order"]
                    + data["sdr_cost_per_closed_deal_best"]
                )
                # Ensure we use the correct revenue from previous steps
                bi_total_contribution_margin = (
                    data["total_revenue_per_order"] - bi_total_variable_cost
                )

                if bi_total_contribution_margin <= 0:
                    logging.error(
                        "Total contribution margin cannot be zero or negative."
                    )
                    bi_break_even_orders = (
                        None  # Set to None if contribution margin is invalid
                    )
                    break

                bi_break_even_orders = (
                    profit_target + bi_total_fixed_costs
                ) / bi_total_contribution_margin

                bi_total_cold_calls_needed = (
                    bi_break_even_orders * data["best_cold_calls_needed"]
                )
                new_bi_num_sdrs = math.ceil(
                    bi_total_cold_calls_needed / sdr_capacity_per_year
                )

                # Check for convergence
                if new_bi_num_sdrs == bi_num_sdrs:
                    break
                bi_num_sdrs = new_bi_num_sdrs

            # Store Best Internal Scenario Results
            data["num_sdrs_best_internal"] = bi_num_sdrs
            data["break_even_orders_internal_best"] = (
                bi_break_even_orders  # Safely assign
            )
            data["total_fixed_costs_best_internal"] = bi_total_fixed_costs
            data["total_variable_cost_internal_best"] = bi_total_variable_cost
            data["total_contribution_margin_internal_best"] = (
                bi_total_contribution_margin
            )

            # Calculate Break-Even Leads and Sales
            data["break_even_leads_internal_best"] = data[
                "best_leads_per_qualified"
            ] * (bi_break_even_orders if bi_break_even_orders else 0)
            data["break_even_sales_internal_best"] = (
                (bi_break_even_orders * data["price_per_unit"])
                if bi_break_even_orders
                else 0
            )

            logging.debug(
                f"Best Internal Scenario - Num SDRs: {bi_num_sdrs}, Break Even Orders: {bi_break_even_orders}"
            )

            # --- Worst Internal Scenario ---
            wi_num_sdrs = 1
            wi_break_even_orders = None

            for _ in range(max_iterations):
                wi_total_fixed_costs = (
                    wi_num_sdrs * (data["avg_salary_sdr"] + data["annual_benefits_sdr"])
                    + data["num_ae"]
                    * (data["avg_salary_ae"] + data["annual_benefits_ae"])
                    + data["sales_team_overhead"]
                    + data["company_fixed_costs"]
                )

                wi_total_variable_cost = (
                    data["variable_cost_per_order"]
                    + data["sdr_cost_per_closed_deal_worst"]
                )
                # Ensure we use the correct revenue from previous steps
                wi_total_contribution_margin = (
                    data["total_revenue_per_order"] - wi_total_variable_cost
                )

                if wi_total_contribution_margin <= 0:
                    logging.error(
                        "Total contribution margin cannot be zero or negative."
                    )
                    wi_break_even_orders = (
                        None  # Set to None if contribution margin is invalid
                    )
                    break

                wi_break_even_orders = (
                    profit_target + wi_total_fixed_costs
                ) / wi_total_contribution_margin

                wi_total_cold_calls_needed = (
                    wi_break_even_orders * data["worst_cold_calls_needed"]
                )
                new_wi_num_sdrs = math.ceil(
                    wi_total_cold_calls_needed / sdr_capacity_per_year
                )

                # Check for convergence
                if new_wi_num_sdrs == wi_num_sdrs:
                    break
                wi_num_sdrs = new_wi_num_sdrs

            # Store Worst Internal Scenario Results
            data["num_sdrs_worst_internal"] = wi_num_sdrs
            data["break_even_orders_internal_worst"] = (
                wi_break_even_orders  # Safely assign
            )
            data["total_fixed_costs_worst_internal"] = wi_total_fixed_costs
            data["total_variable_cost_internal_worst"] = wi_total_variable_cost
            data["total_contribution_margin_internal_worst"] = (
                wi_total_contribution_margin
            )

            # Calculate Break-Even Leads and Sales
            data["break_even_leads_internal_worst"] = data[
                "worst_leads_per_qualified"
            ] * (wi_break_even_orders if wi_break_even_orders else 0)
            data["break_even_sales_internal_worst"] = (
                (wi_break_even_orders * data["price_per_unit"])
                if wi_break_even_orders
                else 0
            )

            logging.debug(
                f"Worst Internal Scenario - Num SDRs: {wi_num_sdrs}, Break Even Orders: {wi_break_even_orders}"
            )

            # --- Best Urxion Scenario ---
            bu_num_sdrs = 0  # Assumes no SDRs needed for Urxion
            bu_total_fixed_costs = (
                data["num_ae"] * (data["avg_salary_ae"] + data["annual_benefits_ae"])
                + data["sales_team_overhead"]
                + data["company_fixed_costs"]
            )
            bu_total_variable_cost = data["variable_cost_per_order"] + (
                urxion_commission_per_meeting * data["best_qualified_per_client"]
            )
            # Ensure we use the correct revenue from previous steps
            bu_total_contribution_margin = (
                data["total_revenue_per_order"] - bu_total_variable_cost
            )

            if bu_total_contribution_margin <= 0:
                logging.error(
                    "Urxion Best Case Contribution margin cannot be zero or negative."
                )
                bu_break_even_orders = None
            else:
                bu_break_even_orders = (
                    profit_target + bu_total_fixed_costs
                ) / bu_total_contribution_margin

            # Store Best Urxion Scenario Results
            data["num_sdrs_best_urxion"] = bu_num_sdrs
            data["break_even_orders_best_urxion"] = bu_break_even_orders
            data["break_even_leads_urxion_best"] = data["best_leads_per_qualified"] * (
                bu_break_even_orders if bu_break_even_orders else 0
            )
            data["break_even_sales_urxion_best"] = (
                (bu_break_even_orders * data["price_per_unit"])
                if bu_break_even_orders
                else 0
            )

            logging.debug(
                f"Best Urxion Scenario - Num SDRs: {bu_num_sdrs}, Break Even Orders: {bu_break_even_orders}"
            )

            # --- Worst Urxion Scenario ---
            wu_num_sdrs = 0  # Assumes no SDRs needed for Urxion
            wu_total_fixed_costs = (
                data["num_ae"] * (data["avg_salary_ae"] + data["annual_benefits_ae"])
                + data["sales_team_overhead"]
                + data["company_fixed_costs"]
            )
            wu_total_variable_cost = data["variable_cost_per_order"] + (
                urxion_commission_per_meeting * data["worst_qualified_per_client"]
            )
            # Ensure we use the correct revenue from previous steps
            wu_total_contribution_margin = (
                data["total_revenue_per_order"] - wu_total_variable_cost
            )

            if wu_total_contribution_margin <= 0:
                logging.error(
                    "Urxion Worst Case Contribution margin cannot be zero or negative."
                )
                wu_break_even_orders = None
            else:
                wu_break_even_orders = (
                    profit_target + wu_total_fixed_costs
                ) / wu_total_contribution_margin

            # Store Worst Urxion Scenario Results
            data["num_sdrs_worst_urxion"] = wu_num_sdrs
            data["break_even_orders_worst_urxion"] = wu_break_even_orders
            data["break_even_leads_urxion_worst"] = data[
                "worst_leads_per_qualified"
            ] * (wu_break_even_orders if wu_break_even_orders else 0)
            data["break_even_sales_urxion_worst"] = (
                (wu_break_even_orders * data["price_per_unit"])
                if wu_break_even_orders
                else 0
            )

            logging.debug(
                f"Worst Urxion Scenario - Num SDRs: {wu_num_sdrs}, Break Even Orders: {wu_break_even_orders}"
            )

            # --- Profit Target Analysis ---
            # Assuming you want to calculate for $100k and $1M profit targets
            profit_targets = [100000, 1000000]
            for target in profit_targets:
                # Best Internal
                bi_break_even_orders_target = (
                    (target + data["total_fixed_costs_best_internal"])
                    / data["total_contribution_margin_internal_best"]
                    if data["total_contribution_margin_internal_best"] > 0
                    else None
                )
                data[f"sales_needed_for_{int(target / 1000)}k_internal_best"] = (
                    (bi_break_even_orders_target * data["price_per_unit"])
                    if bi_break_even_orders_target
                    else 0
                )

                # Worst Internal
                wi_break_even_orders_target = (
                    (target + data["total_fixed_costs_worst_internal"])
                    / data["total_contribution_margin_internal_worst"]
                    if data["total_contribution_margin_internal_worst"] > 0
                    else None
                )
                data[f"sales_needed_for_{int(target / 1000)}k_internal_worst"] = (
                    (wi_break_even_orders_target * data["price_per_unit"])
                    if wi_break_even_orders_target
                    else 0
                )

                # Best Urxion
                bu_break_even_orders_target = (
                    (target + bu_total_fixed_costs) / bu_total_contribution_margin
                    if bu_total_contribution_margin > 0
                    else None
                )
                data[f"sales_needed_for_{int(target / 1000)}k_urxion_best"] = (
                    (bu_break_even_orders_target * data["price_per_unit"])
                    if bu_break_even_orders_target
                    else 0
                )

                # Worst Urxion
                wu_break_even_orders_target = (
                    (target + wu_total_fixed_costs) / wu_total_contribution_margin
                    if wu_total_contribution_margin > 0
                    else None
                )
                data[f"sales_needed_for_{int(target / 1000)}k_urxion_worst"] = (
                    (wu_break_even_orders_target * data["price_per_unit"])
                    if wu_break_even_orders_target
                    else 0
                )

            logging.debug("Profit Target Analysis Calculated.")

            # Save updated data back to the session
            session["data"] = data
            log_session_data("step_3")
            return redirect(url_for("step_4"))

        except (ValueError, KeyError) as e:
            logging.error(f"Error in Step 3: {e}")
            return render_template(
                "step_3.html",
                error_message="Please check your input. Errors may be due to missing data.",
            )

    return render_template("step_3.html", **session.get("data", {}))


# --- Step 4 ---
@app.route("/step_4", methods=["GET"])
def step_4():
    data = session.get("data", {})
    formatted_data = {}

    # Prepare formatted data for HTML display
    for key, value in data.items():
        if value is None:
            formatted_data[key] = "N/A"  # Use "N/A" for NoneType values
        else:
            formatted_data[key] = "{:,.2f}".format(value)  # Format numbers

    return render_template("step_4.html", **formatted_data)


# --- Additional Steps ---
@app.route("/step_5", methods=["GET"])
def step_5():
    data = session.get("data", {})
    formatted_data = {key: "{:,.2f}".format(value) for key, value in data.items()}
    return render_template("step_5.html", **formatted_data)


@app.route("/step_6", methods=["GET"])
def step_6():
    data = session.get("data", {})
    formatted_data = {key: "{:,.2f}".format(value) for key, value in data.items()}
    return render_template("step_6.html", **formatted_data)


# Custom filter for formatting numbers
@app.template_filter("format_number")
def format_number_filter(value):
    return "{:,.2f}".format(value) if isinstance(value, (int, float)) else value


####################################################


# Home Page
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/defaultsite")
def defaultsite():
    return render_template("index.html")


@app.route("/why-urxion")
def why_urxion():
    return render_template("philosophy.html")


@app.route("/rfp")
def athena_rfp():
    return render_template("rfp.html")


@app.route("/athena-rfp")
def athena_rfp_legacy():
    return redirect(url_for("athena_rfp"), code=301)


@app.route("/compliance")
def athena_compliance():
    return render_template("compliance.html")


@app.route("/athena-compliance")
def athena_compliance_legacy():
    return redirect(url_for("athena_compliance"), code=301)


@app.route("/sdr")
def athena_sdr():
    return render_template("sdr.html")


@app.route("/athena-sdr")
def athena_sdr_legacy():
    return redirect(url_for("athena_sdr"), code=301)


@app.route("/custom-agents")
def custom_agents():
    return render_template("custom-agents.html")


# Services Page
@app.route("/services")
def services():
    return redirect(url_for("athena_rfp"), code=301)


# Legacy Cold Calling Page
@app.route("/cold-calling-that-converts")
def cold_calling():
    return redirect(url_for("athena_sdr"), code=301)


# Business Assessment Page
@app.route("/business-assessment")
def business_assessment():
    return render_template("Business Assessment.html")


# Cold Calling Assessment Page
@app.route("/cold-calling-assessment")
def cold_calling_assessment():
    return render_template("Cold Calling Assessment.html")


# Book Reviews Page
@app.route("/Knowledge-is-Power", endpoint="knowledge_is_power")
def knowledge_is_power():
    return render_template("Knowledge is Power.html")


# Demo Page
@app.route("/demo")
@no_store
def demo():
    return render_template("demo.html")


RFP_DEMO_ROOT = Path(__file__).resolve().parent / "demo_runs" / "rfp"
RFP_DEMO_TTL = timedelta(hours=48)


def _rfp_demo_cleanup() -> None:
    RFP_DEMO_ROOT.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(UTC) - RFP_DEMO_TTL
    for path in RFP_DEMO_ROOT.iterdir():
        if path.is_dir() and datetime.fromtimestamp(path.stat().st_mtime, UTC) < cutoff:
            import shutil

            shutil.rmtree(path, ignore_errors=True)


def _rfp_demo_run_dir(run_id: str) -> Path:
    return RFP_DEMO_ROOT / run_id


def _rfp_demo_state_path(run_id: str) -> Path:
    return _rfp_demo_run_dir(run_id) / "state.json"


def _rfp_demo_read_state(run_id: str):
    if not re.match(r"^[a-f0-9]{16}$", run_id):
        return None
    path = _rfp_demo_state_path(run_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _rfp_demo_find_opportunity(state: dict, opportunity_id: str):
    return next(
        (opp for opp in state.get("opportunities", []) if opp["id"] == opportunity_id),
        None,
    )


def _rfp_demo_program_bullets(
    company_name: str, opportunity: dict, first_section: str
) -> str:
    requirements = opportunity.get("requirements", [])
    requirement_bullets = "\n".join(
        f"- {requirement}: mapped to supplied evidence, assigned a support level, and routed for human confirmation."
        for requirement in requirements
    )
    if not requirement_bullets:
        requirement_bullets = "- Buyer requirements: decomposed into response tasks, evidence requests, compliance checks, and approval gates."

    return f"""URXION RFP DEMO PACKAGE

Opportunity: {opportunity["title"]}
Buyer: {opportunity["agency"]}
Respondent: {company_name}

1. Detailed first section generated from your supplied context

{first_section.strip()}

2. What the full URXION RFP program would deliver

This public demo shows the opening section only. In the full program, URXION works from the complete solicitation package plus your source material so the final package can be built with enough detail for a real buyer review. With the RFP documents, forms, pricing inputs, resumes, project examples, certifications, policies, and approval rules, the full workflow would deliver:

- A complete proposal draft, not just the opening section, covering the executive summary, understanding of need, technical approach, delivery plan, team structure, relevant experience, risk controls, transition plan, pricing narrative, and closing.
- A requirement-by-requirement compliance matrix that shows where each buyer instruction is answered, what evidence supports it, and what still needs confirmation before submission.
- A source-backed claim audit so the team can see which statements are supported by company evidence, which require a document owner, and which should be removed or softened.
- A gap and risk list that separates missing attachments, unclear requirements, policy issues, insurance or security questions, pricing dependencies, and mandatory forms.
- A human approval packet for executives, sales, operations, legal, finance, and delivery leads so no proposal is submitted without review.
- A submission checklist organized around the buyer portal, file naming, mandatory forms, signatures, deadlines, addenda, and final quality control.

3. Requirement handling in the full program

{requirement_bullets}

4. What URXION would need from your team

- The full RFP package, including addenda, schedules, appendices, evaluation criteria, mandatory forms, and portal instructions.
- Company evidence such as case studies, past performance summaries, resumes, insurance certificates, certifications, security/privacy policies, implementation plans, and references.
- Commercial inputs such as pricing assumptions, service boundaries, delivery timelines, partner/subcontractor roles, and exceptions that require business approval.
- Named reviewers for technical accuracy, legal/compliance review, pricing approval, and final executive sign-off.

5. Demo boundary

- This demo does not auto-submit anything and should not be used as a final bid.
- The opening section is generated from limited information supplied in the demo form.
- The remaining bullets describe the full URXION program that becomes available when the complete solicitation and company evidence are provided.
- Human review remains required before any buyer-facing submission.
"""


def _rfp_demo_fallback_package(
    company_name: str, company_info: str, opportunity: dict
) -> dict:
    """Deterministic test-only package used when Flask TESTING is enabled."""
    requirements = opportunity["requirements"]
    company_summary = (
        " ".join(company_info.split())[:1200] or "No company evidence supplied."
    )
    first_section = f"""{company_name} is responding to {opportunity["agency"]} with capabilities aligned to {opportunity["title"]}.

This automated-test fallback summarizes the company context supplied in the demo: {company_summary}

Before this language could be used in a real proposal, every capability, certification, timeline, and delivery claim would need to be confirmed against source evidence by a human reviewer."""
    proposal = _rfp_demo_program_bullets(company_name, opportunity, first_section)
    compliance_matrix = [["Requirement", "Status", "Evidence", "Risk"]]
    for requirement in requirements:
        compliance_matrix.append(
            [requirement, "review_needed", "Company info supplied in demo", "review"]
        )
    checklist = [
        "Review the generated first section for accuracy and tone",
        "Provide the full RFP package and all buyer forms",
        "Attach source evidence for security, privacy, insurance, certifications, and past performance",
        "Confirm pricing, delivery timeline, exceptions, and approval owners",
        "Obtain human approval before submission",
    ]
    return {
        "proposal": proposal,
        "compliance_matrix": compliance_matrix,
        "checklist": checklist,
        "claim_audit": [],
        "generated_by": "test_fallback",
    }


def _rfp_demo_llm_prompt(
    company_name: str, company_info: str, opportunity: dict
) -> str:
    return f"""
You are URXION RFP, a human-reviewed proposal drafting workflow.

Generate only the detailed first section of the RFP demo package.
The first section should read like a strong buyer-facing opening section for a proposal: specific, grounded, and relevant to the opportunity.
Do not write the full proposal. The application will append fixed full-program bullets after your first section.
Do not invent certifications, references, prices, legal terms, security attestations, or past projects.
Use only the supplied company context. If evidence is missing, flag it in practical buyer-safe language.
Write in a professional public-sector proposal style.
No hype. No auto-submit language. Human final approval is required.

Return valid JSON only with this exact shape:
{{
  "first_section": "A detailed opening proposal section of roughly 500-800 words. Include a clear heading and paragraphs that cover fit, understanding of need, how the respondent would approach the work, and evidence limitations that need review.",
  "compliance_matrix": [["Requirement", "Status", "Evidence", "Risk"], ["...", "supported|partial|gap", "...", "low|medium|high|review"]],
  "checklist": ["submission/checklist item", "..."],
  "claim_audit": [{{"claim": "...", "support_status": "supported|unsupported|needs_review", "source": "company_info|rfp_requirement|gap"}}]
}}

Opportunity:
Title: {opportunity["title"]}
Buyer: {opportunity["agency"]}
Deadline: {opportunity["deadline"]}
Estimated value: {opportunity["estimated_value"]}
Summary: {opportunity["summary"]}
Requirements:
{chr(10).join(f"- {requirement}" for requirement in opportunity["requirements"])}

Respondent company name:
{company_name}

Company context supplied by user:
{company_info[:8000]}
""".strip()


def _rfp_demo_build_package(
    company_name: str, company_info: str, opportunity: dict
) -> dict:
    if app.config.get("TESTING"):
        return _rfp_demo_fallback_package(company_name, company_info, opportunity)

    package, model = _llm_json_completion(
        "You draft source-aware public-sector proposal opening sections for human review. Return valid JSON only.",
        _rfp_demo_llm_prompt(company_name, company_info, opportunity),
        temperature=0.2,
    )
    first_section = package.get("first_section") or package.get("proposal")
    package["proposal"] = _rfp_demo_program_bullets(
        company_name,
        opportunity,
        first_section or "No generated first section was returned.",
    )
    package.setdefault("generated_by", model)
    if (
        not isinstance(package.get("compliance_matrix"), list)
        or not isinstance(package.get("checklist"), list)
        or not first_section
    ):
        raise RuntimeError("LLM returned an incomplete RFP demo package.")
    return package


@app.route("/try-rfp", methods=["GET", "POST"])
@no_store
def try_rfp():
    _rfp_demo_cleanup()
    if request.method == "GET":
        return render_template("try_rfp.html")
    company_name = request.form.get("company_name", "").strip() or "Demo Company"
    company_info = request.form.get("company_info", "").strip()
    email = request.form.get("email", "").strip().lower()
    if not email or "@" not in email:
        return render_template(
            "try_rfp.html", error="Enter a valid email address."
        ), 400
    if not company_info:
        return render_template(
            "try_rfp.html", error="Paste a short company profile or capability summary."
        ), 400
    run_id = secrets.token_hex(8)
    run_dir = _rfp_demo_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    opportunities, cache_meta = ranked_opportunities(
        company_info, testing=app.config.get("TESTING", False)
    )
    state = {
        "run_id": run_id,
        "company_name": company_name,
        "email_domain": email.split("@")[-1],
        "company_info": company_info,
        "created_at": datetime.now(UTC).isoformat(),
        "opportunities": opportunities,
        "cache_meta": {
            "fetched_at": cache_meta.get("fetched_at"),
            "count": cache_meta.get("count"),
        },
    }
    _rfp_demo_state_path(run_id).write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    return redirect(url_for("try_rfp_opportunities", run_id=run_id))


@app.route("/try-rfp/opportunities/<run_id>")
@no_store
def try_rfp_opportunities(run_id):
    state = _rfp_demo_read_state(run_id)
    if not state:
        abort(404)
    return render_template("try_rfp_opportunities.html", state=state)


@app.route("/try-rfp/select/<run_id>/<opportunity_id>", methods=["POST"])
@no_store
def try_rfp_select(run_id, opportunity_id):
    state = _rfp_demo_read_state(run_id)
    opportunity = _rfp_demo_find_opportunity(state or {}, opportunity_id)
    if not state or not opportunity:
        abort(404)
    try:
        package = _rfp_demo_build_package(
            state["company_name"], state["company_info"], opportunity
        )
    except Exception as exc:
        return render_template(
            "try_rfp_opportunities.html", state=state, error=str(exc)
        ), 503
    state["selected_opportunity"] = opportunity
    state["package"] = package
    _rfp_demo_state_path(run_id).write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    return redirect(url_for("try_rfp_results", run_id=run_id))


@app.route("/try-rfp/results/<run_id>")
@no_store
def try_rfp_results(run_id):
    state = _rfp_demo_read_state(run_id)
    if not state or "package" not in state:
        abort(404)
    return render_template("try_rfp_results.html", state=state)


@app.route("/try-rfp/download/<run_id>")
@no_store
def try_rfp_download(run_id):
    state = _rfp_demo_read_state(run_id)
    if not state or "package" not in state:
        abort(404)
    package = state["package"]
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("proposal_draft.txt", package["proposal"])
        matrix_csv = "\n".join(
            ",".join('"' + str(cell).replace('"', '""') + '"' for cell in row)
            for row in package["compliance_matrix"]
        )
        zf.writestr("compliance_matrix.csv", matrix_csv)
        zf.writestr(
            "submission_checklist.txt",
            "\n".join(f"- {item}" for item in package["checklist"]),
        )
        zf.writestr(
            "audit_note.txt",
            "Public demo package. Human final approval required. No auto-submit.",
        )
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=urxion-rfp-demo-{run_id}.zip"
        },
    )


COMPLIANCE_DEMO_ROOT = Path(__file__).resolve().parent / "demo_runs" / "compliance"
COMPLIANCE_DEMO_TTL = timedelta(hours=48)


def _compliance_demo_cleanup() -> None:
    COMPLIANCE_DEMO_ROOT.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(UTC) - COMPLIANCE_DEMO_TTL
    for path in COMPLIANCE_DEMO_ROOT.iterdir():
        if path.is_dir() and datetime.fromtimestamp(path.stat().st_mtime, UTC) < cutoff:
            import shutil

            shutil.rmtree(path, ignore_errors=True)


def _compliance_demo_run_dir(run_id: str) -> Path:
    return COMPLIANCE_DEMO_ROOT / run_id


def _compliance_demo_state_path(run_id: str) -> Path:
    return _compliance_demo_run_dir(run_id) / "state.json"


def _compliance_demo_read_state(run_id: str):
    if not re.match(r"^[a-f0-9]{16}$", run_id):
        return None
    path = _compliance_demo_state_path(run_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _compliance_demo_safe_filename(filename: str) -> str:
    cleaned = re.sub(
        r"[^A-Za-z0-9_.-]+", "-", filename or "subcontractor-package.txt"
    ).strip(".-")
    return cleaned or "subcontractor-package.txt"


def _compliance_demo_read_upload(upload) -> tuple[str, str]:
    filename = _compliance_demo_safe_filename(
        upload.filename or "subcontractor-package.txt"
    )
    raw = upload.read()
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("File must be 10 MB or smaller.")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".pdf", ".docx"}:
        raise ValueError("Allowed file types: PDF, DOCX, TXT.")
    if suffix == ".txt":
        try:
            return filename, raw.decode("utf-8")
        except UnicodeDecodeError:
            return filename, raw.decode("latin-1", errors="ignore")
    return (
        filename,
        f"Uploaded {suffix.upper()} file {filename}. Text extraction is limited in this public demo preview. A human reviewer should verify the original document.",
    )


def _compliance_demo_fallback_review(
    form: dict, filename: str, document_text: str
) -> dict:
    """Deterministic test-only review used when Flask TESTING is enabled."""
    text = document_text.lower()
    subcontractor = (
        form.get("subcontractor_name", "").strip() or "Uploaded subcontractor"
    )
    project = form.get("project_name", "").strip() or "Demo project"
    evidence_matrix = []
    blockers = []
    remediation_plan = []

    def add_row(rule, required, status, excerpt, risk, action=None, blocker=False):
        evidence_matrix.append(
            {
                "rule": rule,
                "required_evidence": required,
                "matched_document": filename if excerpt else "Missing / not detected",
                "source_excerpt": excerpt
                or "No matching source excerpt detected in the uploaded package.",
                "status": status,
                "risk": risk,
            }
        )
        if blocker:
            blockers.append(
                {
                    "rule": rule,
                    "description": action
                    or f"Resolve {rule} before start-work approval.",
                }
            )
        if action:
            remediation_plan.append(
                {
                    "priority": "High" if blocker else "Review",
                    "action": action,
                    "rule": rule,
                }
            )

    if "expired" in text and "wsib" in text:
        add_row(
            "WSIB clearance",
            "Current WSIB clearance certificate",
            "expired",
            "WSIB clearance appears with expired language in the uploaded package.",
            "high",
            "Request a current WSIB clearance certificate before mobilization.",
            True,
        )
    elif "wsib" in text:
        add_row(
            "WSIB clearance",
            "Current WSIB clearance certificate",
            "review",
            "WSIB referenced in uploaded package.",
            "review",
            "Verify WSIB clearance number, legal name, and expiry date.",
        )
    else:
        add_row(
            "WSIB clearance",
            "Current WSIB clearance certificate",
            "missing",
            "",
            "high",
            "Request WSIB clearance certificate.",
            True,
        )

    if "insurance" in text and (
        "mismatch" in text or "different name" in text or "name mismatch" in text
    ):
        add_row(
            "Insurance certificate",
            "Valid certificate with matching legal name and coverage",
            "mismatch",
            "Insurance certificate appears to include a name mismatch.",
            "high",
            "Request corrected insurance certificate with matching legal name and required coverage.",
            True,
        )
    elif "insurance" in text:
        add_row(
            "Insurance certificate",
            "Valid certificate with matching legal name and coverage",
            "review",
            "Insurance certificate referenced in uploaded package.",
            "review",
            "Verify legal name, additional insured wording, coverage, and expiry.",
        )
    else:
        add_row(
            "Insurance certificate",
            "Valid certificate with matching legal name and coverage",
            "missing",
            "",
            "high",
            "Request certificate of insurance.",
            True,
        )

    if "training" in text or "whmis" in text or "working at heights" in text:
        add_row(
            "Training records",
            "Required safety/trade training evidence",
            "review",
            "Training evidence referenced in uploaded package.",
            "review",
            "Verify training dates, worker names, and role relevance.",
        )
    else:
        add_row(
            "Training records",
            "Required safety/trade training evidence",
            "missing",
            "",
            "medium",
            "Request training records for assigned workers.",
        )

    if "safety" in text or "policy" in text or "hazard" in text:
        add_row(
            "Safety program",
            "Safety policy, hazard controls, or site safety plan",
            "review",
            "Safety material referenced in uploaded package.",
            "review",
            "Confirm safety controls are current and project-specific.",
        )
    else:
        add_row(
            "Safety program",
            "Safety policy, hazard controls, or site safety plan",
            "missing",
            "",
            "medium",
            "Request safety policy or project-specific safety plan.",
        )

    if not remediation_plan:
        remediation_plan.append(
            {
                "priority": "Review",
                "action": "Have a qualified reviewer confirm all evidence before approving start work.",
                "rule": "Human approval",
            }
        )

    return {
        "subcontractor_name": subcontractor,
        "project_name": project,
        "overall_status": "blocked" if blockers else "review_needed",
        "evidence_matrix": evidence_matrix,
        "blockers": blockers,
        "remediation_plan": remediation_plan,
        "disclaimer": "Not legal advice. Built for qualified human review. The system never auto-certifies compliance.",
        "generated_by": "test_fallback",
    }


def _compliance_demo_llm_prompt(form: dict, filename: str, document_text: str) -> str:
    return f"""
You are URXION Compliance, a human-reviewed Ontario construction subcontractor package review workflow.

Review the supplied subcontractor package text. Produce a practical compliance review packet.
Do not certify compliance. Do not provide legal advice. Do not invent evidence.
If evidence is missing, expired, mismatched, or unclear, flag it.
Focus on WSIB clearance, insurance, training, safety, and contract/start-work evidence.

Return valid JSON only with this exact shape:
{{
  "subcontractor_name": "...",
  "project_name": "...",
  "overall_status": "blocked|review_needed|ready_for_human_review",
  "evidence_matrix": [{{"rule": "...", "required_evidence": "...", "matched_document": "...", "source_excerpt": "...", "status": "present|missing|expired|mismatch|review", "risk": "low|medium|high|review"}}],
  "blockers": [{{"rule": "...", "description": "..."}}],
  "remediation_plan": [{{"priority": "High|Medium|Review", "action": "...", "rule": "..."}}],
  "disclaimer": "Not legal advice. Built for qualified human review. The system never auto-certifies compliance."
}}

Project metadata:
Subcontractor: {form.get("subcontractor_name", "").strip() or "Uploaded subcontractor"}
Project: {form.get("project_name", "").strip() or "Demo project"}
Location: {form.get("project_location", "").strip() or "Ontario"}
Planned start date: {form.get("planned_start_date", "").strip() or "Not provided"}
Work type: {form.get("work_type", "").strip() or "Not provided"}
Filename: {filename}

Uploaded package text:
{document_text[:12000]}
""".strip()


def _compliance_demo_build_review(
    form: dict, filename: str, document_text: str
) -> dict:
    if app.config.get("TESTING"):
        return _compliance_demo_fallback_review(form, filename, document_text)

    review, model = _llm_json_completion(
        "You review subcontractor compliance packages for human approval. Return valid JSON only. Do not certify compliance.",
        _compliance_demo_llm_prompt(form, filename, document_text),
        temperature=0.1,
    )
    review.setdefault("generated_by", model)
    review.setdefault(
        "disclaimer",
        "Not legal advice. Built for qualified human review. The system never auto-certifies compliance.",
    )
    for key in ("evidence_matrix", "blockers", "remediation_plan"):
        if not isinstance(review.get(key), list):
            raise RuntimeError("LLM returned an incomplete Compliance review.")
    return review


@app.route("/try-compliance", methods=["GET", "POST"])
@no_store
def try_compliance():
    _compliance_demo_cleanup()
    if request.method == "GET":
        return render_template("try_compliance.html")
    email = request.form.get("email", "").strip().lower()
    if not email or "@" not in email:
        return render_template(
            "try_compliance.html", error="Enter a valid email address."
        ), 400
    upload = request.files.get("documents")
    if not upload or not upload.filename:
        return render_template(
            "try_compliance.html", error="Upload a subcontractor package file."
        ), 400
    try:
        filename, document_text = _compliance_demo_read_upload(upload)
    except ValueError as exc:
        return render_template("try_compliance.html", error=str(exc)), 400
    if re.search(
        r"ignore\s+(all\s+)?previous\s+instructions|system\s+prompt|prompt\s+injection|bypass\s+approval",
        document_text,
        re.I,
    ):
        return render_template(
            "try_compliance.html",
            error="The uploaded package includes prompt-injection language and cannot be processed in the public demo.",
        ), 400
    try:
        review = _compliance_demo_build_review(request.form, filename, document_text)
    except Exception as exc:
        return render_template("try_compliance.html", error=str(exc)), 503
    run_id = secrets.token_hex(8)
    run_dir = _compliance_demo_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "email_domain": email.split("@")[-1],
        "filename": filename,
        "review": review,
    }
    _compliance_demo_state_path(run_id).write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    return redirect(url_for("try_compliance_results", run_id=run_id))


@app.route("/try-compliance/results/<run_id>")
@no_store
def try_compliance_results(run_id):
    state = _compliance_demo_read_state(run_id)
    if not state:
        abort(404)
    return render_template("try_compliance_results.html", state=state)


@app.route("/try-compliance/download/<run_id>")
@no_store
def try_compliance_download(run_id):
    state = _compliance_demo_read_state(run_id)
    if not state:
        abort(404)
    review = state["review"]
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        matrix_rows = [
            [
                "Rule",
                "Required Evidence",
                "Matched Document",
                "Status",
                "Risk",
                "Source Excerpt",
            ]
        ]
        for row in review["evidence_matrix"]:
            matrix_rows.append(
                [
                    row["rule"],
                    row["required_evidence"],
                    row["matched_document"],
                    row["status"],
                    row["risk"],
                    row["source_excerpt"],
                ]
            )
        matrix_csv = "\n".join(
            ",".join('"' + str(cell).replace('"', '""') + '"' for cell in row)
            for row in matrix_rows
        )
        zf.writestr("evidence_matrix.csv", matrix_csv)
        zf.writestr(
            "start_work_blockers.txt",
            "\n".join(
                f"- {item['rule']}: {item['description']}"
                for item in review["blockers"]
            )
            or "No high-risk blockers detected. Human review still required.",
        )
        zf.writestr(
            "remediation_plan.txt",
            "\n".join(
                f"- {item['priority']}: {item['action']} ({item['rule']})"
                for item in review["remediation_plan"]
            ),
        )
        zf.writestr("human_approval_note.txt", review["disclaimer"])
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=urxion-compliance-demo-{run_id}.zip"
        },
    )


@app.route("/cold-calling-results", methods=["POST"])
def cold_calling_results():
    form_data = request.form
    recommended_chapters = analyze_responses(form_data)
    return render_template("results.html", chapters=recommended_chapters)


# Define the chapters and their relevance to different topics
chapters = {
    "dedicated_scripts": [
        {
            "title": "Chapter 5: Strategic Prospecting and Preparing for Sales Dialogue",
            "link": "sell_chapter_5",
        },
        {
            "title": "Chapter 6: Planning Sales Dialogues and Presentations",
            "link": "sell_chapter_6",
        },
    ],
    "objection_training": [
        {
            "title": "Chapter 7: Overcoming Objections",
            "link": "cold_to_committed_chapter_7",
        },
        {
            "title": "Chapter 27: Turning Around Objections",
            "link": "sales_eq_chapter_27",
        },
    ],
    "clear_criteria": [
        {"title": "Chapter 3: Understanding Buyers", "link": "sell_chapter_3"},
        {
            "title": "Chapter 5: Strategic Prospecting and Preparing for Sales Dialogue",
            "link": "sell_chapter_5",
        },
    ],
    "consistent_followup": [
        {
            "title": "Chapter 9: Expanding Customer Relationships",
            "link": "sell_chapter_9",
        },
        {
            "title": "Chapter 10: Adding Value: Self-Leadership and Teamwork",
            "link": "sell_chapter_10",
        },
    ],
    "crm_tracking": [
        {"title": "Chapter 4: Communication Skills", "link": "sell_chapter_4"},
        {
            "title": "Chapter 6: Planning Sales Dialogues and Presentations",
            "link": "sell_chapter_6",
        },
    ],
    "followup_attempts": [
        {
            "title": "Chapter 8: Addressing Concerns and Earning Commitment",
            "link": "sell_chapter_8",
        },
        {
            "title": "Chapter 9: Expanding Customer Relationships",
            "link": "sell_chapter_9",
        },
    ],
    "recruiting_system": [
        {
            "title": "Chapter 1: The Evolving Journey of Solution Selling",
            "link": "challenger_chapter_1",
        },
        {
            "title": "Chapter 2: The Challenger (Part 1): A New Model for High Performance",
            "link": "challenger_chapter_2",
        },
    ],
    "training_philosophy": [
        {
            "title": "Chapter 3: The Challenger (Part 2): Exporting the Model to the Core",
            "link": "challenger_chapter_3",
        },
        {"title": "Chapter 4: Communication Skills", "link": "sell_chapter_4"},
    ],
    "training_frequency": [
        {
            "title": "Chapter 6: Planning Sales Dialogues and Presentations",
            "link": "sell_chapter_6",
        },
        {
            "title": "Chapter 7: Sales Dialogue: Creating and Communicating Value",
            "link": "sell_chapter_7",
        },
    ],
    "break_even": [
        {"title": "Key Concept 2: Break-Even Analysis", "link": "break_even_analysis"},
        {
            "title": "Key Concept 3: Target Profit Analysis",
            "link": "target_profit_analysis",
        },
    ],
}


def analyze_responses(form_data):
    recommended_chapters = []

    if form_data.get("dedicated_scripts") == "No":
        recommended_chapters.extend(chapters["dedicated_scripts"])
    if form_data.get("objection_training") == "No":
        recommended_chapters.extend(chapters["objection_training"])
    if form_data.get("clear_criteria") == "No":
        recommended_chapters.extend(chapters["clear_criteria"])
    if form_data.get("consistent_followup") == "No":
        recommended_chapters.extend(chapters["consistent_followup"])
    if form_data.get("crm_tracking") == "No":
        recommended_chapters.extend(chapters["crm_tracking"])
    if form_data.get("followup_attempts") == "0":
        recommended_chapters.extend(chapters["followup_attempts"])
    if form_data.get("recruiting_system") == "No":
        recommended_chapters.extend(chapters["recruiting_system"])
    if form_data.get("training_philosophy") == "0":
        recommended_chapters.extend(chapters["training_philosophy"])
    if form_data.get("training_frequency") == "0":
        recommended_chapters.extend(chapters["training_frequency"])
    if form_data.get("break_even") == "No":
        recommended_chapters.extend(chapters["break_even"])

    return recommended_chapters


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error_message="Page not found."), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template(
        "error.html",
        error_message="An internal server error occurred. Please try again later.",
    ), 500


@app.route("/sales-assessment")
def sales_assessment():
    print("Serving Sales Assessment.html")
    return render_template("Sales Assessment.html")


# --- Blog Outline Pages ---
@app.route("/blog/challenger")
def blog_challenger_outline():
    return render_template("blog/challenger_outline.html")


@app.route("/blog/sell")
def blog_sell_outline():
    return render_template("blog/sell_outline.html")


@app.route("/blog/cold_to_committed")
def blog_cold_to_committed_outline():
    return render_template("blog/cold_to_committed_outline.html")


@app.route("/blog/hacking_sales")
def blog_hacking_sales_outline():
    return render_template("blog/hacking_sales_outline.html")


@app.route("/blog/sales_eq")
def blog_sales_eq_outline():
    return render_template("blog/sales_eq_outline.html")


@app.route("/blog/break-even-point")
def blog_break_even():
    return render_template("Break even point.html")


# Contact Page
@app.route("/contact")
def contact():
    return render_template("contact.html")


# Privacy Page
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# Privacy Page
@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/get-slots", methods=["GET"])
def slots():
    try:
        # Add debug logging
        app.logger.debug("Fetching slots from Google Apps Script")
        response = requests.get(GOOGLE_APPS_SCRIPT_URL + "?action=getSlots")
        app.logger.debug(f"Response from Google Apps Script: {response.text}")
        return response.json()
    except Exception as e:
        app.logger.error(f"Error fetching slots: {str(e)}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/book-meeting", methods=["POST"])
def book_meeting():
    try:
        data = request.json
        # Forward the booking request to Google Apps Script
        response = requests.post(
            GOOGLE_APPS_SCRIPT_URL, json={"action": "bookMeeting", "data": data}
        )
        return response.json()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# unsubscribe Page
@app.route("/unsubscribe")
def unsubscribe():
    return render_template("unsubscribe.html")


# Route to handle the form submission
@app.route("/unsubscribe/process", methods=["POST"])
def process_unsubscribe():
    try:
        email = request.form.get("email")
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400

        # Save to unsubscribe.txt
        file_path = os.path.join(
            os.path.dirname(__file__), "templates", "unsubscribe.txt"
        )
        with open(file_path, "a") as f:
            f.write(f"{email}\n")

        return jsonify({"success": True, "message": "Unsubscribe successful"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# Robots.txt
@app.route("/robots.txt")
def robots_txt():
    return Response(
        f"User-agent: *\nDisallow:\n\nSitemap: {CANONICAL_BASE_URL}/sitemap.xml",
        status=200,
        mimetype="text/plain",
    )


# --- Book Chapter Routes ---
# Challenger Sale Chapters
@app.route("/blog/challenger_chapter_1")
def challenger_chapter_1():
    return render_template("blog/challenger_chapter_1.html")


@app.route("/blog/challenger_chapter_2")
def challenger_chapter_2():
    return render_template("blog/challenger_chapter_2.html")


@app.route("/blog/challenger_chapter_3")
def challenger_chapter_3():
    return render_template("blog/challenger_chapter_3.html")


@app.route("/blog/challenger_chapter_4")
def challenger_chapter_4():
    return render_template("blog/challenger_chapter_4.html")


@app.route("/blog/challenger_chapter_5")
def challenger_chapter_5():
    return render_template("blog/challenger_chapter_5.html")


@app.route("/blog/challenger_chapter_6")
def challenger_chapter_6():
    return render_template("blog/challenger_chapter_6.html")


@app.route("/blog/challenger_chapter_7")
def challenger_chapter_7():
    return render_template("blog/challenger_chapter_7.html")


@app.route("/blog/challenger_chapter_8")
def challenger_chapter_8():
    return render_template("blog/challenger_chapter_8.html")


@app.route("/blog/challenger_chapter_9")
def challenger_chapter_9():
    return render_template("blog/challenger_chapter_9.html")


# Cold to Committed Chapters
@app.route("/blog/cold_to_committed_chapter_1")
def cold_to_committed_chapter_1():
    return render_template("blog/cold_to_committed_chapter_1.html")


@app.route("/blog/cold_to_committed_chapter_2")
def cold_to_committed_chapter_2():
    return render_template("blog/cold_to_committed_chapter_2.html")


@app.route("/blog/cold_to_committed_chapter_3")
def cold_to_committed_chapter_3():
    return render_template("blog/cold_to_committed_chapter_3.html")


@app.route("/blog/cold_to_committed_chapter_4")
def cold_to_committed_chapter_4():
    return render_template("blog/cold_to_committed_chapter_4.html")


@app.route("/blog/cold_to_committed_chapter_5")
def cold_to_committed_chapter_5():
    return render_template("blog/cold_to_committed_chapter_5.html")


@app.route("/blog/cold_to_committed_chapter_6")
def cold_to_committed_chapter_6():
    return render_template("blog/cold_to_committed_chapter_6.html")


@app.route("/blog/cold_to_committed_chapter_7")
def cold_to_committed_chapter_7():
    return render_template("blog/cold_to_committed_chapter_7.html")


@app.route("/blog/cold_to_committed_chapter_8")
def cold_to_committed_chapter_8():
    return render_template("blog/cold_to_committed_chapter_8.html")


@app.route("/blog/cold_to_committed_chapter_9")
def cold_to_committed_chapter_9():
    return render_template("blog/cold_to_committed_chapter_9.html")


@app.route("/blog/cold_to_committed_chapter_10")
def cold_to_committed_chapter_10():
    return render_template("blog/cold_to_committed_chapter_10.html")


# Hacking Sales Chapters
@app.route("/blog/hacking_sales_chapter_1")
def hacking_sales_chapter_1():
    return render_template("blog/hacking_sales_chapter_1.html")


@app.route("/blog/hacking_sales_chapter_2")
def hacking_sales_chapter_2():
    return render_template("blog/hacking_sales_chapter_2.html")


@app.route("/blog/hacking_sales_chapter_3")
def hacking_sales_chapter_3():
    return render_template("blog/hacking_sales_chapter_3.html")


@app.route("/blog/hacking_sales_chapter_4")
def hacking_sales_chapter_4():
    return render_template("blog/hacking_sales_chapter_4.html")


@app.route("/blog/hacking_sales_chapter_5")
def hacking_sales_chapter_5():
    return render_template("blog/hacking_sales_chapter_5.html")


@app.route("/blog/hacking_sales_chapter_6")
def hacking_sales_chapter_6():
    return render_template("blog/hacking_sales_chapter_6.html")


@app.route("/blog/hacking_sales_chapter_7")
def hacking_sales_chapter_7():
    return render_template("blog/hacking_sales_chapter_7.html")


@app.route("/blog/hacking_sales_chapter_8")
def hacking_sales_chapter_8():
    return render_template("blog/hacking_sales_chapter_8.html")


@app.route("/blog/hacking_sales_chapter_9")
def hacking_sales_chapter_9():
    return render_template("blog/hacking_sales_chapter_9.html")


@app.route("/blog/hacking_sales_chapter_10")
def hacking_sales_chapter_10():
    return render_template("blog/hacking_sales_chapter_10.html")


@app.route("/blog/hacking_sales_chapter_11")
def hacking_sales_chapter_11():
    return render_template("blog/hacking_sales_chapter_11.html")


@app.route("/blog/hacking_sales_chapter_12")
def hacking_sales_chapter_12():
    return render_template("blog/hacking_sales_chapter_12.html")


@app.route("/blog/hacking_sales_chapter_13")
def hacking_sales_chapter_13():
    return render_template("blog/hacking_sales_chapter_13.html")


@app.route("/blog/hacking_sales_chapter_14")
def hacking_sales_chapter_14():
    return render_template("blog/hacking_sales_chapter_14.html")


# Sell Chapters
@app.route("/blog/sell_chapter_1")
def sell_chapter_1():
    return render_template("blog/sell_chapter_1.html")


@app.route("/blog/sell_chapter_2")
def sell_chapter_2():
    return render_template("blog/sell_chapter_2.html")


@app.route("/blog/sell_chapter_3")
def sell_chapter_3():
    return render_template("blog/sell_chapter_3.html")


@app.route("/blog/sell_chapter_4")
def sell_chapter_4():
    return render_template("blog/sell_chapter_4.html")


@app.route("/blog/sell_chapter_5")
def sell_chapter_5():
    return render_template("blog/sell_chapter_5.html")


@app.route("/blog/sell_chapter_6")
def sell_chapter_6():
    return render_template("blog/sell_chapter_6.html")


@app.route("/blog/sell_chapter_7")
def sell_chapter_7():
    return render_template("blog/sell_chapter_7.html")


@app.route("/blog/sell_chapter_8")
def sell_chapter_8():
    return render_template("blog/sell_chapter_8.html")


@app.route("/blog/sell_chapter_9")
def sell_chapter_9():
    return render_template("blog/sell_chapter_9.html")


@app.route("/blog/sell_chapter_10")
def sell_chapter_10():
    return render_template("blog/sell_chapter_10.html")


# Sales EQ Chapters
@app.route("/blog/sales_eq_chapter_1")
def sales_eq_chapter_1():
    return render_template("blog/sales_eq_chapter_1.html")


@app.route("/blog/sales_eq_chapter_2")
def sales_eq_chapter_2():
    return render_template("blog/sales_eq_chapter_2.html")


@app.route("/blog/sales_eq_chapter_3")
def sales_eq_chapter_3():
    return render_template("blog/sales_eq_chapter_3.html")


@app.route("/blog/sales_eq_chapter_4")
def sales_eq_chapter_4():
    return render_template("blog/sales_eq_chapter_4.html")


@app.route("/blog/sales_eq_chapter_5")
def sales_eq_chapter_5():
    return render_template("blog/sales_eq_chapter_5.html")


@app.route("/blog/sales_eq_chapter_6")
def sales_eq_chapter_6():
    return render_template("blog/sales_eq_chapter_6.html")


@app.route("/blog/sales_eq_chapter_7")
def sales_eq_chapter_7():
    return render_template("blog/sales_eq_chapter_7.html")


@app.route("/blog/sales_eq_chapter_8")
def sales_eq_chapter_8():
    return render_template("blog/sales_eq_chapter_8.html")


@app.route("/blog/sales_eq_chapter_9")
def sales_eq_chapter_9():
    return render_template("blog/sales_eq_chapter_9.html")


@app.route("/blog/sales_eq_chapter_10")
def sales_eq_chapter_10():
    return render_template("blog/sales_eq_chapter_10.html")


@app.route("/blog/sales_eq_chapter_11")
def sales_eq_chapter_11():
    return render_template("blog/sales_eq_chapter_11.html")


@app.route("/blog/sales_eq_chapter_12")
def sales_eq_chapter_12():
    return render_template("blog/sales_eq_chapter_12.html")


@app.route("/blog/sales_eq_chapter_13")
def sales_eq_chapter_13():
    return render_template("blog/sales_eq_chapter_13.html")


@app.route("/blog/sales_eq_chapter_14")
def sales_eq_chapter_14():
    return render_template("blog/sales_eq_chapter_14.html")


@app.route("/blog/sales_eq_chapter_15")
def sales_eq_chapter_15():
    return render_template("blog/sales_eq_chapter_15.html")


@app.route("/blog/sales_eq_chapter_16")
def sales_eq_chapter_16():
    return render_template("blog/sales_eq_chapter_16.html")


@app.route("/blog/sales_eq_chapter_17")
def sales_eq_chapter_17():
    return render_template("blog/sales_eq_chapter_17.html")


@app.route("/blog/sales_eq_chapter_18")
def sales_eq_chapter_18():
    return render_template("blog/sales_eq_chapter_18.html")


@app.route("/blog/sales_eq_chapter_19")
def sales_eq_chapter_19():
    return render_template("blog/sales_eq_chapter_19.html")


@app.route("/blog/sales_eq_chapter_20")
def sales_eq_chapter_20():
    return render_template("blog/sales_eq_chapter_20.html")


@app.route("/blog/sales_eq_chapter_21")
def sales_eq_chapter_21():
    return render_template("blog/sales_eq_chapter_21.html")


@app.route("/blog/sales_eq_chapter_22")
def sales_eq_chapter_22():
    return render_template("blog/sales_eq_chapter_22.html")


@app.route("/blog/sales_eq_chapter_23")
def sales_eq_chapter_23():
    return render_template("blog/sales_eq_chapter_23.html")


@app.route("/blog/sales_eq_chapter_24")
def sales_eq_chapter_24():
    return render_template("blog/sales_eq_chapter_24.html")


@app.route("/blog/sales_eq_chapter_25")
def sales_eq_chapter_25():
    return render_template("blog/sales_eq_chapter_25.html")


@app.route("/blog/sales_eq_chapter_26")
def sales_eq_chapter_26():
    return render_template("blog/sales_eq_chapter_26.html")


@app.route("/blog/sales_eq_chapter_27")
def sales_eq_chapter_27():
    return render_template("blog/sales_eq_chapter_27.html")


@app.route("/blog/sales_eq_chapter_28")
def sales_eq_chapter_28():
    return render_template("blog/sales_eq_chapter_28.html")


@app.route("/blog/sales_eq_chapter_29")
def sales_eq_chapter_29():
    return render_template("blog/sales_eq_chapter_29.html")


# Sitemap Route
@app.route("/sitemap.xml")
def sitemap_xml():
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
    urls = []

    for rule in app.url_map.iter_rules():
        if (
            rule.endpoint in ignored_endpoints
            or "GET" not in rule.methods
            or rule.arguments
        ):
            continue
        if rule.rule.startswith("/.well-known"):
            continue
        urls.append(rule.rule)

    unique_urls = sorted(set(urls), key=lambda path: (path != "/", path))
    url_entries = "\n".join(
        f"  <url><loc>{escape(CANONICAL_BASE_URL + path)}</loc></url>"
        for path in unique_urls
    )
    sitemap_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{url_entries}\n"
        "</urlset>"
    )
    return Response(sitemap_content, status=200, mimetype="application/xml")


if __name__ == "__main__":
    app.run(debug=True)
