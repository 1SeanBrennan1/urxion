from flask import Flask, render_template, request, Response, url_for, redirect

app = Flask(__name__)

#Home Page
@app.route('/')
def index():
    return render_template('index.html')

#Services Page
@app.route('/services')
def services():
    return render_template('services.html')

#Cold Calling Page
@app.route('/cold-calling-that-converts')
def cold_calling():
    return render_template('Cold Calling That Converts.html')

#Business Assessment Page
@app.route('/business-assessment')
def business_assessment():
    return render_template('Business Assessment.html')

#Cold Calling Assessment Page
@app.route('/cold-calling-assessment')
def cold_calling_assessment():
    return render_template('Cold Calling Assessment.html')

#Cold Calling Assessment Page
@app.route('/Knowledge-is-Power')
def knowledge_is_power():
    return render_template('Knowledge is Power.html')

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

#Sales Assessment Page


@app.route('/', methods=['GET', 'POST'])
def step_1():
    if request.method == 'POST':
        try:
            price_per_unit = float(request.form['price_per_unit'])
            variable_cost_per_unit = float(request.form['variable_cost_per_unit'])
            units_per_order = float(request.form['units_per_order'])

            total_revenue_per_order = price_per_unit * units_per_order
            variable_cost_per_order = variable_cost_per_unit * units_per_order

            return render_template('step_2.html',
                                   total_revenue_per_order=total_revenue_per_order,
                                   variable_cost_per_order=variable_cost_per_order)
        except ValueError:
            return "Invalid input. Please enter numeric values.", 400
    else:
        return render_template('step_1.html')

@app.route('/step_2', methods=['GET', 'POST'])
def step_2():
    if request.method == 'POST':
        try:
            num_sales_reps = int(request.form['num_sales_reps'])
            avg_salary = float(request.form['avg_salary'])
            annual_benefits = float(request.form['annual_benefits'])
            overhead_costs = float(request.form['overhead_costs'])

            total_fixed_costs_internal = (num_sales_reps * (avg_salary + annual_benefits)) + overhead_costs

            return render_template('step_3.html', total_fixed_costs_internal=total_fixed_costs_internal,
                                   total_revenue_per_order=request.form.get('total_revenue_per_order'),
                                   variable_cost_per_order=request.form.get('variable_cost_per_order'))
        except ValueError:
            return "Invalid input. Please enter numeric values.", 400
    else:
        return render_template('step_2.html', total_revenue_per_order=request.args.get('total_revenue_per_order'),
                               variable_cost_per_order=request.args.get('variable_cost_per_order'))

@app.route('/step_3', methods=['GET', 'POST'])
def step_3():
    if request.method == 'POST':
        try:
            weekly_cold_calling_cost = float(request.form['weekly_cold_calling_cost'])
            cost_per_booked_meeting = float(request.form['cost_per_booked_meeting'])
            conversion_rate = float(request.form['conversion_rate'])

            cold_calls_per_week = 20
            cold_calls_per_booked_meeting = 5

            variable_cost_per_closed_deal = (weekly_cold_calling_cost / cold_calls_per_week) * cold_calls_per_booked_meeting + cost_per_booked_meeting
            variable_cost_per_order_external = variable_cost_per_closed_deal / conversion_rate

            return render_template('step_4.html', variable_cost_per_order_external=variable_cost_per_order_external,
                                   total_fixed_costs_internal=request.form.get('total_fixed_costs_internal'),
                                   total_revenue_per_order=request.form.get('total_revenue_per_order'),
                                   variable_cost_per_order=request.form.get('variable_cost_per_order'))
        except ValueError:
            return "Invalid input. Please enter numeric values.", 400
    else:
        return render_template('step_3.html', total_fixed_costs_internal=request.args.get('total_fixed_costs_internal'),
                               total_revenue_per_order=request.args.get('total_revenue_per_order'),
                               variable_cost_per_order=request.args.get('variable_cost_per_order'))

@app.route('/step_4', methods=['GET', 'POST'])
def step_4():
    if request.method == 'POST':
        try:
            projected_orders_internal = float(request.form['projected_orders_internal'])
            projected_orders_external = float(request.form['projected_orders_external'])

            return render_template('step_5.html', projected_orders_internal=projected_orders_internal,
                                   projected_orders_external=projected_orders_external,
                                   variable_cost_per_order_external=request.form.get('variable_cost_per_order_external'),
                                   total_fixed_costs_internal=request.form.get('total_fixed_costs_internal'),
                                   total_revenue_per_order=request.form.get('total_revenue_per_order'),
                                   variable_cost_per_order=request.form.get('variable_cost_per_order'))
        except ValueError:
            return "Invalid input. Please enter numeric values.", 400
    else:
        return render_template('step_4.html', variable_cost_per_order_external=request.args.get('variable_cost_per_order_external'),
                               total_fixed_costs_internal=request.args.get('total_fixed_costs_internal'),
                               total_revenue_per_order=request.args.get('total_revenue_per_order'),
                               variable_cost_per_order=request.args.get('variable_cost_per_order'))

@app.route('/step_5', methods=['GET', 'POST'])
def step_5():
    if request.method == 'POST':
        try:
            total_fixed_costs_internal = float(request.form.get('total_fixed_costs_internal'))
            total_revenue_per_order = float(request.form.get('total_revenue_per_order'))
            variable_cost_per_order_internal = float(request.form.get('variable_cost_per_order'))
            variable_cost_per_order_external = float(request.form.get('variable_cost_per_order_external'))

            break_even_orders_internal = total_fixed_costs_internal / (total_revenue_per_order - variable_cost_per_order_internal)
            break_even_sales_internal = break_even_orders_internal * total_revenue_per_order

            break_even_orders_external = 0
            break_even_sales_external = (495 * 52) / ((total_revenue_per_order - variable_cost_per_order_external) / total_revenue_per_order)

            return render_template('step_5.html', break_even_orders_internal=break_even_orders_internal,
                                   break_even_sales_internal=break_even_sales_internal,
                                   break_even_orders_external=break_even_orders_external,
                                   break_even_sales_external=break_even_sales_external,
                                   projected_orders_internal=request.form.get('projected_orders_internal'),
                                   projected_orders_external=request.form.get('projected_orders_external'),
                                   variable_cost_per_order_external=variable_cost_per_order_external,
                                   total_fixed_costs_internal=total_fixed_costs_internal,
                                   total_revenue_per_order=total_revenue_per_order,
                                   variable_cost_per_order=variable_cost_per_order)
        except ValueError:
            return "Invalid input. Please enter numeric values.", 400
    else:
        return render_template('step_5.html', projected_orders_internal=request.args.get('projected_orders_internal'),
                               projected_orders_external=request.args.get('projected_orders_external'),
                               variable_cost_per_order_external=request.args.get('variable_cost_per_order_external'),
                               total_fixed_costs_internal=request.args.get('total_fixed_costs_internal'),
                               total_revenue_per_order=request.args.get('total_revenue_per_order'),
                               variable_cost_per_order=request.args.get('variable_cost_per_order'))

@app.route('/step_6', methods=['GET', 'POST'])
def step_6():
    if request.method == 'POST':
        try:
            projected_orders_internal = float(request.form.get('projected_orders_internal'))
            projected_orders_external = float(request.form.get('projected_orders_external'))
            total_fixed_costs_internal = float(request.form.get('total_fixed_costs_internal'))
            total_revenue_per_order = float(request.form.get('total_revenue_per_order'))
            variable_cost_per_order_internal = float(request.form.get('variable_cost_per_order'))
            variable_cost_per_order_external = float(request.form.get('variable_cost_per_order_external'))

            annual_sales_revenue_internal = projected_orders_internal * 12 * total_revenue_per_order
            annual_profit_internal = annual_sales_revenue_internal - total_fixed_costs_internal - (
                        annual_sales_revenue_internal * (variable_cost_per_order_internal / total_revenue_per_order))

            annual_sales_revenue_external = projected_orders_external * 12 * total_revenue_per_order
            annual_profit_external = annual_sales_revenue_external - (
                        annual_sales_revenue_external * (variable_cost_per_order_external / total_revenue_per_order))

            return render_template('step_6.html', annual_sales_revenue_internal=annual_sales_revenue_internal,
                                   annual_profit_internal=annual_profit_internal,
                                   annual_sales_revenue_external=annual_sales_revenue_external,
                                   annual_profit_external=annual_profit_external,
                                   projected_orders_internal=projected_orders_internal,
                                   projected_orders_external=projected_orders_external,
                                   variable_cost_per_order_external=variable_cost_per_order_external,
                                   total_fixed_costs_internal=total_fixed_costs_internal,
                                   total_revenue_per_order=total_revenue_per_order,
                                   variable_cost_per_order=variable_cost_per_order)
        except ValueError:
            return "Invalid input. Please enter numeric values.", 400
    else:
        return render_template('step_6.html', projected_orders_internal=request.args.get('projected_orders_internal'),
                               projected_orders_external=request.args.get('projected_orders_external'),
                               variable_cost_per_order_external=request.args.get('variable_cost_per_order_external'),
                               total_fixed_costs_internal=request.args.get('total_fixed_costs_internal'),
                               total_revenue_per_order=request.args.get('total_revenue_per_order'),
                               variable_cost_per_order=request.args.get('variable_cost_per_order'))

@app.route('/step_7', methods=['GET', 'POST'])
def step_7():
    if request.method == 'POST':
        try:
            projected_orders_internal = float(request.form.get('projected_orders_internal'))
            projected_orders_external = float(request.form.get('projected_orders_external'))
            total_fixed_costs_internal = float(request.form.get('total_fixed_costs_internal'))
            total_revenue_per_order = float(request.form.get('total_revenue_per_order'))
            variable_cost_per_order_internal = float(request.form.get('variable_cost_per_order'))
            variable_cost_per_order_external = float(request.form.get('variable_cost_per_order_external'))
            annual_sales_revenue_internal = float(request.form.get('annual_sales_revenue_internal'))
            annual_profit_internal = float(request.form.get('annual_profit_internal'))
            annual_sales_revenue_external = float(request.form.get('annual_sales_revenue_external'))
            annual_profit_external = float(request.form.get('annual_profit_external'))

            return render_template('step_7.html',
                                   projected_orders_internal=projected_orders_internal,
                                   projected_orders_external=projected_orders_external,
                                   total_fixed_costs_internal=total_fixed_costs_internal,
                                   total_revenue_per_order=total_revenue_per_order,
                                   variable_cost_per_order=variable_cost_per_order,
                                   variable_cost_per_order_external=variable_cost_per_order_external,
                                   annual_sales_revenue_internal=annual_sales_revenue_internal,
                                   annual_profit_internal=annual_profit_internal,
                                   annual_sales_revenue_external=annual_sales_revenue_external,
                                   annual_profit_external=annual_profit_external)
        except ValueError:
            return "Invalid input. Please enter numeric values.", 400
    else:
        return render_template('step_7.html',
                               projected_orders_internal=request.args.get('projected_orders_internal'),
                               projected_orders_external=request.args.get('projected_orders_external'),
                               total_fixed_costs_internal=request.args.get('total_fixed_costs_internal'),
                               total_revenue_per_order=request.args.get('total_revenue_per_order'),
                               variable_cost_per_order=request.args.get('variable_cost_per_order'),
                               variable_cost_per_order_external=request.args.get('variable_cost_per_order_external'),
                               annual_sales_revenue_internal=request.args.get('annual_sales_revenue_internal'),
                               annual_profit_internal=request.args.get('annual_profit_internal'),
                               annual_sales_revenue_external=request.args.get('annual_sales_revenue_external'),
                               annual_profit_external=request.args.get('annual_profit_external'))

@app.route('/step_8', methods=['GET', 'POST'])
def step_8():
    if request.method == 'POST':
        try:
            annual_profit_internal = float(request.form.get('annual_profit_internal'))
            annual_profit_external = float(request.form.get('annual_profit_external'))
            break_even_orders_internal = float(request.form.get('break_even_orders_internal'))
            break_even_sales_external = float(request.form.get('break_even_sales_external'))

            if annual_profit_internal > annual_profit_external and break_even_orders_internal < break_even_sales_external:
                recommendation = "Internal Team"
                rationale = "The internal team is projected to be more profitable and has a lower break-even point."
                consideration_1 = "You'll need to invest in hiring and training sales representatives."
                consideration_2 = "Managing an internal team requires more time and effort."
                consideration_3 = "However, you'll have more control over your sales process and team culture."
            else:
                recommendation = "External Team"
                rationale = "The external team is projected to be more profitable or has a lower break-even point, or both."
                consideration_1 = "You'll have lower upfront costs and less management overhead."
                consideration_2 = "You might have less control over the sales process and team performance."
                consideration_3 = "Consider the reputation and track record of the external team before making a decision."

            return render_template('step_8.html', recommendation=recommendation,
                                   rationale=rationale,
                                   consideration_1=consideration_1,
                                   consideration_2=consideration_2,
                                   consideration_3=consideration_3,
                                   annual_profit_internal=annual_profit_internal,
                                   annual_profit_external=annual_profit_external,
                                   break_even_orders_internal=break_even_orders_internal,
                                   break_even_sales_external=break_even_sales_external)
        except ValueError:
            return "Invalid input. Please enter numeric values.", 400
    else:
        return render_template('step_8.html',
                               annual_profit_internal=request.args.get('annual_profit_internal'),
                               annual_profit_external=request.args.get('annual_profit_external'),
                               break_even_orders_internal=request.args.get('break_even_orders_internal'),
                               break_even_sales_external=request.args.get('break_even_sales_external'))



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
<loc>http://www.urxion.com/blog/cold_to_committed</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sales_eq</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/break-even-point</loc>
</url>

<!-- Challenger Sale Chapters -->
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_1</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_2</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_3</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_4</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_5</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_6</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_7</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_8</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/challenger_chapter_9</loc>
</url>
<!-- Cold to Committed Chapters -->
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_1</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_2</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_3</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_4</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_5</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_6</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_7</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_8</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_9</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/cold_to_committed_chapter_10</loc>
</url>
<!-- Hacking Sales Chapters -->
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_1</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_2</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_3</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_4</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_5</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_6</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_7</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_8</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_9</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_10</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_11</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_12</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_13</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/hacking_sales_chapter_14</loc>
</url>
<!-- Sell Chapters -->
<url>
<loc>http://www.urxion.com/blog/sell_chapter_1</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_2</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_3</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_4</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_5</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_6</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_7</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_8</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_9</loc>
</url>
<url>
<loc>http://www.urxion.com/blog/sell_chapter_10</loc>
</url>
<!-- Sales EQ Chapters -->
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