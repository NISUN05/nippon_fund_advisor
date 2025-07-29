import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import requests
from io import StringIO

st.set_page_config(
    page_title="NIPPON FUND ADVISOR",
    page_icon="📈",
    layout="wide"
)

# --- Homepage Banner ---
st.title("Nippon Fund Advisor")
st.markdown("""
Welcome to **Nippon Fund Advisor** – your personalized guide to the best Nippon India mutual funds, tailored to your investment goals.
Live NAV data from [AMFI India](https://www.amfiindia.com/).
""")

# --- Fetch Real NAV Data from AMFI ---
@st.cache_data(ttl=86400)
def load_amfi_nav():
    url = "https://www.amfiindia.com/spages/NAVAll.txt"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to fetch NAV data from AMFI.")
        return pd.DataFrame()

    raw_lines = response.text.splitlines()
    start_idx = None
    for i, line in enumerate(raw_lines):
        if line.strip().startswith("Scheme Code;"):
            start_idx = i
            break

    if start_idx is None:
        st.error("Unable to parse AMFI data format.")
        return pd.DataFrame()

    csv_data = "\n".join(raw_lines[start_idx:])
    df = pd.read_csv(StringIO(csv_data), sep=';')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Scheme Name'])
    df['Net Asset Value'] = pd.to_numeric(df['Net Asset Value'].astype(str).str.replace(',', ''), errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df.dropna(subset=['Date'])

nav_df = load_amfi_nav()
nippon_df = nav_df[nav_df['Scheme Name'].str.contains("Nippon", case=False, na=False)]
scheme_names = sorted(nippon_df['Scheme Name'].unique())

# --- Sidebar: Collect User Preferences ---
with st.sidebar:
    st.header("Investor Profile")
    with st.form("profile_form"):
        investment_horizon = st.selectbox("What is your investment horizon?", ["Short Term (1-2 years)", "Medium Term (3-5 years)", "Long Term (5+ years)"])
        risk_tolerance = st.selectbox("What is your risk appetite?", ["Low", "Medium", "High"])
        goal_type = st.selectbox("Your investment goal?", ["Wealth Growth", "Regular Income", "Capital Preservation"])
        submitted = st.form_submit_button("Update Recommendation")

# --- Fund Recommendation Logic ---
def recommend_fund(df, horizon, risk, goal):
    rating_map = {
        ("Long Term (5+ years)", "High", "Wealth Growth"): "Nippon India Small Cap Fund - Growth",
        ("Medium Term (3-5 years)", "Medium", "Capital Preservation"): "Nippon India Large Cap Fund - Growth",
        ("Short Term (1-2 years)", "Low", "Regular Income"): "Nippon India Low Duration Fund - Growth",
    }
    for key, scheme in rating_map.items():
        if key == (horizon, risk, goal) and scheme in df['Scheme Name'].values:
            return scheme
    return scheme_names[0]

if submitted:
    best_scheme = recommend_fund(nippon_df, investment_horizon, risk_tolerance, goal_type)
    st.session_state["best_scheme"] = best_scheme

best_scheme = st.session_state.get("best_scheme", recommend_fund(nippon_df, investment_horizon, risk_tolerance, goal_type))

# --- Display Recommended Scheme ---
st.header("Best Match for You")
st.success(f"Based on your profile, we recommend: **{best_scheme}**")

# --- Prepare Data for Selected Scheme ---
scheme_data = nippon_df[nippon_df['Scheme Name'] == best_scheme].copy()
scheme_data = scheme_data.sort_values('Date')

# --- Key Stats ---
if not scheme_data.empty:
    st.subheader("FUND SUMMARY")
    avg_nav = round(scheme_data['Net Asset Value'].mean(), 2)
    max_nav = round(scheme_data['Net Asset Value'].max(), 2)
    min_nav = round(scheme_data['Net Asset Value'].min(), 2)

    col1, col2, col3 = st.columns(3)
    col1.metric("Average NAV", f"₹{avg_nav}")
    col2.metric("Highest NAV", f"₹{max_nav}")
    col3.metric("Lowest NAV", f"₹{min_nav}")

    st.subheader("ADVISOR INSIGHT")
    st.info("This fund aligns with your risk profile. Consider SIPs for disciplined investing.")
else:
    st.warning("No NAV data available for this scheme.")

# --- Show All Nippon Fund Schemes with Search + Tags ---
st.header("📚 Browse & Explore Funds")
search_text = st.text_input("Search by scheme name:", "")
filtered_df = nippon_df[nippon_df['Scheme Name'].str.contains(search_text, case=False, na=False)]

selected_scheme_browse = st.selectbox("Choose a scheme to view details:", sorted(filtered_df['Scheme Name'].unique()))
selected_data = filtered_df[filtered_df['Scheme Name'] == selected_scheme_browse].sort_values('Date')

if not selected_data.empty:
    st.subheader(f"Fund Details: {selected_scheme_browse}")
    tag = "High Risk / High Return" if "Small Cap" in selected_scheme_browse else ("Moderate Risk" if "Large Cap" in selected_scheme_browse else "Low Risk")
    tag_style = {
        "High Risk / High Return": "color: #E63946; font-weight: bold; font-family: 'Georgia', serif; font-size: 18px;",
        "Moderate Risk": "color: #F4A261; font-weight: bold; font-family: 'Georgia', serif; font-size: 18px;",
        "Low Risk": "color: #2A9D8F; font-weight: bold; font-family: 'Georgia', serif; font-size: 18px;"
    }
    st.markdown(f"<div style='{tag_style[tag]}'>Risk Profile: {tag}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:16px;'>Latest NAV: ₹{selected_data['Net Asset Value'].iloc[-1]:.2f}</div>", unsafe_allow_html=True)
else:
    st.warning("No data available for selected scheme.")
