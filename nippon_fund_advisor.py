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

# --- Fund Recommendation Logic ---
def recommend_funds(df, horizon, risk, goal):
    keyword_map = {
        ("Long Term (5+ years)", "High", "Wealth Growth"): "Small Cap",
        ("Medium Term (3-5 years)", "Medium", "Capital Preservation"): "Large Cap",
        ("Short Term (1-2 years)", "Low", "Regular Income"): "Low Duration",
        ("Medium Term (3-5 years)", "High", "Wealth Growth"): "Mid Cap",
        ("Long Term (5+ years)", "Medium", "Capital Preservation"): "Balanced",
        ("Short Term (1-2 years)", "Medium", "Wealth Growth"): "Savings",
    }
    keyword = keyword_map.get((horizon, risk, goal), "Large Cap")
    filtered = df[df['Scheme Name'].str.contains(keyword, case=False, na=False)]
    top_funds = filtered['Scheme Name'].unique().tolist()[:3]

    if top_funds:
        return top_funds, keyword
    else:
        return df['Scheme Name'].unique().tolist()[:3], None

# --- Sidebar: Collect User Preferences ---
with st.sidebar:
    st.header("Investor Profile")
    with st.form("profile_form"):
        investment_horizon = st.selectbox("What is your investment horizon?", ["Short Term (1-2 years)", "Medium Term (3-5 years)", "Long Term (5+ years)"])
        risk_tolerance = st.selectbox("What is your risk appetite?", ["Low", "Medium", "High"])
        goal_type = st.selectbox("Your investment goal?", ["Wealth Growth", "Regular Income", "Capital Preservation"])
        submitted = st.form_submit_button("Update Recommendation")

# --- Always recompute if submitted or profile changed ---
current_profile = (investment_horizon, risk_tolerance, goal_type)
last_profile = st.session_state.get("last_profile")

if submitted or current_profile != last_profile:
    top_schemes, reason = recommend_funds(nippon_df, *current_profile)
    st.session_state.best_schemes = top_schemes
    st.session_state.recommend_reason = reason
    st.session_state.last_profile = current_profile

best_schemes = st.session_state.get("best_schemes", [])
recommend_reason = st.session_state.get("recommend_reason")

# --- Display Recommended Schemes ---
st.header("Best Match for You")
if best_schemes:
    for idx, scheme in enumerate(best_schemes):
        st.success(f"#{idx+1} Recommendation: **{scheme}**")
    if recommend_reason:
        st.markdown(f"_Why these funds?_ Matched to category: **{recommend_reason}**.")
else:
    st.warning("No recommendation yet. Please select a profile.")

# --- Compare NAV Stats of Top 3 Schemes ---
if best_schemes:
    st.subheader("🔍 Compare Recommended Funds")
    nav_stats = []
    for name in best_schemes:
        df = nippon_df[nippon_df['Scheme Name'] == name]
        df = df.sort_values("Date")
        if not df.empty:
            avg = round(df['Net Asset Value'].mean(), 2)
            max_ = round(df['Net Asset Value'].max(), 2)
            min_ = round(df['Net Asset Value'].min(), 2)
            nav_stats.append({"Scheme": name, "Avg NAV": avg, "Max NAV": max_, "Min NAV": min_})

    if nav_stats:
        stat_df = pd.DataFrame(nav_stats)
        st.dataframe(stat_df, use_container_width=True)

# --- Prepare Data for Top Scheme ---
best_scheme = best_schemes[0] if best_schemes else None
scheme_data = nippon_df[nippon_df['Scheme Name'] == best_scheme].copy()
scheme_data = scheme_data.sort_values('Date')

# --- Key Stats ---
if best_scheme and not scheme_data.empty:
    st.subheader("NO.1 FUND SUMMARY")
    avg_nav = round(scheme_data['Net Asset Value'].mean(), 2)
    max_nav = round(scheme_data['Net Asset Value'].max(), 2)
    min_nav = round(scheme_data['Net Asset Value'].min(), 2)

    col1, col2, col3 = st.columns(3)
    col1.metric("Average NAV", f"₹{avg_nav}")
    col2.metric("Highest NAV", f"₹{max_nav}")
    col3.metric("Lowest NAV", f"₹{min_nav}")

    st.subheader("ADVISOR INSIGHT")
    st.info("These funds align with your risk profile. Consider SIPs for disciplined investing.")
else:
    st.warning("No NAV data available for top scheme.")

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
