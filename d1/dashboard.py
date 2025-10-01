import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List


st.title("Faculty Travel Survey Dashboard")
st.markdown("### Insights & Visualizations based on Faculty Travel Survey Responses")

CSV_PATH = r"e:\Gago\Faculty_Travel_Survey.csv"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data(CSV_PATH)
except FileNotFoundError:
    st.error(f"Could not find the CSV at: {CSV_PATH}. Make sure the file exists in the workspace.")
    st.stop()
except Exception as e:
    st.error(f"Error loading CSV: {e}")
    st.stop()

# KPIs
total_responses = len(df)
travel_mode_lower = df['Travel Mode'].fillna('').astype(str).str.lower()
private_mask = travel_mode_lower.str.contains('own car') | travel_mode_lower.str.contains('personal') | travel_mode_lower.str.contains('bike')
pct_private = (private_mask.sum() / total_responses * 100) if total_responses else 0
carpool_lower = df['Carpool Willingness'].fillna('').astype(str).str.lower()
open_to_carpool_mask = carpool_lower.isin(['yes', 'maybe'])
pct_open_carpool = (open_to_carpool_mask.sum() / total_responses * 100) if total_responses else 0
cab_issue_lower = df['Cab Availability Issues'].fillna('').astype(str).str.lower()
cab_issue_mask = cab_issue_lower.isin(['yes', 'sometimes'])
pct_cab_issues = (cab_issue_mask.sum() / total_responses * 100) if total_responses else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total responses", f"{total_responses}")
col2.metric("Private vehicle %", f"{pct_private:.0f}%")
col3.metric("Open to carpool %", f"{pct_open_carpool:.0f}%")
col4.metric("Report cab availability issues %", f"{pct_cab_issues:.0f}%")

st.subheader("1 Travel Mode Preferences")
mode_counts = df['Travel Mode'].fillna("(Missing)").value_counts()

fig1 = px.pie(values=mode_counts.values, names=mode_counts.index, title="Travel Mode Distribution", hole=0.3)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("Insight: Most faculty rely on private vehicles (Own Car, Bike). Shared transport usage (Ola/Uber, Carpool, Bus) is lower.")

st.subheader("2 Cab Availability Issues by Travel Mode")
df_mode_issue = df[['Travel Mode', 'Cab Availability Issues']].fillna('(Missing)')
ct = pd.crosstab(df_mode_issue['Travel Mode'], df_mode_issue['Cab Availability Issues'])

ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

fig2 = go.Figure()
for col in ct_pct.columns:
    fig2.add_trace(go.Bar(name=col, x=ct_pct.index, y=ct_pct[col]))
fig2.update_layout(barmode='stack', title='Cab Availability Issues across Travel Modes', yaxis_title='Percentage %')
st.plotly_chart(fig2, use_container_width=True)

st.markdown("Insight: Ola/Uber and Rapido users report higher availability issues, while Own Car and Bike users rarely face this.")

st.subheader("3 Carpool Willingness")
pool_counts = df['Carpool Willingness'].fillna('(Missing)').value_counts()

fig3 = px.bar(x=pool_counts.index, y=pool_counts.values, labels={'x':'Response','y':'Count'}, title='Carpool Willingness (Yes / No / Maybe)', color=pool_counts.index)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("Insight: Many faculty are open to carpooling (Yes/Maybe), but flexibility and autonomy concerns limit adoption.")

st.subheader("4 Reasons for Not Using Ola/Uber/Rapido Frequently")

def split_reasons(texts: pd.Series) -> List[str]:
    all_reasons: List[str] = []
    for item in texts.dropna().astype(str):
        item = item.replace('/', ',').replace(';', ',')
        parts = [p.strip() for p in item.split(',') if p.strip()]
        all_reasons.extend(parts)
    return all_reasons

reasons_series = df.get('Reason for not using Ola/Uber/Rapido frequently')
reasons_list = split_reasons(reasons_series) if reasons_series is not None else []
reasons_df = pd.Series([r.title() for r in reasons_list], name='reason').value_counts().reset_index()
reasons_df.columns = ['reason','count']

if not reasons_df.empty:
    fig4 = px.bar(reasons_df.head(15), x='count', y='reason', orientation='h', title='Top Reasons for Not Using Ola/Uber/Rapido', labels={'count':'Count','reason':'Reason'})
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info('No reasons recorded for not using Ola/Uber/Rapido frequently.')

st.markdown("Insight: Common barriers include High Cost, Availability Issues, Safety Concerns, Inconvenient Pickup/Drop, and Preference for Personal Vehicle.")

st.subheader("5 Reasons for Not Preferring Carpooling")

reasons_carpool_series = df.get('Reason for not preferring carpooling')
reasons_carpool_list = split_reasons(reasons_carpool_series) if reasons_carpool_series is not None else []
reasons_carpool_df = pd.Series([r.title() for r in reasons_carpool_list], name='reason').value_counts().reset_index()
reasons_carpool_df.columns = ['reason','count']

# ensure count is numeric
if not reasons_carpool_df.empty:
    reasons_carpool_df['count'] = pd.to_numeric(reasons_carpool_df['count'], errors='coerce').fillna(0).astype(int)
    try:
        if reasons_carpool_df['reason'].nunique() >= 2:
            fig5 = px.treemap(reasons_carpool_df.head(50), path=['reason'], values='count', title='Reasons for Not Preferring Carpooling')
            st.plotly_chart(fig5, use_container_width=True)
        else:
            fig5 = px.bar(reasons_carpool_df.head(50), x='count', y='reason', orientation='h', title='Reasons for Not Preferring Carpooling', labels={'count':'Count','reason':'Reason'})
            st.plotly_chart(fig5, use_container_width=True)
    except Exception:
        fig5 = px.bar(reasons_carpool_df.head(50), x='count', y='reason', orientation='h', title='Reasons for Not Preferring Carpooling', labels={'count':'Count','reason':'Reason'})
        st.plotly_chart(fig5, use_container_width=True)
else:
    st.info('No reasons recorded for not preferring carpooling.')

st.markdown("Insight: Faculty often mention inflexible schedules, autonomy, dependency, and safety concerns as reasons to avoid carpooling.")

# st.subheader("Recommendations")
# st.markdown("""
# - Carpool Pilot Program: Start within Greater Noida clusters where faculty live nearby.
# - Shuttle Service: University-organized transport for long routes (Ghaziabad, Gurgaon, Delhi).
# - Cost Mitigation: Negotiate with Ola/Uber for corporate discounts.
# - Safety Measures: Trusted faculty-only carpool groups, verified pickup points.
# - Incentives: Priority parking or fuel reimbursements for carpool participants.
# """)
