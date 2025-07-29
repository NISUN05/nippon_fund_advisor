import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

# ------------------ FUND DATABASE ------------------
funds = [
    {
        "name": "Nippon India Small Cap Fund",
        "category": "Small Cap",
        "risk": "High",
        "goal": ["Wealth Creation"],
        "description": "Focuses on small-cap stocks with high growth potential. Suitable for aggressive investors with long-term horizon.",
        "cagr_5y": 27.3
    },
    {
        "name": "Nippon India Large Cap Fund",
        "category": "Large Cap",
        "risk": "Medium",
        "goal": ["Wealth Creation", "Retirement"],
        "description": "Invests in large, stable companies. Balanced growth and lower volatility.",
        "cagr_5y": 14.2
    },
    {
        "name": "Nippon India ELSS Tax Saver",
        "category": "ELSS",
        "risk": "Medium",
        "goal": ["Tax Saving", "Wealth Creation"],
        "description": "Save tax under 80C and grow wealth with a 3-year lock-in.",
        "cagr_5y": 17.5
    },
    {
        "name": "Nippon India Balanced Advantage Fund",
        "category": "Dynamic Asset Allocation",
        "risk": "Medium",
        "goal": ["Retirement", "Child Education", "Wealth Creation"],
        "description": "Auto-balances equity and debt based on market conditions. Great for medium risk investors.",
        "cagr_5y": 11.8
    },
    {
        "name": "Nippon India Liquid Fund",
        "category": "Liquid",
        "risk": "Low",
        "goal": ["Short-Term Saving"],
        "description": "Ultra-short duration fund with low risk. Better than a savings account for idle money.",
        "cagr_5y": 5.3
    },
    {
        "name": "Nippon India Multi Cap Fund",
        "category": "Multi Cap",
        "risk": "High",
        "goal": ["Wealth Creation"],
        "description": "Diversified across large, mid, and small caps. Ideal for long-term growth.",
        "cagr_5y": 18.7
    },
]

# ------------------ FUND RECOMMENDER ------------------
def recommend_funds(goal, risk):
    results = []
    for fund in funds:
        if goal in fund["goal"] and (
            risk == fund["risk"] or (risk == "High" and fund["risk"] in ["Medium", "High"])
        ):
            results.append(fund)
    return results

# ------------------ CAGR PROJECTION ------------------
def project_returns(amount, cagr, years):
    return round(amount * ((1 + cagr / 100) ** years), 2)

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title="Nippon India Fund Advisor", layout="centered")
st.title(" Nippon India Mutual Fund Advisor")
st.caption("Personalized recommendations based on your investment profile")

# 🧾 Input Section
col1, col2 = st.columns(2)
with col1:
    age = st.slider("Your Age", 18, 70, 30)
    salary = st.number_input("Monthly Salary (INR)", min_value=5000, step=1000)
    goal = st.selectbox("Your Investment Goal", ["Wealth Creation", "Retirement", "Tax Saving", "Child Education", "Short-Term Saving"])
with col2:
    expenses = st.number_input("Monthly Expenses (INR)", min_value=1000, step=500)
    risk = st.radio("Your Risk Tolerance", ["Low", "Medium", "High"])
    horizon = st.slider("Investment Horizon (Years)", 1, 30, 5)

invest_amount = st.number_input("How much do you want to invest monthly? (INR)", min_value=500, step=100)

if st.button("📈 Show My Fund Recommendations"):
    recs = recommend_funds(goal, risk)

    if not recs:
        st.warning("No matching funds found for your profile.")
    else:
        st.success(f"Here are {len(recs)} suitable funds for you:")
        for fund in recs:
            st.markdown(f"""
            ### {fund['name']}
            *Category:* {fund['category']}  
            *Risk Level:* {fund['risk']}  
            *CAGR (5Y):* {fund['cagr_5y']}%  
            **{fund['description']}**
            """)
            projected = project_returns(invest_amount * 12, fund["cagr_5y"], horizon)
            st.markdown(f"📊 **Projected Value (₹{invest_amount * 12}/yr for {horizon} yrs): ₹{projected:,}**")
            st.markdown("---")

        # Bar chart comparison
        chart_data = pd.DataFrame({
            "Fund": [f["name"] for f in recs],
            "Projected Value": [project_returns(invest_amount * 12, f["cagr_5y"], horizon) for f in recs]
        })
        fig = go.Figure([go.Bar(x=chart_data["Fund"], y=chart_data["Projected Value"], marker_color='crimson')])
        fig.update_layout(title="📊 Projected Returns Comparison", yaxis_title="₹ Value")
        st.plotly_chart(fig, use_container_width=True)
