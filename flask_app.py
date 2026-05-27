### Complete Flask Application Code with Updated Function:

from flask import Flask, request, render_template, redirect, url_for, session, abort,Response,jsonify, request, send_from_directory
import logging
import secrets
import math
import json
import os
import requests
from datetime import datetime,timedelta

GOOGLE_APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxveq1SuTzj9PPBF5BKgFwF5DxHs7BmLLXLQPL8yV00Ryb9ORjT_K185Q7itjvgvVAm/exec'

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

# Route for the new DispatchAI Landing Page
@app.route('/DispatchAI')
def DispatchAI():
    return render_template('DispatchAI.html')

@app.route('/dispatchai')
def dispatchai():
    return render_template('DispatchAI.html')

@app.route('/lastcall')
def lastcall():
    return render_template('LastCall.html')

@app.route('/LastCall')
def LastCall():
    return render_template('LastCall.html')


def should_refresh_slots():
    """Check if slots should be refreshed based on last update time"""
    last_update = session.get('slots_last_update')
    if not last_update:
        return True

    last_update = datetime.fromisoformat(last_update)
    return datetime.now() - last_update > timedelta(minutes=15)  # Refresh every 15 minutes

def fetch_available_slots():
    """Fetch available time slots and store in session"""
    if not should_refresh_slots():
        return

    try:
        response = requests.get(GOOGLE_APPS_SCRIPT_URL + '?action=getSlots')
        available_slots = response.json()
        session['available_slots'] = available_slots
        session['slots_last_update'] = datetime.now().isoformat()
    except Exception as e:
        if 'available_slots' not in session:
            session['available_slots'] = {'success': False, 'error': str(e)}

def log_session_data(step):
    """Logs the current session data."""
    data = session.get("data", {})
    logging.info(f"Session data at {step}: {json.dumps(data, indent=4)}")

def create_data_dictionary():
    """Creates a dictionary with all necessary keys."""
    return {
        'price_per_unit': None,
        'variable_cost_per_unit': None,
        'ae_commission_rate': None,
        'commission_per_meeting': None,
        'avg_units_per_order': None,
        'total_revenue_per_order': None,
        'variable_cost_per_order': None,
        'best_cold_call_to_lead': None,
        'best_lead_to_qualified': None,
        'best_qualified_to_client': None,
        'worst_cold_call_to_lead': None,
        'worst_lead_to_qualified': None,
        'worst_qualified_to_client': None,
        'best_cold_calls_needed': None,
        'worst_cold_calls_needed': None,
        'num_ae': None,
        'avg_salary_ae': None,
        'annual_benefits_ae': None,
        'sales_team_overhead': None,
        'company_fixed_costs': None,
        'cold_calls_per_sdr_per_week': None,
        'avg_salary_sdr': None,
        'annual_benefits_sdr': None,
        'num_sdrs':1,
        'sdr_cost_per_closed_deal_best': None,
        'sdr_cost_per_closed_deal_worst': None,
        'total_variable_cost_internal_best': None,
        'total_variable_cost_internal_worst': None,
        'total_contribution_margin_internal_best': None,
        'total_contribution_margin_internal_worst': None,
        'break_even_orders_internal_best': None,
        'break_even_orders_internal_worst': None,
        'sales_needed_for_100k': None,
        'sales_needed_for_1M': None,
        # Add the new variables here
        'num_sdrs_best_internal': None,
        'break_even_orders_best_internal': None,
        'num_sdrs_worst_internal': None,
        'break_even_orders_worst_internal': None,
        'num_sdrs_best_urxion': None,
        'break_even_orders_best_urxion': None,
        'num_sdrs_worst_urxion': None,
        'break_even_orders_worst_urxion': None,
        'urxion_commission_per_meeting': 75, # You'll need to define this somewhere, maybe ask for it in step 1
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

@app.route('/.well-known/microsoft-identity-association')
def serve_ms_identity():
    return send_from_directory(
        os.path.join(app.root_path, 'templates', '.well-known'),
        'microsoft-identity-association.json',
        mimetype='application/json'
    )
@app.route('/.well-known/microsoft-identity-association.json')
def serve_ms_identity2():
    return send_from_directory(
        os.path.join(app.root_path, 'templates', '.well-known'),
        'microsoft-identity-association.json',
        mimetype='application/json'
    )

# Centralized input validation function
def validate_positive_inputs(data, fields):
    return all(data[field] > 0 for field in fields)


# --- Step 1 ---
@app.route('/step_1', methods=['GET', 'POST'])
def step_1():
    if 'data' not in session:
        session['data'] = create_data_dictionary()

    if request.method == 'POST':
        data = session['data']
        try:
            price_per_unit = float(request.form['price_per_unit'])
            variable_cost_per_unit = float(request.form['variable_cost_per_unit'])
            ae_commission_rate = float(request.form['ae_commission_rate'])
            commission_per_meeting = float(request.form['commission_per_meeting'])
            avg_units_per_order = float(request.form['avg_units_per_order'])

            # Input validation
            if validate_positive_inputs(locals(), ['price_per_unit', 'variable_cost_per_unit', 'ae_commission_rate', 'commission_per_meeting', 'avg_units_per_order']):
                data.update({
                    'price_per_unit': price_per_unit,
                    'variable_cost_per_unit': variable_cost_per_unit,
                    'ae_commission_rate': ae_commission_rate,
                    'commission_per_meeting': commission_per_meeting,
                    'avg_units_per_order': avg_units_per_order
                })
                data['total_revenue_per_order'] = data['price_per_unit'] * data['avg_units_per_order']
                data['variable_cost_per_order'] = (
                    data['variable_cost_per_unit'] * data['avg_units_per_order'] +
                    (data['ae_commission_rate'] / 100) * data['total_revenue_per_order']
                )
                session['data'] = data
                log_session_data('step_1')
                return redirect(url_for('step_2'))
            else:
                logging.warning("Input validation failed: All input values must be positive.")
                return render_template('step_1.html', error_message="All input values must be positive.")

        except ValueError:
            return render_template('step_1.html', error_message="Invalid input. Please enter numeric values.")

    return render_template('step_1.html', **session.get('data', {}))

# --- Step 2 ---
@app.route('/step_2', methods=['GET', 'POST'])
def step_2():
    if request.method == 'POST':
        data = session['data']
        try:
            # Collect conversion rates
            for key in ['best_cold_call_to_lead', 'best_lead_to_qualified', 'best_qualified_to_client',
                         'worst_cold_call_to_lead', 'worst_lead_to_qualified', 'worst_qualified_to_client']:
                data[key] = float(request.form[key]) / 100

            # Input validation for conversion rates
            if not validate_positive_inputs(data, ['best_cold_call_to_lead', 'best_lead_to_qualified', 'best_qualified_to_client',
                                                    'worst_cold_call_to_lead', 'worst_lead_to_qualified', 'worst_qualified_to_client']):
                logging.error("Conversion rates must be greater than zero.")
                return render_template('step_2.html', error_message="Conversion rates must be greater than zero.")

            # Calculate activities needed per stage
            for key in ['best', 'worst']:
                data[f'{key}_cold_calls_per_lead'] = 1 / data[f'{key}_cold_call_to_lead']
                data[f'{key}_leads_per_qualified'] = 1 / data[f'{key}_lead_to_qualified']
                data[f'{key}_qualified_per_client'] = 1 / data[f'{key}_qualified_to_client']
                data[f'{key}_cold_calls_needed'] = (
                    data[f'{key}_cold_calls_per_lead'] *
                    data[f'{key}_leads_per_qualified'] *
                    data[f'{key}_qualified_per_client']
                )

            # Ensure SDR cost per closed deal calculation
            data['sdr_cost_per_closed_deal_best'] = data['commission_per_meeting'] * data['best_qualified_per_client']
            data['sdr_cost_per_closed_deal_worst'] = data['commission_per_meeting'] * data['worst_qualified_per_client']

            session['data'] = data
            log_session_data('step_2')
            return redirect(url_for('step_3'))

        except ValueError:
            return render_template('step_2.html', error_message="Invalid input. Please enter numeric values.")

    return render_template('step_2.html', **session.get('data', {}))


@app.route('/step_3', methods=['GET', 'POST'])
def step_3():
    if request.method == 'POST':
        data = session.get('data', {})
        try:
            # Get input values from the form
            # Removed default values for variables that were already calculated
            data['num_ae'] = int(float(request.form['num_ae']))
            data['avg_salary_ae'] = float(request.form['avg_salary_ae'])
            data['annual_benefits_ae'] = float(request.form['annual_benefits_ae'])
            data['sales_team_overhead'] = float(request.form['sales_team_overhead'])
            data['company_fixed_costs'] = float(request.form['company_fixed_costs'])
            data['cold_calls_per_sdr_per_week'] = float(request.form['cold_calls_per_sdr_per_week'])
            data['avg_salary_sdr'] = float(request.form['avg_salary_sdr'])
            data['annual_benefits_sdr'] = float(request.form['annual_benefits_sdr'])

            # Do not overwrite calculated values with defaults
            # Ensure these values are pulled from previous steps instead
            if 'price_per_unit' not in data or data['price_per_unit'] is None:
                return render_template('step_3.html', error_message="Missing price per unit.")
            if 'variable_cost_per_order' not in data or data['variable_cost_per_order'] is None:
                return render_template('step_3.html', error_message="Missing variable cost per order.")
            if 'total_revenue_per_order' not in data or data['total_revenue_per_order'] is None:
                return render_template('step_3.html', error_message="Missing total revenue per order.")

            # Log session data after collecting inputs
            logging.debug("Session Data:")
            for key, value in data.items():
                logging.debug(f"{key}: {value}")

            # Validate inputs
            input_fields = [
                'num_ae', 'avg_salary_ae', 'annual_benefits_ae',
                'sales_team_overhead', 'company_fixed_costs',
                'cold_calls_per_sdr_per_week', 'avg_salary_sdr',
                'annual_benefits_sdr'
            ]
            if not validate_positive_inputs(data, input_fields):
                logging.warning("Validation failed: All input values must be positive.")
                return render_template('step_3.html', error_message="All input values must be positive.")

            # Check for required prior calculations
            required_fields = ['sdr_cost_per_closed_deal_best', 'sdr_cost_per_closed_deal_worst', 'urxion_commission_per_meeting']
            if any(field not in data or data[field] is None for field in required_fields):
                logging.error("Missing calculated values: " + ", ".join(required_fields))
                return render_template('step_3.html', error_message="Required calculations are missing.")

            urxion_commission_per_meeting = data['urxion_commission_per_meeting']
            sdr_capacity_per_year = data['cold_calls_per_sdr_per_week'] * 52
            profit_target = 100000  # Specify your profit target for calculations

            # --- Best Internal Scenario ---
            bi_num_sdrs = 1
            bi_break_even_orders = None  # Initialize bi_break_even_orders
            max_iterations = 100
            for _ in range(max_iterations):
                bi_total_fixed_costs = (
                    bi_num_sdrs * (data['avg_salary_sdr'] + data['annual_benefits_sdr']) +
                    data['num_ae'] * (data['avg_salary_ae'] + data['annual_benefits_ae']) +
                    data['sales_team_overhead'] + data['company_fixed_costs']
                )

                bi_total_variable_cost = data['variable_cost_per_order'] + data['sdr_cost_per_closed_deal_best']
                # Ensure we use the correct revenue from previous steps
                bi_total_contribution_margin = data['total_revenue_per_order'] - bi_total_variable_cost

                if bi_total_contribution_margin <= 0:
                    logging.error("Total contribution margin cannot be zero or negative.")
                    bi_break_even_orders = None  # Set to None if contribution margin is invalid
                    break

                bi_break_even_orders = (profit_target + bi_total_fixed_costs) / bi_total_contribution_margin

                bi_total_cold_calls_needed = bi_break_even_orders * data['best_cold_calls_needed']
                new_bi_num_sdrs = math.ceil(bi_total_cold_calls_needed / sdr_capacity_per_year)

                # Check for convergence
                if new_bi_num_sdrs == bi_num_sdrs:
                    break
                bi_num_sdrs = new_bi_num_sdrs

            # Store Best Internal Scenario Results
            data['num_sdrs_best_internal'] = bi_num_sdrs
            data['break_even_orders_internal_best'] = bi_break_even_orders  # Safely assign
            data['total_fixed_costs_best_internal'] = bi_total_fixed_costs
            data['total_variable_cost_internal_best'] = bi_total_variable_cost
            data['total_contribution_margin_internal_best'] = bi_total_contribution_margin

            # Calculate Break-Even Leads and Sales
            data['break_even_leads_internal_best'] = data['best_leads_per_qualified'] * (bi_break_even_orders if bi_break_even_orders else 0)
            data['break_even_sales_internal_best'] = (bi_break_even_orders * data['price_per_unit']) if bi_break_even_orders else 0

            logging.debug(f"Best Internal Scenario - Num SDRs: {bi_num_sdrs}, Break Even Orders: {bi_break_even_orders}")

            # --- Worst Internal Scenario ---
            wi_num_sdrs = 1
            wi_break_even_orders = None

            for _ in range(max_iterations):
                wi_total_fixed_costs = (
                    wi_num_sdrs * (data['avg_salary_sdr'] + data['annual_benefits_sdr']) +
                    data['num_ae'] * (data['avg_salary_ae'] + data['annual_benefits_ae']) +
                    data['sales_team_overhead'] + data['company_fixed_costs']
                )

                wi_total_variable_cost = data['variable_cost_per_order'] + data['sdr_cost_per_closed_deal_worst']
                # Ensure we use the correct revenue from previous steps
                wi_total_contribution_margin = data['total_revenue_per_order'] - wi_total_variable_cost

                if wi_total_contribution_margin <= 0:
                    logging.error("Total contribution margin cannot be zero or negative.")
                    wi_break_even_orders = None  # Set to None if contribution margin is invalid
                    break

                wi_break_even_orders = (profit_target + wi_total_fixed_costs) / wi_total_contribution_margin

                wi_total_cold_calls_needed = wi_break_even_orders * data['worst_cold_calls_needed']
                new_wi_num_sdrs = math.ceil(wi_total_cold_calls_needed / sdr_capacity_per_year)

                # Check for convergence
                if new_wi_num_sdrs == wi_num_sdrs:
                    break
                wi_num_sdrs = new_wi_num_sdrs

            # Store Worst Internal Scenario Results
            data['num_sdrs_worst_internal'] = wi_num_sdrs
            data['break_even_orders_internal_worst'] = wi_break_even_orders  # Safely assign
            data['total_fixed_costs_worst_internal'] = wi_total_fixed_costs
            data['total_variable_cost_internal_worst'] = wi_total_variable_cost
            data['total_contribution_margin_internal_worst'] = wi_total_contribution_margin

            # Calculate Break-Even Leads and Sales
            data['break_even_leads_internal_worst'] = data['worst_leads_per_qualified'] * (wi_break_even_orders if wi_break_even_orders else 0)
            data['break_even_sales_internal_worst'] = (wi_break_even_orders * data['price_per_unit']) if wi_break_even_orders else 0

            logging.debug(f"Worst Internal Scenario - Num SDRs: {wi_num_sdrs}, Break Even Orders: {wi_break_even_orders}")

            # --- Best Urxion Scenario ---
            bu_num_sdrs = 0  # Assumes no SDRs needed for Urxion
            bu_total_fixed_costs = (
                data['num_ae'] * (data['avg_salary_ae'] + data['annual_benefits_ae']) +
                data['sales_team_overhead'] + data['company_fixed_costs']
            )
            bu_total_variable_cost = data['variable_cost_per_order'] + (urxion_commission_per_meeting * data['best_qualified_per_client'])
            # Ensure we use the correct revenue from previous steps
            bu_total_contribution_margin = data['total_revenue_per_order'] - bu_total_variable_cost

            if bu_total_contribution_margin <= 0:
                logging.error("Urxion Best Case Contribution margin cannot be zero or negative.")
                bu_break_even_orders = None
            else:
                bu_break_even_orders = (profit_target + bu_total_fixed_costs) / bu_total_contribution_margin

            # Store Best Urxion Scenario Results
            data['num_sdrs_best_urxion'] = bu_num_sdrs
            data['break_even_orders_best_urxion'] = bu_break_even_orders
            data['break_even_leads_urxion_best'] = data['best_leads_per_qualified'] * (bu_break_even_orders if bu_break_even_orders else 0)
            data['break_even_sales_urxion_best'] = (bu_break_even_orders * data['price_per_unit']) if bu_break_even_orders else 0

            logging.debug(f"Best Urxion Scenario - Num SDRs: {bu_num_sdrs}, Break Even Orders: {bu_break_even_orders}")

            # --- Worst Urxion Scenario ---
            wu_num_sdrs = 0  # Assumes no SDRs needed for Urxion
            wu_total_fixed_costs = (
                data['num_ae'] * (data['avg_salary_ae'] + data['annual_benefits_ae']) +
                data['sales_team_overhead'] + data['company_fixed_costs']
            )
            wu_total_variable_cost = data['variable_cost_per_order'] + (urxion_commission_per_meeting * data['worst_qualified_per_client'])
            # Ensure we use the correct revenue from previous steps
            wu_total_contribution_margin = data['total_revenue_per_order'] - wu_total_variable_cost

            if wu_total_contribution_margin <= 0:
                logging.error("Urxion Worst Case Contribution margin cannot be zero or negative.")
                wu_break_even_orders = None
            else:
                wu_break_even_orders = (profit_target + wu_total_fixed_costs) / wu_total_contribution_margin

            # Store Worst Urxion Scenario Results
            data['num_sdrs_worst_urxion'] = wu_num_sdrs
            data['break_even_orders_worst_urxion'] = wu_break_even_orders
            data['break_even_leads_urxion_worst'] = data['worst_leads_per_qualified'] * (wu_break_even_orders if wu_break_even_orders else 0)
            data['break_even_sales_urxion_worst'] = (wu_break_even_orders * data['price_per_unit']) if wu_break_even_orders else 0

            logging.debug(f"Worst Urxion Scenario - Num SDRs: {wu_num_sdrs}, Break Even Orders: {wu_break_even_orders}")

            # --- Profit Target Analysis ---
            # Assuming you want to calculate for $100k and $1M profit targets
            profit_targets = [100000, 1000000]
            for target in profit_targets:
                # Best Internal
                bi_break_even_orders_target = (target + data['total_fixed_costs_best_internal']) / data['total_contribution_margin_internal_best'] if data['total_contribution_margin_internal_best'] > 0 else None
                data[f'sales_needed_for_{int(target/1000)}k_internal_best'] = (bi_break_even_orders_target * data['price_per_unit']) if bi_break_even_orders_target else 0

                # Worst Internal
                wi_break_even_orders_target = (target + data['total_fixed_costs_worst_internal']) / data['total_contribution_margin_internal_worst'] if data['total_contribution_margin_internal_worst'] > 0 else None
                data[f'sales_needed_for_{int(target/1000)}k_internal_worst'] = (wi_break_even_orders_target * data['price_per_unit']) if wi_break_even_orders_target else 0

                # Best Urxion
                bu_break_even_orders_target = (target + bu_total_fixed_costs) / bu_total_contribution_margin if bu_total_contribution_margin > 0 else None
                data[f'sales_needed_for_{int(target/1000)}k_urxion_best'] = (bu_break_even_orders_target * data['price_per_unit']) if bu_break_even_orders_target else 0

                # Worst Urxion
                wu_break_even_orders_target = (target + wu_total_fixed_costs) / wu_total_contribution_margin if wu_total_contribution_margin > 0 else None
                data[f'sales_needed_for_{int(target/1000)}k_urxion_worst'] = (wu_break_even_orders_target * data['price_per_unit']) if wu_break_even_orders_target else 0

            logging.debug("Profit Target Analysis Calculated.")

            # Save updated data back to the session
            session['data'] = data
            log_session_data('step_3')
            return redirect(url_for('step_4'))

        except (ValueError, KeyError) as e:
            logging.error(f"Error in Step 3: {e}")
            return render_template('step_3.html', error_message="Please check your input. Errors may be due to missing data.")

    return render_template('step_3.html', **session.get('data', {}))

# --- Step 4 ---
@app.route('/step_4', methods=['GET'])
def step_4():
    data = session.get('data', {})
    formatted_data = {}

    # Prepare formatted data for HTML display
    for key, value in data.items():
        if value is None:
            formatted_data[key] = "N/A"  # Use "N/A" for NoneType values
        else:
            formatted_data[key] = "{:,.2f}".format(value)  # Format numbers

    return render_template('step_4.html', **formatted_data)

# --- Additional Steps ---
@app.route('/step_5', methods=['GET'])
def step_5():
    data = session.get('data', {})
    formatted_data = {key: "{:,.2f}".format(value) for key, value in data.items()}
    return render_template('step_5.html', **formatted_data)

@app.route('/step_6', methods=['GET'])
def step_6():
    data = session.get('data', {})
    formatted_data = {key: "{:,.2f}".format(value) for key, value in data.items()}
    return render_template('step_6.html', **formatted_data)

# Custom filter for formatting numbers
@app.template_filter('format_number')
def format_number_filter(value):
    return "{:,.2f}".format(value) if isinstance(value, (int, float)) else value

####################################################

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/defaultsite')
def defaultsite():
    return render_template('index.html')


# Services Page
@app.route('/services')
def services():
    return redirect(url_for('cold_calling'))

# Cold Calling Page
@app.route('/cold-calling-that-converts')
def cold_calling():
    return render_template('Cold Calling That Converts.html')

# Business Assessment Page
@app.route('/business-assessment')
def business_assessment():
    return render_template('Business Assessment.html')

# Cold Calling Assessment Page
@app.route('/cold-calling-assessment')
def cold_calling_assessment():
    return render_template('Cold Calling Assessment.html')

# Book Reviews Page
@app.route('/Knowledge-is-Power', endpoint='knowledge_is_power')
def knowledge_is_power():
    return render_template('Knowledge is Power.html')

# Demo Page
@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/cold-calling-results', methods=['POST'])
def cold_calling_results():
    form_data = request.form
    recommended_chapters = analyze_responses(form_data)
    return render_template('results.html', chapters=recommended_chapters)

# Define the chapters and their relevance to different topics
chapters = {
    "dedicated_scripts": [
        {"title": "Chapter 5: Strategic Prospecting and Preparing for Sales Dialogue", "link": "sell_chapter_5"},
        {"title": "Chapter 6: Planning Sales Dialogues and Presentations", "link": "sell_chapter_6"},
    ],
    "objection_training": [
        {"title": "Chapter 7: Overcoming Objections", "link": "cold_to_committed_chapter_7"},
        {"title": "Chapter 27: Turning Around Objections", "link": "sales_eq_chapter_27"},
    ],
    "clear_criteria": [
        {"title": "Chapter 3: Understanding Buyers", "link": "sell_chapter_3"},
        {"title": "Chapter 5: Strategic Prospecting and Preparing for Sales Dialogue", "link": "sell_chapter_5"},
    ],
    "consistent_followup": [
        {"title": "Chapter 9: Expanding Customer Relationships", "link": "sell_chapter_9"},
        {"title": "Chapter 10: Adding Value: Self-Leadership and Teamwork", "link": "sell_chapter_10"},
    ],
    "crm_tracking": [
        {"title": "Chapter 4: Communication Skills", "link": "sell_chapter_4"},
        {"title": "Chapter 6: Planning Sales Dialogues and Presentations", "link": "sell_chapter_6"},
    ],
    "followup_attempts": [
        {"title": "Chapter 8: Addressing Concerns and Earning Commitment", "link": "sell_chapter_8"},
        {"title": "Chapter 9: Expanding Customer Relationships", "link": "sell_chapter_9"},
    ],
    "recruiting_system": [
        {"title": "Chapter 1: The Evolving Journey of Solution Selling", "link": "challenger_chapter_1"},
        {"title": "Chapter 2: The Challenger (Part 1): A New Model for High Performance", "link": "challenger_chapter_2"},
    ],
    "training_philosophy": [
        {"title": "Chapter 3: The Challenger (Part 2): Exporting the Model to the Core", "link": "challenger_chapter_3"},
        {"title": "Chapter 4: Communication Skills", "link": "sell_chapter_4"},
    ],
    "training_frequency": [
        {"title": "Chapter 6: Planning Sales Dialogues and Presentations", "link": "sell_chapter_6"},
        {"title": "Chapter 7: Sales Dialogue: Creating and Communicating Value", "link": "sell_chapter_7"},
    ],
    "break_even": [
        {"title": "Key Concept 2: Break-Even Analysis", "link": "break_even_analysis"},
        {"title": "Key Concept 3: Target Profit Analysis", "link": "target_profit_analysis"},
    ],
}

def analyze_responses(form_data):
    recommended_chapters = []

    if form_data.get('dedicated_scripts') == 'No':
        recommended_chapters.extend(chapters['dedicated_scripts'])
    if form_data.get('objection_training') == 'No':
        recommended_chapters.extend(chapters['objection_training'])
    if form_data.get('clear_criteria') == 'No':
        recommended_chapters.extend(chapters['clear_criteria'])
    if form_data.get('consistent_followup') == 'No':
        recommended_chapters.extend(chapters['consistent_followup'])
    if form_data.get('crm_tracking') == 'No':
        recommended_chapters.extend(chapters['crm_tracking'])
    if form_data.get('followup_attempts') == '0':
        recommended_chapters.extend(chapters['followup_attempts'])
    if form_data.get('recruiting_system') == 'No':
        recommended_chapters.extend(chapters['recruiting_system'])
    if form_data.get('training_philosophy') == '0':
        recommended_chapters.extend(chapters['training_philosophy'])
    if form_data.get('training_frequency') == '0':
        recommended_chapters.extend(chapters['training_frequency'])
    if form_data.get('break_even') == 'No':
        recommended_chapters.extend(chapters['break_even'])

    return recommended_chapters










@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_message="Page not found."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_message="An internal server error occurred. Please try again later."), 500

@app.route('/sales-assessment')
def sales_assessment():
    print("Serving Sales Assessment.html")
    return render_template('Sales Assessment.html')

#--- Blog Outline Pages ---
@app.route('/blog/challenger')
def blog_challenger_outline():
    return render_template('blog/challenger_outline.html')

@app.route('/blog/sell')
def blog_sell_outline():
    return render_template('blog/sell_outline.html')

@app.route('/blog/cold_to_committed')
def blog_cold_to_committed_outline():
    return render_template('blog/cold_to_committed_outline.html')

@app.route('/blog/hacking_sales')
def blog_hacking_sales_outline():
    return render_template('blog/hacking_sales_outline.html')

@app.route('/blog/sales_eq')
def blog_sales_eq_outline():
    return render_template('blog/sales_eq_outline.html')

@app.route('/blog/break-even-point')
def blog_break_even():
    return render_template('Break even point.html')

#Contact Page
@app.route('/contact')
def contact():
    return render_template('contact.html')

#Privacy Page
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

#Privacy Page
@app.route('/terms')
def terms():
    return render_template('terms.html')



@app.route('/get-slots', methods=['GET'])
def slots():
    try:
        # Add debug logging
        app.logger.debug('Fetching slots from Google Apps Script')
        response = requests.get(GOOGLE_APPS_SCRIPT_URL + '?action=getSlots')
        app.logger.debug(f'Response from Google Apps Script: {response.text}')
        return response.json()
    except Exception as e:
        app.logger.error(f'Error fetching slots: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/book-meeting', methods=['POST'])
def book_meeting():
    try:
        data = request.json
        # Forward the booking request to Google Apps Script
        response = requests.post(
            GOOGLE_APPS_SCRIPT_URL,
            json={
                'action': 'bookMeeting',
                'data': data
            }
        )
        return response.json()
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


#unsubscribe Page
@app.route('/unsubscribe')
def unsubscribe():
    return render_template('unsubscribe.html')

# Route to handle the form submission
@app.route('/unsubscribe/process', methods=['POST'])
def process_unsubscribe():
    try:
        email = request.form.get('email')
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        # Save to unsubscribe.txt
        file_path = os.path.join(os.path.dirname(__file__), 'templates', 'unsubscribe.txt')
        with open(file_path, 'a') as f:
            f.write(f"{email}\n")

        return jsonify({'success': True, 'message': 'Unsubscribe successful'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

#Robots.txt
@app.route('/robots.txt')
def robots_txt():
    return Response("User-agent: *\nDisallow:\n\nSitemap: http://www.urxion.com/sitemap.xml",status=200, mimetype="text/plain")

#--- Book Chapter Routes ---
#Challenger Sale Chapters
@app.route('/blog/challenger_chapter_1')
def challenger_chapter_1():
    return render_template('blog/challenger_chapter_1.html')

@app.route('/blog/challenger_chapter_2')
def challenger_chapter_2():
    return render_template('blog/challenger_chapter_2.html')

@app.route('/blog/challenger_chapter_3')
def challenger_chapter_3():
    return render_template('blog/challenger_chapter_3.html')

@app.route('/blog/challenger_chapter_4')
def challenger_chapter_4():
    return render_template('blog/challenger_chapter_4.html')

@app.route('/blog/challenger_chapter_5')
def challenger_chapter_5():
    return render_template('blog/challenger_chapter_5.html')

@app.route('/blog/challenger_chapter_6')
def challenger_chapter_6():
    return render_template('blog/challenger_chapter_6.html')

@app.route('/blog/challenger_chapter_7')
def challenger_chapter_7():
    return render_template('blog/challenger_chapter_7.html')

@app.route('/blog/challenger_chapter_8')
def challenger_chapter_8():
    return render_template('blog/challenger_chapter_8.html')

@app.route('/blog/challenger_chapter_9')
def challenger_chapter_9():
    return render_template('blog/challenger_chapter_9.html')

#Cold to Committed Chapters
@app.route('/blog/cold_to_committed_chapter_1')
def cold_to_committed_chapter_1():
    return render_template('blog/cold_to_committed_chapter_1.html')

@app.route('/blog/cold_to_committed_chapter_2')
def cold_to_committed_chapter_2():
    return render_template('blog/cold_to_committed_chapter_2.html')

@app.route('/blog/cold_to_committed_chapter_3')
def cold_to_committed_chapter_3():
    return render_template('blog/cold_to_committed_chapter_3.html')

@app.route('/blog/cold_to_committed_chapter_4')
def cold_to_committed_chapter_4():
    return render_template('blog/cold_to_committed_chapter_4.html')

@app.route('/blog/cold_to_committed_chapter_5')
def cold_to_committed_chapter_5():
    return render_template('blog/cold_to_committed_chapter_5.html')

@app.route('/blog/cold_to_committed_chapter_6')
def cold_to_committed_chapter_6():
    return render_template('blog/cold_to_committed_chapter_6.html')

@app.route('/blog/cold_to_committed_chapter_7')
def cold_to_committed_chapter_7():
    return render_template('blog/cold_to_committed_chapter_7.html')

@app.route('/blog/cold_to_committed_chapter_8')
def cold_to_committed_chapter_8():
    return render_template('blog/cold_to_committed_chapter_8.html')

@app.route('/blog/cold_to_committed_chapter_9')
def cold_to_committed_chapter_9():
    return render_template('blog/cold_to_committed_chapter_9.html')

@app.route('/blog/cold_to_committed_chapter_10')
def cold_to_committed_chapter_10():
    return render_template('blog/cold_to_committed_chapter_10.html')

#Hacking Sales Chapters
@app.route('/blog/hacking_sales_chapter_1')
def hacking_sales_chapter_1():
    return render_template('blog/hacking_sales_chapter_1.html')

@app.route('/blog/hacking_sales_chapter_2')
def hacking_sales_chapter_2():
    return render_template('blog/hacking_sales_chapter_2.html')

@app.route('/blog/hacking_sales_chapter_3')
def hacking_sales_chapter_3():
    return render_template('blog/hacking_sales_chapter_3.html')

@app.route('/blog/hacking_sales_chapter_4')
def hacking_sales_chapter_4():
    return render_template('blog/hacking_sales_chapter_4.html')

@app.route('/blog/hacking_sales_chapter_5')
def hacking_sales_chapter_5():
    return render_template('blog/hacking_sales_chapter_5.html')

@app.route('/blog/hacking_sales_chapter_6')
def hacking_sales_chapter_6():
    return render_template('blog/hacking_sales_chapter_6.html')

@app.route('/blog/hacking_sales_chapter_7')
def hacking_sales_chapter_7():
    return render_template('blog/hacking_sales_chapter_7.html')

@app.route('/blog/hacking_sales_chapter_8')
def hacking_sales_chapter_8():
    return render_template('blog/hacking_sales_chapter_8.html')

@app.route('/blog/hacking_sales_chapter_9')
def hacking_sales_chapter_9():
    return render_template('blog/hacking_sales_chapter_9.html')

@app.route('/blog/hacking_sales_chapter_10')
def hacking_sales_chapter_10():
    return render_template('blog/hacking_sales_chapter_10.html')

@app.route('/blog/hacking_sales_chapter_11')
def hacking_sales_chapter_11():
    return render_template('blog/hacking_sales_chapter_11.html')

@app.route('/blog/hacking_sales_chapter_12')
def hacking_sales_chapter_12():
    return render_template('blog/hacking_sales_chapter_12.html')

@app.route('/blog/hacking_sales_chapter_13')
def hacking_sales_chapter_13():
    return render_template('blog/hacking_sales_chapter_13.html')

@app.route('/blog/hacking_sales_chapter_14')
def hacking_sales_chapter_14():
    return render_template('blog/hacking_sales_chapter_14.html')

#Sell Chapters
@app.route('/blog/sell_chapter_1')
def sell_chapter_1():
    return render_template('blog/sell_chapter_1.html')

@app.route('/blog/sell_chapter_2')
def sell_chapter_2():
    return render_template('blog/sell_chapter_2.html')

@app.route('/blog/sell_chapter_3')
def sell_chapter_3():
    return render_template('blog/sell_chapter_3.html')

@app.route('/blog/sell_chapter_4')
def sell_chapter_4():
    return render_template('blog/sell_chapter_4.html')

@app.route('/blog/sell_chapter_5')
def sell_chapter_5():
    return render_template('blog/sell_chapter_5.html')

@app.route('/blog/sell_chapter_6')
def sell_chapter_6():
    return render_template('blog/sell_chapter_6.html')

@app.route('/blog/sell_chapter_7')
def sell_chapter_7():
    return render_template('blog/sell_chapter_7.html')

@app.route('/blog/sell_chapter_8')
def sell_chapter_8():
    return render_template('blog/sell_chapter_8.html')

@app.route('/blog/sell_chapter_9')
def sell_chapter_9():
    return render_template('blog/sell_chapter_9.html')

@app.route('/blog/sell_chapter_10')
def sell_chapter_10():
    return render_template('blog/sell_chapter_10.html')

#Sales EQ Chapters
@app.route('/blog/sales_eq_chapter_1')
def sales_eq_chapter_1():
    return render_template('blog/sales_eq_chapter_1.html')

@app.route('/blog/sales_eq_chapter_2')
def sales_eq_chapter_2():
    return render_template('blog/sales_eq_chapter_2.html')

@app.route('/blog/sales_eq_chapter_3')
def sales_eq_chapter_3():
    return render_template('blog/sales_eq_chapter_3.html')

@app.route('/blog/sales_eq_chapter_4')
def sales_eq_chapter_4():
    return render_template('blog/sales_eq_chapter_4.html')

@app.route('/blog/sales_eq_chapter_5')
def sales_eq_chapter_5():
    return render_template('blog/sales_eq_chapter_5.html')

@app.route('/blog/sales_eq_chapter_6')
def sales_eq_chapter_6():
    return render_template('blog/sales_eq_chapter_6.html')

@app.route('/blog/sales_eq_chapter_7')
def sales_eq_chapter_7():
    return render_template('blog/sales_eq_chapter_7.html')

@app.route('/blog/sales_eq_chapter_8')
def sales_eq_chapter_8():
    return render_template('blog/sales_eq_chapter_8.html')

@app.route('/blog/sales_eq_chapter_9')
def sales_eq_chapter_9():
    return render_template('blog/sales_eq_chapter_9.html')

@app.route('/blog/sales_eq_chapter_10')
def sales_eq_chapter_10():
    return render_template('blog/sales_eq_chapter_10.html')

@app.route('/blog/sales_eq_chapter_11')
def sales_eq_chapter_11():
    return render_template('blog/sales_eq_chapter_11.html')

@app.route('/blog/sales_eq_chapter_12')
def sales_eq_chapter_12():
    return render_template('blog/sales_eq_chapter_12.html')

@app.route('/blog/sales_eq_chapter_13')
def sales_eq_chapter_13():
    return render_template('blog/sales_eq_chapter_13.html')

@app.route('/blog/sales_eq_chapter_14')
def sales_eq_chapter_14():
    return render_template('blog/sales_eq_chapter_14.html')

@app.route('/blog/sales_eq_chapter_15')
def sales_eq_chapter_15():
    return render_template('blog/sales_eq_chapter_15.html')

@app.route('/blog/sales_eq_chapter_16')
def sales_eq_chapter_16():
    return render_template('blog/sales_eq_chapter_16.html')

@app.route('/blog/sales_eq_chapter_17')
def sales_eq_chapter_17():
    return render_template('blog/sales_eq_chapter_17.html')

@app.route('/blog/sales_eq_chapter_18')
def sales_eq_chapter_18():
    return render_template('blog/sales_eq_chapter_18.html')

@app.route('/blog/sales_eq_chapter_19')
def sales_eq_chapter_19():
    return render_template('blog/sales_eq_chapter_19.html')

@app.route('/blog/sales_eq_chapter_20')
def sales_eq_chapter_20():
    return render_template('blog/sales_eq_chapter_20.html')

@app.route('/blog/sales_eq_chapter_21')
def sales_eq_chapter_21():
    return render_template('blog/sales_eq_chapter_21.html')

@app.route('/blog/sales_eq_chapter_22')
def sales_eq_chapter_22():
    return render_template('blog/sales_eq_chapter_22.html')

@app.route('/blog/sales_eq_chapter_23')
def sales_eq_chapter_23():
    return render_template('blog/sales_eq_chapter_23.html')

@app.route('/blog/sales_eq_chapter_24')
def sales_eq_chapter_24():
    return render_template('blog/sales_eq_chapter_24.html')

@app.route('/blog/sales_eq_chapter_25')
def sales_eq_chapter_25():
    return render_template('blog/sales_eq_chapter_25.html')

@app.route('/blog/sales_eq_chapter_26')
def sales_eq_chapter_26():
    return render_template('blog/sales_eq_chapter_26.html')

@app.route('/blog/sales_eq_chapter_27')
def sales_eq_chapter_27():
    return render_template('blog/sales_eq_chapter_27.html')

@app.route('/blog/sales_eq_chapter_28')
def sales_eq_chapter_28():
    return render_template('blog/sales_eq_chapter_28.html')

@app.route('/blog/sales_eq_chapter_29')
def sales_eq_chapter_29():
    return render_template('blog/sales_eq_chapter_29.html')

#Sitemap Route
@app.route('/sitemap.xml')
def sitemap_xml():
    sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url>
<loc>http://www.urxion.com/</loc>
</url>
<url>
<loc>http://www.urxion.com/services</loc>
</url>
<url>
<loc>http://www.urxion.com/cold-calling-that-converts</loc>
</url>
<url>
<loc>http://www.urxion.com/business-assessment</loc>
</url>
<url>
<loc>http://www.urxion.com/cold-calling-assessment</loc>
</url>
<url>
<loc>http://www.urxion.com/sales-assessment</loc>
</url>
<url>
<loc>http://www.urxion.com/contact</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_1</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_2</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_3</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_4</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_5</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_6</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_7</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_8</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_9</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_10</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_11</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_12</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_13</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_14</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_15</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_16</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_17</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_18</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_19</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_20</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_21</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_22</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_23</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_24</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_25</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_26</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_27</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_28</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq_chapter_29</loc>
</url>
</urlset>"""
    return Response(sitemap_content, status=200, mimetype="application/xml")

if __name__ == '__main__':
    app.run(debug=True)