import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import time

# Set page config
st.set_page_config(
    page_title="Personal Finance & Historical Analysis",
    layout="wide"
)

# Custom CSS for both pages
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

# Historical Treaties Data
treaties_data = {
    "Treaty Name": [
        "Lend-Lease Act (USSR)", "Yalta Conference Agreement", "Potsdam Conference", "SALT I",
        "Helsinki Accords", "INF Treaty", "START I", "Budapest Memorandum", "NATO-Russia Founding Act",
        "START II", "SORT Treaty", "New START Treaty", "Minsk Protocol", "Minsk II",
        "New START Extension", "Donbas Ceasefire 2023 (Hypothetical)", "Crimea Status Accord 2024 (Hypothetical)",
        "US-Russia Arms Limitation Talks 2025 (Hypothetical)"
    ],
    "Date": [
        "1941-10-01", "1945-02-11", "1945-08-02", "1972-05-26", "1975-08-01", "1987-12-08",
        "1991-07-31", "1994-12-05", "1997-05-27", "1993-01-03", "2002-05-24", "2010-04-08",
        "2014-09-05", "2015-02-12", "2021-02-03", "2023-06-15", "2024-03-20", "2025-01-15"
    ],
    "Description": [
        "US program to supply the USSR with war material during WWII",
        "Post-WWII reorganization of Europe agreed by US, UK and USSR",
        "Further decisions on Germany, Poland, and post-war order",
        "Strategic Arms Limitation Talks between US and USSR",
        "Agreement recognizing post-WWII borders in Europe",
        "Intermediate-Range Nuclear Forces Treaty (US-USSR)",
        "Strategic Arms Reduction Treaty between US and USSR",
        "Security assurances to Ukraine in exchange for giving up nuclear weapons",
        "Foundation of cooperation between NATO and Russia",
        "Further strategic arms reductions (never fully implemented)",
        "Strategic Offensive Reductions Treaty (US-Russia)",
        "Nuclear arms reduction treaty between US and Russia",
        "Ceasefire agreement during Donbas conflict in Ukraine",
        "Follow-up to the Minsk Protocol",
        "Extension of the New START treaty until February 2026",
        "Attempted ceasefire in Donbas amid ongoing tensions (hypothetical)",
        "Agreement addressing Crimea’s status with international oversight (hypothetical)",
        "New talks to limit emerging tech-based arms (hypothetical)"
    ],
    "Signatories": [
        "US, USSR", "US, USSR, UK", "US, USSR, UK", "US, USSR", "US, USSR, and other European states",
        "US, USSR", "US, USSR", "US, Russia, UK, Ukraine", "NATO members, Russia", "US, Russia",
        "US, Russia", "US, Russia", "Ukraine, Russia, OSCE", "Ukraine, Russia, Germany, France",
        "US, Russia", "Ukraine, Russia, OSCE", "Ukraine, Russia, US, EU", "US, Russia"
    ],
    "Status": [
        "Completed 1945", "Implemented", "Implemented", "Expired 1977", "Still in effect",
        "US withdrew 2019, Russia withdrew 2023", "Expired 2009", "Russia claimed violation in 2014",
        "Relations suspended 2014", "Never fully implemented, US withdrew 2002", "Superseded by New START",
        "Extended until 2026", "Limited implementation", "Limited implementation", "Active until 2026",
        "Partially implemented (hypothetical)", "Under negotiation (hypothetical)", "Initial talks ongoing (hypothetical)"
    ],
    "Type": [
        "Economic/Military Aid", "Post-War Settlement", "Post-War Settlement", "Arms Control",
        "Security/Human Rights", "Arms Control", "Arms Control", "Security", "Security Cooperation",
        "Arms Control", "Arms Control", "Arms Control", "Ceasefire", "Ceasefire", "Arms Control",
        "Ceasefire", "Territorial/Security", "Arms Control"
    ],
    "Reference": [
        "U.S. Department of State, 'Lend-Lease and Military Aid to the Allies in the Early Years of World War II'",
        "U.S. Department of State, Office of the Historian, 'The Yalta Conference, 1945'",
        "U.S. Department of State, Office of the Historian, 'The Potsdam Conference, 1945'",
        "U.S. Department of State, 'Strategic Arms Limitations Talks/Treaty (SALT) I and II'",
        "Organization for Security and Co-operation in Europe, 'Helsinki Final Act'",
        "U.S. Department of State, 'INF Treaty'", "U.S. Department of State, 'START I'",
        "UN Document A/49/765", "NATO, 'Founding Act'", "U.S. Department of State, 'START II'",
        "U.S. Department of State, 'SORT Treaty'", "U.S. Department of State, 'New START Treaty'",
        "OSCE, 'Minsk Protocol'", "United Nations, 'Minsk II'", "U.S. Department of State, 'New START Extension 2021'",
        "OSCE, 'Donbas Ceasefire Agreement 2023' (hypothetical)", "UN, 'Crimea Status Accord 2024' (hypothetical)",
        "U.S. Department of State, 'Arms Limitation Talks 2025' (hypothetical)"
    ]
}

territory_references = {
    "Formation of USSR (1922)": "Declaration and Treaty on the Formation of the Union of Soviet Socialist Republics, December 1922",
    "Crimea Transfer (1954)": "Presidium of the Supreme Soviet of the USSR, Decree of February 19, 1954",
    "USSR Dissolution (1991)": "Belavezha Accords and Alma-Ata Protocol, December 1991",
    "Crimea Annexation (2014)": "Treaty on Accession of the Republic of Crimea to Russia, March 18, 2014 (not recognized internationally)",
    "2022 Invasion": "Multiple sources including UN General Assembly resolutions condemning the invasion",
    "Crimea Status Accord 2024 (Hypothetical)": "UN, 'Crimea Status Accord 2024' (hypothetical resolution)"
}

treaties_df = pd.DataFrame(treaties_data)
treaties_df['Date'] = pd.to_datetime(treaties_df['Date'])
treaties_df['Year'] = treaties_df['Date'].dt.year
treaties_df['End_Date'] = treaties_df['Date'] + pd.DateOffset(months=3)

territorial_events = {
    1922: "Formation of USSR",
    1954: "Crimea transferred to Ukrainian SSR",
    1991: "Dissolution of USSR, Ukrainian independence",
    2014: "Russia annexes Crimea",
    2022: "Russia invades Ukraine",
    2024: "Crimea Status Accord (hypothetical)"
}

def render_map(selected_year):
    closest_events = sorted([(abs(year - selected_year), year) for year in territorial_events.keys()])
    if closest_events[0][0] <= 3:
        st.info(f"**Historical Context ({closest_events[0][1]}):** {territorial_events[closest_events[0][1]]}")
    
    st.subheader(f"Territorial Control in {selected_year}")
    
    if selected_year < 1922:
        map_title = "Post-WWI Period (Early Soviet Russia)"
        ukraine_status = "Various entities/disputed"
        russia_status = "Early Soviet Russia"
    elif selected_year < 1991:
        map_title = "Soviet Period"
        ukraine_status = "Ukrainian SSR (part of USSR)"
        russia_status = "Russian SFSR (part of USSR)"
    elif selected_year < 2014:
        map_title = "Post-Soviet Period"
        ukraine_status = "Independent Ukraine"
        russia_status = "Russian Federation"
    elif selected_year < 2022:
        map_title = "Post-2014 Period"
        ukraine_status = "Ukraine (Crimea under Russian control)"
        russia_status = "Russian Federation (including Crimea)"
    elif selected_year < 2024:
        map_title = "Post-2022 Invasion"
        ukraine_status = "Ukraine (parts occupied by Russia)"
        russia_status = "Russian Federation (claims additional Ukrainian territories)"
    else:
        map_title = "Post-2024 Accord (Hypothetical)"
        ukraine_status = "Ukraine (Crimea status under negotiation)"
        russia_status = "Russian Federation (Crimea status disputed)"
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ukraine Status", ukraine_status)
    with col2:
        st.metric("Russia Status", russia_status)
    
    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        locations=['USA', 'RUS', 'UKR'], locationmode='ISO-3', z=[1, 2, 3],
        colorscale='Blues', showscale=False, marker_line_color='white', marker_line_width=0.5
    ))
    
    if selected_year < 1922:
        ukraine_color = 'lightgrey'
    elif selected_year < 1991:
        ukraine_color = 'red'
    elif selected_year < 2014:
        ukraine_color = 'yellow'
    elif selected_year < 2022:
        ukraine_color = 'yellow'
        fig.add_trace(go.Scattergeo(
            lon=[34], lat=[45], text='Crimea (Russian control)',
            mode='markers', marker=dict(size=10, color='red'), name='Crimea'
        ))
    elif selected_year < 2024:
        ukraine_color = 'yellow'
        fig.add_trace(go.Scattergeo(
            lon=[34, 37, 38, 36], lat=[45, 47, 48, 46],
            text=['Crimea', 'Donetsk', 'Luhansk', 'Zaporizhzhia/Kherson'],
            mode='markers', marker=dict(size=10, color='red'), name='Russian-occupied'
        ))
    else:
        ukraine_color = 'yellow'
        fig.add_trace(go.Scattergeo(
            lon=[34], lat=[45], text='Crimea (Disputed)',
            mode='markers', marker=dict(size=10, color='orange'), name='Crimea (Disputed)'
        ))
    
    fig.add_trace(go.Choropleth(
        locations=['UKR'], locationmode='ISO-3', z=[1],
        colorscale=[[0, ukraine_color], [1, ukraine_color]], showscale=False,
        marker_line_color='black', marker_line_width=1
    ))
    
    russia_color = 'red' if selected_year < 1991 else 'lightblue'
    fig.add_trace(go.Choropleth(
        locations=['RUS'], locationmode='ISO-3', z=[1],
        colorscale=[[0, russia_color], [1, russia_color]], showscale=False,
        marker_line_color='black', marker_line_width=1
    ))
    
    fig.add_trace(go.Choropleth(
        locations=['USA'], locationmode='ISO-3', z=[1],
        colorscale=[[0, 'blue'], [1, 'blue']], showscale=False,
        marker_line_color='black', marker_line_width=1
    ))
    
    fig.update_geos(
        projection_type="natural earth", showcoastlines=True, coastlinecolor="Black",
        showland=True, landcolor="lightgrey", showocean=True, oceancolor="lightblue",
        showlakes=True, lakecolor="lightblue", showcountries=True, countrycolor="Black"
    )
    
    fig.update_layout(
        title=dict(text=map_title, x=0.5), height=600, margin=dict(l=0, r=0, t=50, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"map_{selected_year}")
    
    st.markdown("""
    **Map Legend:**
    - 🟦 USA
    - 🟥 Soviet Union territories (pre-1991)
    - 🔵 Russian Federation (post-1991)
    - 🟨 Independent Ukraine (post-1991)
    - 🔴 Russian-occupied/claimed territories
    - 🟧 Disputed territories (post-2024 hypothetical)
    *Note: Simplified visualization, not exact boundaries.*
    """)

def personal_finance_calculator():
    st.title("Personal Finance Calculators")
    
    page = st.sidebar.radio("Select Calculator", ["Novated Lease", "Mortgage"])
    
    if page == "Novated Lease":
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
            new_car_value, interest_rate, lease_term, tax_rate, gst_included,
            annual_fuel, annual_maintenance, annual_tyres, annual_finance_costs, annual_registration_insurance
        )

        ownership_cost, final_car_value = calculate_car_ownership_costs(
            current_car_value, years, annual_maintenance, annual_registration_insurance, annual_fuel
        )

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
        fig.update_layout(title='Asset Value Over Time', xaxis_title='Years', yaxis_title='Value ($)',
                          legend=dict(x=0.01, y=0.99), height=400)
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

    elif page == "Mortgage":
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

def hobby_page():
    st.title("Historical Treaties and Territorial Evolution: US, Russia, and Ukraine")
    st.markdown("""
    This application visualizes significant treaties and agreements between the United States, 
    Russia (including Soviet Union), and Ukraine, along with the territorial evolution over time.
    """)
    
    with st.sidebar:
        st.header("References & Resources")
        search_term = st.text_input("Search Treaties:", "")
        sidebar_view = st.radio("View References By:", ["Treaties", "Territorial Events", "Further Reading"])
        
        if sidebar_view == "Treaties":
            st.subheader("Treaty References")
            filtered_treaties = treaties_df
            if search_term:
                filtered_treaties = treaties_df[
                    treaties_df['Treaty Name'].str.contains(search_term, case=False) |
                    treaties_df['Description'].str.contains(search_term, case=False) |
                    treaties_df['Signatories'].str.contains(search_term, case=False)
                ]
            for idx, row in filtered_treaties.iterrows():
                with st.expander(f"{row['Treaty Name']} ({row['Year']})"):
                    st.write(f"**Date:** {row['Date'].strftime('%B %d, %Y')}")
                    st.write(f"**Type:** {row['Type']}")
                    st.write(f"**Signatories:** {row['Signatories']}")
                    st.write(f"**Status:** {row['Status']}")
                    st.write(f"**Description:** {row['Description']}")
                    st.write(f"**Source:** {row['Reference']}")
        
        elif sidebar_view == "Territorial Events":
            st.subheader("Territorial Changes")
            for event, reference in territory_references.items():
                with st.expander(event):
                    st.write(f"**Reference:** {reference}")
                    if "USSR (1922)" in event:
                        st.write("The Union of Soviet Socialist Republics was formed, with the Ukrainian SSR as one of the founding republics.")
                    elif "Crimea Transfer (1954)" in event:
                        st.write("The Crimean Oblast was transferred from the Russian SFSR to the Ukrainian SSR within the Soviet Union.")
                    elif "USSR Dissolution (1991)" in event:
                        st.write("Ukraine declared independence and was recognized internationally as a sovereign state with its Soviet-era borders.")
                    elif "Crimea Annexation (2014)" in event:
                        st.write("Following the Revolution of Dignity in Ukraine, Russia annexed Crimea, which is not recognized by most UN member states.")
                    elif "2022 Invasion" in event:
                        st.write("Russia launched a full-scale invasion of Ukraine and currently occupies portions of eastern and southern Ukraine.")
                    elif "Crimea Status Accord 2024" in event:
                        st.write("Hypothetical accord addressing Crimea’s status under international oversight.")
        
        else:
            st.subheader("Further Reading")
            st.markdown("""
            **Books:**
            - Plokhy, Serhii. "The Last Empire: The Final Days of the Soviet Union"
            - Sarotte, Mary Elise. "Not One Inch"
            - Kotkin, Stephen. "Armageddon Averted"
            **Academic Resources:**
            - Harvard Ukrainian Research Institute
            - Wilson Center Digital Archive
            - U.S. Department of State - Office of the Historian
            **Legal Documents:**
            - United Nations Treaty Collection
            - Library of Congress - Treaties and International Agreements
            """)
        
        st.markdown("---")
        st.caption("Data compiled from official sources, updated March 01, 2025.")

    tab1, tab2, tab3 = st.tabs(["Treaties Timeline", "Territorial Evolution", "About"])

    with tab1:
        st.header("Historical Treaties and Agreements")
        st.subheader("Filter Options")
        col1, col2 = st.columns(2)
        with col1:
            selected_types = st.multiselect(
                "Select Treaty Types",
                options=sorted(treaties_df["Type"].unique()),
                default=sorted(treaties_df["Type"].unique())
            )
        with col2:
            year_range = st.slider(
                "Year Range",
                min_value=int(treaties_df["Year"].min()),
                max_value=int(treaties_df["Year"].max()),
                value=(int(treaties_df["Year"].min()), int(treaties_df["Year"].max()))
            )
        
        filtered_df = treaties_df[
            (treaties_df["Type"].isin(selected_types)) &
            (treaties_df["Year"] >= year_range[0]) &
            (treaties_df["Year"] <= year_range[1])
        ]
        
        st.subheader("Treaties Timeline")
        if not filtered_df.empty:
            fig = px.bar(
                filtered_df, x="Date", y="Treaty Name", color="Type", orientation='h',
                height=600, hover_data=["Description", "Signatories", "Status"]
            )
            fig.update_layout(
                title="Timeline of Treaties and Agreements", xaxis_title="Date", yaxis_title="Treaty",
                legend_title="Treaty Type", yaxis=dict(categoryorder='category ascending'),
                xaxis=dict(type='date', tickformat='%Y', tickmode='auto', nticks=15)
            )
            for year in [1945, 1975, 1991, 2000, 2010, 2014, 2024]:
                fig.add_vline(x=pd.Timestamp(f"{year}-01-01"), line_dash="dash", line_color="gray", opacity=0.7)
            st.plotly_chart(fig, use_container_width=True, key="treaties_timeline")
        
        st.subheader("Treaty Details")
        st.dataframe(
            filtered_df[["Treaty Name", "Date", "Signatories", "Type", "Status", "Description"]],
            hide_index=True, use_container_width=True
        )

    with tab2:
        st.header("Territorial Evolution")
        if 'selected_year' not in st.session_state:
            st.session_state.selected_year = 1991
        if 'playing' not in st.session_state:
            st.session_state.playing = False

        col1, col2 = st.columns([3, 1])
        with col1:
            st.session_state.selected_year = st.slider(
                "Select Year", min_value=1920, max_value=2024, value=st.session_state.selected_year,
                step=1, key="year_slider"
            )
        with col2:
            play_button = st.button("Play Evolution", key="play_button")

        if play_button or st.session_state.playing:
            st.session_state.playing = True
            placeholder = st.empty()
            for year in range(1920, 2025):
                if not st.session_state.playing:
                    break
                st.session_state.selected_year = year
                with placeholder.container():
                    st.write(f"Year: {year}")
                    render_map(year)
                    time.sleep(0.1)
            st.session_state.playing = False
        else:
            render_map(st.session_state.selected_year)

    with tab3:
        st.header("About This Application")
        st.markdown("""
        ### Purpose
        This application provides a visual overview of diplomatic history and territorial changes involving the US, Russia/USSR, and Ukraine up to March 01, 2025.
        
        ### Data Sources
        - U.S. Department of State archives
        - United Nations Treaty Collection
        - Hypothetical entries based on trends as of March 01, 2025
        
        ### Methodology
        - Includes major agreements and hypothetical future treaties
        - Territorial visualization simplified to key phases
        
        ### Limitations
        - Hypothetical treaties are speculative
        - Territorial maps are illustrative, not precise
        
        ### Usage Guide
        1. Explore references in the sidebar
        2. Filter treaties in the Treaties tab
        3. Use the slider or play button in the Territorial tab
        """)
        st.markdown("---")
        st.markdown("Created for educational purposes, updated March 01, 2025.")

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", ["Hobby", "Personal Finance Cal"])
    
    if page == "Personal Finance Cal":
        personal_finance_calculator()
    elif page == "Hobby":
        hobby_page()

if __name__ == "__main__":
    main()