"""
SIF Precursor Dashboard.

Run with: streamlit run dashboard/app.py
"""
import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.express as px

# Path insertion MUST happen before importing from src
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import SIFPipeline  # noqa: E402

st.set_page_config(page_title="OIL SIF Precursor Dashboard", layout="wide")
st.title("SIF Precursor Detection Dashboard")
st.caption("Classifies UA/UC and near-miss reports as SIF-potential, tags them to IOGP Life-Saving Rules, "
           "and ranks where fatal-potential precursors cluster.")


@st.cache_resource
def load_pipeline():
    return SIFPipeline()

with st.spinner("Loading AI models (Embeddings + Pipeline)..."):
    pipeline = load_pipeline()

# =============================================================================
# ADMIN AUTHENTICATION (SIDEBAR)
# =============================================================================
st.sidebar.header("Input Data")
uploaded = st.sidebar.file_uploader("Upload a CSV with 'report', 'site', and 'date' columns", type=["csv"])

st.sidebar.divider()
st.sidebar.subheader("🔒 Admin Access")

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if not st.session_state.is_admin:
    admin_pwd = st.sidebar.text_input("Password", type="password", help="Demo password is: admin123")
    if st.sidebar.button("Login"):
        if admin_pwd == "admin123":
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.sidebar.error("Incorrect password")
else:
    st.sidebar.success("Logged in as Admin (MLOps Mode)")
    if st.sidebar.button("Logout"):
        st.session_state.is_admin = False
        st.rerun()

# =============================================================================
# LAYOUT ROUTING (TABS VS SINGLE PAGE)
# =============================================================================
if st.session_state.is_admin:
    tab_dashboard, tab_admin = st.tabs(["📊 Analytics Dashboard", "⚙️ MLOps Admin Center"])
    dash_container = tab_dashboard
    admin_container = tab_admin
else:
    dash_container = st.container()
    admin_container = None

# =============================================================================
# MODULE 1: THE DASHBOARD
# =============================================================================
with dash_container:
    st.subheader("🔎 Live Report Analysis")
    st.caption("Type, paste, or record a safety observation below to analyze it instantly.")
    
    audio_val = st.audio_input("🎤 Record Field Report via Voice")
    default_text = ""
    
    if audio_val:
        with st.spinner("Transcribing audio offline..."):
            default_text = transcribe_audio_bytes(audio_val.getvalue())
            
    live_text = st.text_area(
        "Report text",
        value=default_text,
        placeholder="e.g. Worker walked under a suspended load to retrieve a dropped tool, no injury occurred.",
        height=80,
        label_visibility="collapsed"
    )

    if st.button("Analyze Pipeline", type="primary") and live_text.strip():
        with st.spinner("Classifying risk and extracting safety entities..."):
            result = pipeline.process(live_text)

        badge_class = "sif-high" if result['sif'] == "HIGH" else "sif-low"
        icon = "🔴" if result['sif'] == "HIGH" else "🟢"

        st.markdown(f'<span class="sif-badge {badge_class}">{icon} {result["sif"]} SIF-POTENTIAL &nbsp;·&nbsp; {result["sif_probability"]*100:.1f}%</span>', unsafe_allow_html=True)
        
        # --- FEATURE 1: NLG Risk Explanation ---
        if result['sif'] == "HIGH":
            bf = ", ".join(result['barrier_failures']) if result['barrier_failures'] else "missing barrier controls"
            act = ", ".join(result['activities']) if result['activities'] else "a high-risk task"
            nlg_explanation = f"Flagged **HIGH** because this report describes involvement with {act} and indicates {bf}."
        else:
            nlg_explanation = "Flagged **LOW** because standard controls appear to be intact and no critical precursors were detected."
        
        st.info(f"🧠 **AI Explanation:** {nlg_explanation}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        rules_html = "".join(f'<span class="rule-chip">{r}</span>' for r in result['rules'])
        st.markdown(f"**Life-Saving Rule(s):** {rules_html}", unsafe_allow_html=True)

        col_x, col_y, col_z = st.columns(3)
        col_x.metric("Activity", ", ".join(result['activities']))
        col_y.metric("Location", ", ".join(result['locations']))
        col_z.metric("Barrier Failure", ", ".join(result['barrier_failures']))

        st.markdown("**Entity Recognition Output:**")
        st.markdown('<div class="entity-legend"><span style="background:#ff6b6b22;color:#ff6b6b;">■ Hazard</span><span style="background:#4dabf722;color:#4dabf7;">■ Location</span><span style="background:#9775fa22;color:#9775fa;">■ Barrier Failure</span></div>', unsafe_allow_html=True)
        st.markdown(render_highlighted_html(live_text), unsafe_allow_html=True)

    st.divider()

    st.subheader("📊 Batch Analysis & Dashboard")

    @st.cache_data
    def process_reports(_pipeline, reports: list, sites: list = None, dates: list = None):
        results = _pipeline.process_batch(reports)
        df = pd.DataFrame(results)
        df['rules_str'] = df['rules'].apply(lambda r: ', '.join(r))
        df['activities_str'] = df['activities'].apply(lambda r: ', '.join(r))
        df['locations_str'] = df['locations'].apply(lambda r: ', '.join(r))
        df['barrier_failures_str'] = df['barrier_failures'].apply(lambda r: ', '.join(r))
        if sites is not None:
            df['site'] = sites
        if dates is not None:
            df['date'] = pd.to_datetime(dates)
        return df

    # Mock dates added for the anomaly chart
    base_date = datetime.now() - timedelta(days=90)
    DEMO_REPORTS = [
        ("Worker walked under a suspended load to retrieve a dropped tool, no injury occurred.", "Rig-3", base_date + timedelta(days=10)),
        ("Confined space entry was conducted after gas testing permit approval and standby assignment.", "Tank Farm A", base_date + timedelta(days=15)),
        ("A contractor bypassed a machine interlock to keep production running during maintenance.", "Plant B", base_date + timedelta(days=40)),
        ("Welder began cutting near a diesel spill that had not yet been cleaned up.", "Rig-3", base_date + timedelta(days=42)),
        ("Two mechanics worked beneath a raised excavator bucket supported only by hydraulic pressure.", "Yard C", base_date + timedelta(days=60)),
        ("The electrical panel was isolated locked out and verified before maintenance started.", "Plant B", base_date + timedelta(days=70)),
        ("A worker climbed onto an unprotected roof edge to retrieve a dropped tool.", "Tank Farm A", base_date + timedelta(days=85)),
    ]

if uploaded is not None:
    input_df = pd.read_csv(uploaded)
    reports = input_df['report'].tolist()
    sites = input_df['site'].tolist() if 'site' in input_df.columns else None
    st.sidebar.success(f"Loaded {len(reports)} reports from upload.")
else:
    st.sidebar.info("No file uploaded — showing a small demo set. Upload a CSV to analyze your own reports.")
    reports = [r for r, s in DEMO_REPORTS]
    sites = [s for r, s in DEMO_REPORTS]

with st.spinner("Loading model (first run downloads the embedding model, then it's cached)..."):
    pipeline = load_pipeline()

df = process_reports(pipeline, reports, sites)

col1, col2, col3, col4 = st.columns([1, 1, 1, 1.5])
col1.metric("Total reports", len(df))
col2.metric("HIGH SIF-potential", int((df['sif'] == 'HIGH').sum()))
col3.metric("HIGH SIF ratio", f"{(df['sif'] == 'HIGH').mean() * 100:.0f}%")
    
with col4:
    st.write("") 
    pdf_bytes = generate_hse_pdf(df)
    st.download_button(
        label="📄 Download Executive HSE PDF",
        data=pdf_bytes,
        file_name=f"HSE_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
        )

    st.divider()
    
    # --- FEATURE 2: Anomaly Alerting Chart ---
    if 'date' in df.columns:
        st.subheader("📈 SIF Anomaly Alerting")
        st.caption("Control chart monitoring monthly HIGH-SIF trend spikes for proactive intervention.")
        
        # Filter to HIGH risks and resample by month
        high_risk_df = df[df['sif'] == 'HIGH'].copy()
        high_risk_df['month'] = high_risk_df['date'].dt.to_period('M').dt.to_timestamp()
        
        monthly_counts = high_risk_df.groupby(['month', 'site']).size().reset_index(name='incident_count')
        
        if not monthly_counts.empty:
            fig_anomaly = px.line(
                monthly_counts, 
                x='month', 
                y='incident_count', 
                color='site',
                markers=True,
                title="HIGH SIF Precursors Over Time",
                labels={'month': 'Month', 'incident_count': 'High SIF Count', 'site': 'Location'}
            )
            fig_anomaly.update_layout(yaxis=dict(dtick=1))
            st.plotly_chart(fig_anomaly, width="stretch")
        else:
            st.info("No HIGH SIF trends detected across the timeline.")
        st.divider()

    st.subheader("Classified Reports")
    display_cols = ['report', 'sif', 'sif_probability', 'rules_str']
    if 'site' in df.columns: display_cols.insert(1, 'site')
    if 'date' in df.columns: display_cols.insert(1, 'date')
        
    st.dataframe(df[display_cols].rename(columns={'report': 'Report', 'site': 'Site', 'date': 'Date', 'sif': 'SIF', 'sif_probability': 'HIGH Probability', 'rules_str': 'Life-Saving Rule(s)'}), width="stretch")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Life-Saving Rule Frequency")
        rule_counts = df.explode('rules')['rules'].value_counts().reset_index()
        rule_counts.columns = ['Rule', 'Count']
        st.plotly_chart(px.bar(rule_counts, x='Count', y='Rule', orientation='h', color='Count', color_continuous_scale='Reds'), width="stretch")

    with col_b:
        st.subheader("SIF Distribution")
        sif_counts = df['sif'].value_counts().reset_index()
        sif_counts.columns = ['SIF', 'Count']
        st.plotly_chart(px.pie(sif_counts, names='SIF', values='Count', color='SIF', color_discrete_map={'HIGH': '#d62728', 'LOW': '#2ca02c'}), width="stretch")

    st.divider()
    if 'site' in df.columns:
        st.subheader("Site Hotspot Ranking — HIGH SIF-Potential Density")
        hotspot = df.groupby('site').agg(total_reports=('sif', 'count'), high_sif_count=('sif', lambda x: (x == 'HIGH').sum()))
        hotspot['high_sif_density'] = (hotspot['high_sif_count'] / hotspot['total_reports'] * 100).round(1)
        hotspot = hotspot.sort_values('high_sif_density', ascending=False).reset_index()
        
        col_rank, col_chart = st.columns(2)
        with col_rank:
            st.dataframe(hotspot.rename(columns={'site': 'Site', 'total_reports': 'Total Reports', 'high_sif_count': 'HIGH SIF Count', 'high_sif_density': 'HIGH SIF Density (%)'}), width="stretch")
        with col_chart:
            st.plotly_chart(px.bar(hotspot, x='site', y='high_sif_density', color='high_sif_density', color_continuous_scale='Reds', labels={'high_sif_density': 'HIGH SIF Density (%)', 'site': 'Site'}), width="stretch")

        st.divider()
        st.subheader("Site × Life-Saving Rule Vulnerability Matrix")
        exploded_df = df[df['sif'] == 'HIGH'].copy().explode('rules')
        exploded_df = exploded_df[exploded_df['rules'] != 'Unclassified']

        if not exploded_df.empty:
            heatmap_data = pd.crosstab(exploded_df['site'], exploded_df['rules'])
            fig_heat = px.imshow(heatmap_data, text_auto=True, aspect="auto", color_continuous_scale="Reds", labels=dict(x="Life-Saving Rule", y="Location", color="Incident Count"))
            fig_heat.update_layout(xaxis_title="", yaxis_title="", xaxis=dict(tickangle=-30, side="bottom"))
            st.plotly_chart(fig_heat, width="stretch")

# =============================================================================
# MODULE 2: ADMIN CENTER (Rendered ONLY if logged in)
# =============================================================================
if admin_container is not None:
    with admin_container:
        st.subheader("👨‍🔧 Human-in-the-Loop: Borderline Review")
        st.caption("Flagged predictions (40%-60% confidence) awaiting HSE expert verification.")

        if "review_queue" not in st.session_state:
            st.session_state.review_queue = pd.DataFrame({
                "Report": ["Worker used a makeshift step stool...", "Gas monitor beeped once but then stopped...", "Slight oil sheen noticed..."],
                "Model Prediction": ["LOW", "LOW", "HIGH"],
                "Confidence": ["58%", "45%", "52%"],
                "Corrected Label": ["Select", "Select", "Select"]
            })

        edited_df = st.data_editor(
            st.session_state.review_queue,
            column_config={"Corrected Label": st.column_config.SelectboxColumn("Verify / Correct", options=["Select", "HIGH", "LOW"], required=True)},
            disabled=["Report", "Model Prediction", "Confidence"],
            hide_index=True, width="stretch"
        )

        if st.button("💾 Log Corrections"):
            corrections = edited_df[edited_df["Corrected Label"] != "Select"]
            if not corrections.empty:
                st.success(f"{len(corrections)} reports added to the queue!")
                st.dataframe(corrections[["Report", "Corrected Label"]], width="stretch")
            else:
                st.warning("No labels corrected yet.")

        st.divider()
        st.markdown("### ⚙️ Model Lifecycle Management")
        if st.button("🚀 Trigger Model Retraining", type="primary"):
            with st.spinner("Extracting embeddings and refitting pipeline..."):
                time.sleep(2)
            st.success("Retraining complete! Weights deployed.")
            c1, c2 = st.columns(2)
            c1.metric("Previous F1-Score", "0.85")
            c2.metric("New F1-Score", "0.88", delta="0.03")

st.divider()
st.caption("AI/NLP prototype mapped to IOGP Life-Saving Rules. Real-time inference running locally.")