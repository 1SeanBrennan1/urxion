function convertPercentageToNumber(value) {
    if (value.includes('%')) {
        value = value.replace('%', '');
        value = parseFloat(value) / 100;
    }
    return value;
}

function calculateScenario1() {
    const aeSalaryElement = document.getElementById('aeSalary');
    const sdrSalaryElement = document.getElementById('sdrSalary');
    const aeVarCostsElement = document.getElementById('aeVarCosts');
    const sdrBonusElement = document.getElementById('sdrBonus');
    const coaElement = document.getElementById('coa');
    const leadsToSaleLowElement = document.getElementById('leadsToSaleLow');
    const leadsToSaleHighElement = document.getElementById('leadsToSaleHigh');
    const averageDealSizeElement = document.getElementById('averagedealsize');

    if (!aeSalaryElement || !sdrSalaryElement || !aeVarCostsElement || !sdrBonusElement ||
        !leadsToSaleLowElement || !leadsToSaleHighElement || !averageDealSizeElement) {
        alert('One or more input fields are missing.');
        return;
    }

    const aeSalary = parseFloat(aeSalaryElement.value.replace(/,/g, ''));
    const sdrSalary = parseFloat(sdrSalaryElement.value.replace(/,/g, ''));
    const aeVarCosts = parseFloat(aeVarCostsElement.value.replace(/,/g, ''));
    const sdrBonus = parseFloat(sdrBonusElement.value.replace(/,/g, ''));
    //const coa = parseFloat(coaElement.value.replace(/,/g, ''));
    const leadsToSaleLow = parseFloat(convertPercentageToNumber(leadsToSaleLowElement.value));
    const leadsToSaleHigh = parseFloat(convertPercentageToNumber(leadsToSaleHighElement.value));
    const averageDealSize = parseFloat(averageDealSizeElement.value.replace(/,/g, ''));

    // Validate input fields
    if (isNaN(aeSalary) || isNaN(sdrSalary) || isNaN(aeVarCosts) || isNaN(sdrBonus) ||
        isNaN(leadsToSaleLow) || isNaN(leadsToSaleHigh) || isNaN(averageDealSize)) {
        alert('Please ensure all input fields are filled with valid numbers.');
        return;
    }

    // Fixed Costs (Scenario 1)
    const totalFixedCosts = aeSalary + (2 * sdrSalary);

    // CAC Calculation (Cost per Acquired Customer)
    const cacLow = sdrBonus / (leadsToSaleLow)  + aeVarCosts;
    const cacHigh = sdrBonus / (leadsToSaleHigh) + aeVarCosts;

    // Contribution Margin per Deal
    const contributionMarginLow = averageDealSize - cacLow;
    const contributionMarginHigh = averageDealSize - cacHigh;

    // Breakeven Deals - Low Leads to Sale
    const breakEvenDealsLow = totalFixedCosts / contributionMarginLow;

    // Breakeven Deals - High Leads to Sale
    const breakEvenDealsHigh = totalFixedCosts / contributionMarginHigh;

    // Deals for $100k Profit - Low Leads to Sale
    const targetProfit = 100000; // $100k per week for a year
    const dealsForProfitLow = (totalFixedCosts + targetProfit) / contributionMarginLow;

    // Deals for $100k Profit - High Leads to Sale
    const dealsForProfitHigh = (totalFixedCosts + targetProfit) / contributionMarginHigh;

    return {
        totalFixedCosts,
        cacLow,
        cacHigh,
        contributionMarginLow,
        contributionMarginHigh,
        breakEvenDealsLow,
        breakEvenDealsHigh,
        dealsForProfitLow,
        dealsForProfitHigh
    };
}

function calculateScenario2() {
    const aeSalaryElement = document.getElementById('aeSalary');
    const aeVarCostsElement = document.getElementById('aeVarCosts');
    const leadsToSaleLowElement = document.getElementById('leadsToSaleLow');
    const leadsToSaleHighElement = document.getElementById('leadsToSaleHigh');
    const averageDealSizeElement = document.getElementById('averagedealsize');

    if (!aeSalaryElement || !aeVarCostsElement || !leadsToSaleLowElement || !leadsToSaleHighElement || !averageDealSizeElement) {
        alert('One or more input fields are missing.');
        return;
    }

    const aeSalary = parseFloat(aeSalaryElement.value.replace(/,/g, ''));
    const leadGenServiceCost = 19500; // Fixed cost of lead generation service
    const leadGenCostPerLead = 75; // Fixed cost per lead
    const aeVarCosts = parseFloat(aeVarCostsElement.value.replace(/,/g, ''));
    const leadsToSaleLow = parseFloat(convertPercentageToNumber(leadsToSaleLowElement.value));
    const leadsToSaleHigh = parseFloat(convertPercentageToNumber(leadsToSaleHighElement.value));
    const averageDealSize = parseFloat(averageDealSizeElement.value.replace(/,/g, ''));

    // Validate input fields
    if (isNaN(aeSalary) || isNaN(aeVarCosts) || isNaN(leadsToSaleLow) || isNaN(leadsToSaleHigh) || isNaN(averageDealSize)) {
        alert('Please ensure all input fields are filled with valid numbers.');
        return;
    }

    // Fixed Costs (Scenario 2)
    const totalFixedCosts = aeSalary + leadGenServiceCost;

    // CAC Calculation (Cost per Acquired Customer)
    const cacLow = (leadGenCostPerLead * leadsToSaleLow) + aeVarCosts;
    const cacHigh = (leadGenCostPerLead * leadsToSaleHigh) + aeVarCosts;

    // Contribution Margin per Deal
    const contributionMarginLow = averageDealSize - cacLow;
    const contributionMarginHigh = averageDealSize - cacHigh;

    // Breakeven Deals - Low Leads to Sale
    const breakEvenDealsLow = totalFixedCosts / contributionMarginLow;

    // Breakeven Deals - High Leads to Sale
    const breakEvenDealsHigh = totalFixedCosts / contributionMarginHigh;

    // Deals for $100k Profit - Low Leads to Sale
    const targetProfit = 100000 * 52; // $100k per week for a year
    const dealsForProfitLow = (totalFixedCosts + targetProfit) / contributionMarginLow;

    // Deals for $100k Profit - High Leads to Sale
    const dealsForProfitHigh = (totalFixedCosts + targetProfit) / contributionMarginHigh;

    return {
        totalFixedCosts,
        cacLow,
        cacHigh,
        contributionMarginLow,
        contributionMarginHigh,
        breakEvenDealsLow,
        breakEvenDealsHigh,
        dealsForProfitLow,
        dealsForProfitHigh
    };
}

function displayScenarioResults(scenario, resultsDivId) {
    const resultsDiv = document.getElementById(resultsDivId);
    if (resultsDiv) {
        resultsDiv.innerHTML = `
            <h2>${resultsDivId === 'scenario1-results' ? 'Scenario 1 (1 AE + 2 SDRs)' : 'Scenario 2 (1 AE + Lead Gen Service)'}</h2>
            <p>Total Fixed Costs: $${scenario.totalFixedCosts.toFixed(2)}</p>
            <p>CAC (Low Leads): $${scenario.cacLow.toFixed(2)}</p>
            <p>CAC (High Leads): $${scenario.cacHigh.toFixed(2)}</p>
            <p>Contribution Margin (Low): $${scenario.contributionMarginLow.toFixed(2)}</p>
            <p>Contribution Margin (High): $${scenario.contributionMarginHigh.toFixed(2)}</p>
            <p><strong>Breakeven Deals (Low Leads):</strong> ${scenario.breakEvenDealsLow.toFixed(0)}</p>
            <p><strong>Breakeven Deals (High Leads):</strong> ${scenario.breakEvenDealsHigh.toFixed(0)}</p>
            <p><strong>Deals for $100k Profit (Low Leads):</strong> ${scenario.dealsForProfitLow.toFixed(0)}</p>
            <p><strong>Deals for $100k Profit (High Leads):</strong> ${scenario.dealsForProfitHigh.toFixed(0)}</p>
        `;
    }
}

function calculateAllScenarios() {
    const scenario1Results = calculateScenario1();
    const scenario2Results = calculateScenario2();

    if (scenario1Results && scenario2Results) {
        displayScenarioResults(scenario1Results, 'scenario1-results');
        displayScenarioResults(scenario2Results, 'scenario2-results');

        // Show the results section after calculations
        const totalResults = document.getElementById('total-results');
        if (totalResults) {
            totalResults.style.display = 'block';
        }

        // Show the analysis summary section
        const analysisSummary = document.getElementById('analysis-summary');
        if (analysisSummary) {
            analysisSummary.style.display = 'block'; // Show after calculation
        }
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    // Attach the calculateAllScenarios function to the button click event
    document.querySelector('.calculate-btn').addEventListener('click', calculateAllScenarios);
});