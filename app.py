import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Set page config
st.set_page_config(layout="wide", page_title="Financial Calculators")

# Custom CSS
st.markdown("""
<style>
    .stApp {
        font-size: 14px;
    }
    .stMarkdown, .stText {
        font-size: 14px;
    }
    .stButton button {
        font-size: 16px;
        font-weight: bold;
        height: 3em;
        width: 100%;
        margin-bottom: 10px;
    }
    .stSelectbox, .stMultiselect, .stSlider {
        font-size: 14px;
    }
    .calculator-button {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        transition-duration: 0.4s;
    }
    .calculator-button:hover {
        background-color: #45a049;
    }
    .selected {
        background-color: #008CBA;
    }
    .selected:hover {
        background-color: #007B9E;
    }
</style>
""", unsafe_allow_html=True)

# Novated Lease Calculator Functions
def calculate_novated_lease(car_value, interest_rate, lease_term, tax_rate, gst_included=False,
                             annual_fuel=0, annual_maintenance=0, annual_tyres=0,
                             annual_finance_costs=0, annual_registration_insurance=0):
    if gst_included:
        car_value_ex_gst = car_value / 1.1
    else:
        car_value_ex_gst = car_value

    monthly_payment = (car_value_ex_gst * (interest_rate / 12)) / (1 - (1 + interest_rate / 12) ** (-lease_term))
    
    total_annual_costs = (annual_fuel + annual_maintenance + annual_tyres +
                          annual_finance_costs + annual_registration_insurance)
    
    total_cost = (monthly_payment * lease_term) + (total_annual_costs * (lease_term / 12))
    
    tax_savings = total_cost * tax_rate
    net_cost = total_cost - tax_savings
    return net_cost, monthly_payment, tax_savings

def calculate_car_ownership_costs(car_value, years, annual_maintenance, annual_insurance, annual_fuel):
    depreciation_rate = 0.15
    total_cost = 0
    for year in range(int(years)):
        total_cost += annual_maintenance + annual_insurance + annual_fuel
        car_value *= (1 - depreciation_rate)
    return total_cost, car_value

# Mortgage Calculator Functions
def calculate_repayment(loan_amount, annual_interest_rate, loan_term_years):
    monthly_interest_rate = annual_interest_rate / 12 / 100
    number_of_payments = loan_term_years * 12
    repayment = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments) / ((1 + monthly_interest_rate) ** number_of_payments - 1)
    return repayment

def calculate_cgt(purchase_price, selling_price, years_owned, capital_losses):
    capital_gain = selling_price - purchase_price - capital_losses
    if capital_gain > 0:
        cgt_discount = 0.5 if years_owned > 1 else 0
        taxable_gain = capital_gain * (1 - cgt_discount)
        return taxable_gain * 0.3
    return 0

def calculate_expected_rate(current_long_term_rate, current_short_term_rate):
    R = current_long_term_rate
    r = current_short_term_rate
    expected_rate = ((1 + R)**2 / (1 + r)) - 1
    return expected_rate * 100

def calculate_new_loan_term(loan_amount, annual_interest_rate, monthly_repayment, extra_payment):
    monthly_interest_rate = annual_interest_rate / 12 / 100
    total_monthly_payment = monthly_repayment + extra_payment
    months = -np.log(1 - (monthly_interest_rate * loan_amount) / total_monthly_payment) / np.log(1 + monthly_interest_rate)
    return months

def breakdown_payments(loan_amount, annual_interest_rate, loan_term_years):
    monthly_interest_rate = annual_interest_rate / 12 / 100
    number_of_payments = loan_term_years * 12
    
    principal_paid = []
    interest_paid = []
    
    for month in range(1, number_of_payments + 1):
        interest_for_month = loan_amount * monthly_interest_rate
        total_repayment = calculate_repayment(loan_amount, annual_interest_rate, loan_term_years)
        principal_for_month = total_repayment - interest_for_month
        principal_paid.append(principal_for_month)
        interest_paid.append(interest_for_month)
        loan_amount -= principal_for_month
    
    return principal_paid, interest_paid

# Main App
def main():
    st.title("Financial Calculators")
    
    # Sidebar for page selection
    page = st.sidebar.radio("Select Calculator", ["Novated Lease", "Mortgage"])
    
    if page == "Novated Lease":
        novated_lease_calculator()
    elif page == "Mortgage":
        mortgage_calculator()

def novated_lease_calculator():
    st.title('Car Ownership vs Novated Lease Comparison')

    st.sidebar.header('Input Parameters')
    current_car_value = st.sidebar.number_input('Current Car Value ($)', value=20000, step=1000)
    new_car_value = st.sidebar.number_input('New Car Value ($)', value=50000, step=1000)
    interest_rate = st.sidebar.slider('Annual Interest Rate (%)', 1.0, 10.0, 6.0) / 100
    lease_term = st.sidebar.slider('Lease Term (months)', 12, 60, 48)
    tax_rate = st.sidebar.slider('Marginal Tax Rate (%)', 10, 50, 32) / 100

    gst_included = st.sidebar.checkbox('Is GST included in the car value?', value=False)

    st.sidebar.header('Novated Lease Costs (Annual)')
    annual_fuel = st.sidebar.number_input('Fuel/Charge Cost ($)', value=2000, step=100)
    annual_maintenance = st.sidebar.number_input('Maintenance Cost ($)', value=1000, step=100)
    annual_tyres = st.sidebar.number_input('Tyres Cost ($)', value=500, step=100)
    annual_finance_costs = st.sidebar.number_input('Finance & Other Costs ($)', value=1200, step=100)
    annual_registration_insurance = st.sidebar.number_input('Registration & Insurance Cost ($)', value=1200, step=100)

    years = lease_term / 12

    novated_cost, monthly_payment, tax_savings = calculate_novated_lease(
        new_car_value,
        interest_rate,
        lease_term,
        tax_rate,
        gst_included,
        annual_fuel,
        annual_maintenance,
        annual_tyres,
        annual_finance_costs,
        annual_registration_insurance
    )

    ownership_cost, final_car_value = calculate_car_ownership_costs(current_car_value, years, 
                                                                    annual_maintenance, 
                                                                    annual_registration_insurance,
                                                                    annual_fuel)

    st.header('Results')
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Current Car Ownership')
        st.metric('Total Cost', f'${ownership_cost:,.2f}')
        st.metric('Final Car Value', f'${final_car_value:,.2f}')
        st.metric('Net Cost', f'${ownership_cost - (current_car_value - final_car_value):,.2f}')
    with col2:
        st.subheader('Novated Lease')
        st.metric('Net Cost', f'${novated_cost:,.2f}')
        st.metric('Monthly Payment', f'${monthly_payment:,.2f}')
        st.metric('Tax Savings (Total over Lease Term)', f'${tax_savings:,.2f}')

    st.header('Tax Savings Comparison')
    ownership_tax_savings = 0
    novated_lease_tax_savings = tax_savings
    difference = novated_lease_tax_savings - ownership_tax_savings

    col1, col2 = st.columns(2)
    with col1:
        st.metric('Current Car Ownership Tax Savings', f'${ownership_tax_savings:,.2f}')
    with col2:
        st.metric('Novated Lease Tax Savings', f'${novated_lease_tax_savings:,.2f}')

    st.write("Note: This assumes a **100% tax break** on the novated lease car expenses.")

    st.header('Comparison Over Time')
    years_range = np.arange(0, years + 1)
    ownership_values = [current_car_value * (0.85 ** year) - (ownership_cost / years) * year for year in years_range]
    novated_values = [new_car_value - (i * monthly_payment) for i in range(len(years_range))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years_range, y=ownership_values, mode='lines', name='Current Car Value'))
    fig.add_trace(go.Scatter(x=years_range, y=novated_values, mode='lines', name='Novated Lease Car Value'))
    fig.update_layout(title='Asset Value Over Time',
                       xaxis_title='Years', 
                       yaxis_title='Value ($)',
                        legend=dict(x=0.01, y=0.99),
                        height=400)
    st.plotly_chart(fig)

    st.header('Analysis')
    options = {
        'Current Car Ownership': ownership_cost - (current_car_value - final_car_value),
        'Novated Lease': novated_cost,
    }
    best_option = min(options, key=options.get)

    st.success(f'Based on the given parameters, the **{best_option}** appears to be the best financial option.')

    for option, value in options.items():
        st.write(f'{option}: Net Cost/Opportunity Cost = ${value:,.2f}')

    st.write("Please note that this analysis is based on several assumptions and doesn't account for all factors such as:")
    st.write("1. The utility and comfort of a new car vs. the current car")
    st.write("2. Potential changes in tax rates over time")
    st.write("3. The impact of inflation on purchasing power")
    st.write("4. Unexpected repairs or other costs that may arise")
    st.write("5. The assumption of a **100% tax break** on novated lease expenses.")

    st.write("It's important to consider these factors and consult with a financial advisor before making a decision.")

def mortgage_calculator():
    st.title("🏡 Mortgage Repayment & Financial Projection Calculator")

    st.sidebar.header("Input Your Details")

    st.sidebar.subheader("House and Loan Details")
    house_price = st.sidebar.number_input("House Price ($)", value=852075, step=1000)
    deposit = st.sidebar.number_input("Deposit ($)", value=230208, step=1000)
    loan_term_years = st.sidebar.number_input("Loan Term (Years)", value=15, min_value=1, max_value=30)

    st.sidebar.subheader("Interest Rates")
    current_long_term_rate = st.sidebar.number_input("Current Long-Term Interest Rate (%)", value=6.04, step=0.01)
    current_short_term_rate = st.sidebar.number_input("Current Short-Term Interest Rate (%)", value=5.00, step=0.01)

    st.sidebar.subheader("Financial Projections")
    selling_price = st.sidebar.number_input("Projected Selling Price ($)", value=1300000, step=1000)
    years_owned = st.sidebar.number_input("Years Owned", value=5, min_value=1)
    capital_losses = st.sidebar.number_input("Capital Losses/Expenditure on House ($)", value=45000, step=1000)

    st.sidebar.subheader("Monthly Income and Expenses")
    monthly_income = st.sidebar.number_input("Monthly Income ($)", value=8500, step=100)
    rental_income = st.sidebar.number_input("Expected Monthly Rental Income ($)", value=3000, step=100)
    property_management_fee_percentage = st.sidebar.number_input("Property Management Fee (%)", value=6.0, format="%.2f", step=0.1) / 100
    rent_expense = st.sidebar.number_input("Monthly Rent Expense ($)", value=1950, step=50)
    utilities_expense = st.sidebar.number_input("Monthly Utilities Expense ($)", value=200, step=50)
    groceries_expense = st.sidebar.number_input("Monthly Groceries Expense ($)", value=600, step=50)
    other_expenses = st.sidebar.number_input("Other Monthly Expenses ($)", value=100, step=50)

    extra_payment = st.sidebar.number_input("Extra Monthly Payment ($)", value=1500, step=100)

    loan_amount = house_price - deposit


    if loan_amount > 0:
        # [Previous calculations remain the same]
        annual_interest_rate = calculate_expected_rate(current_long_term_rate / 100, current_short_term_rate / 100)
        monthly_repayment = calculate_repayment(loan_amount, annual_interest_rate, loan_term_years)
        principal_paid, interest_paid = breakdown_payments(loan_amount, annual_interest_rate, loan_term_years)
        total_payment = monthly_repayment * loan_term_years * 12
        total_interest = total_payment - loan_amount
        cgt_due = calculate_cgt(house_price, selling_price, years_owned, capital_losses)
        net_profit_from_sale = selling_price - house_price - cgt_due 
        management_fee_amount = rental_income * property_management_fee_percentage
        net_rental_income = rental_income - management_fee_amount
        total_monthly_expenses = rent_expense + utilities_expense + groceries_expense + other_expenses + monthly_repayment - net_rental_income
        net_monthly_savings = monthly_income - total_monthly_expenses
        new_loan_months = calculate_new_loan_term(loan_amount, annual_interest_rate, monthly_repayment, extra_payment)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Mortgage Summary")
            st.metric("Loan Amount", f"${loan_amount:,.2f}")
            st.metric("Annual Interest Rate", f"{annual_interest_rate:.2f}%")
            st.metric("Monthly Repayment", f"${monthly_repayment:,.2f}")

        with col2:
            st.subheader("Total Payments")
            st.metric("Total Payment", f"${total_payment:,.2f}")
            st.metric("Total Interest", f"${total_interest:,.2f}")
            st.metric("Interest to Principal Ratio", f"{(total_interest/loan_amount)*100:.2f}%")

        with col3:
            st.subheader("Financial Projections")
            st.metric("Capital Gains Tax", f"${cgt_due:,.2f}")
            st.metric("Net Profit from Sale", f"${net_profit_from_sale:,.2f}")
            st.metric("Monthly Net Savings", f"${net_monthly_savings:,.2f}")

        st.subheader("Loan Term Reduction")
        col4, col5 = st.columns(2)
        with col4:
            st.metric("Original Loan Term", f"{loan_term_years} years")
        with col5:
            new_loan_years = new_loan_months / 12
            st.metric("New Loan Term", f"{new_loan_years:.2f} years", 
                      delta=f"-{loan_term_years - new_loan_years:.2f} years")

        st.subheader("Payment Breakdown Over Time")
        
        years = np.arange(1, loan_term_years + 1)
        yearly_principal = [sum(principal_paid[i*12:(i+1)*12]) for i in range(loan_term_years)]
        yearly_interest = [sum(interest_paid[i*12:(i+1)*12]) for i in range(loan_term_years)]
        
        cumulative_principal = np.cumsum(yearly_principal)
        cumulative_interest = np.cumsum(yearly_interest)
        
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Yearly Breakdown", "Cumulative Payments"))
        
        fig.add_trace(go.Bar(x=years, y=yearly_principal, name='Principal', marker_color='blue'), row=1, col=1)
        fig.add_trace(go.Bar(x=years, y=yearly_interest, name='Interest', marker_color='red'), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=years, y=cumulative_principal, mode='lines+markers', name='Cumulative Principal', line=dict(color='blue')), row=1, col=2)
        fig.add_trace(go.Scatter(x=years, y=cumulative_interest, mode='lines+markers', name='Cumulative Interest', line=dict(color='red')), row=1, col=2)
        
        fig.update_layout(height=400, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig.update_xaxes(title_text="Year", row=1, col=1)
        fig.update_xaxes(title_text="Year", row=1, col=2)
        fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
        fig.update_yaxes(title_text="Cumulative Amount ($)", row=1, col=2)
        
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Deposit must be less than House Price.")

    st.markdown("---")
    st.markdown("""
    ### Disclaimer:
    This calculator provides estimates based on user inputs and general assumptions. 
    Actual mortgage terms may vary based on lender conditions and individual circumstances. 
    Please consult with a financial advisor for personalized advice.
    """)

if __name__ == "__main__":
    main()

