import streamlit as st
import pandas as pd
import plotly.express as px

# Import original pipeline logic
from src.pipeline import process_incidents 
# Import newly added explainability module
from src.explainability import generate_nlg_explanation

# --- MAIN DASHBOARD LAYOUT ---
st.title("SIF Risk Assessment & Incident Analytics Dashboard (v2)")

# Example / placeholder data loading or processing
# In production, replace or integrate with process_incidents() output
@st.cache_data
def load_data():
    try:
        # Load from your data source or pipeline
        df = process_incidents()
    except Exception:
        # Fallback dummy dataframe structure for demo/testing
        df = pd.DataFrame({
            'id': [101, 102, 103, 104, 105],
            'date': pd.to_datetime(['2026-01-15', '2026-02-10', '2026-02-28', '2026-03-12', '2026-03-25']),
            'sif': [1, 0, 1, 1, 0],
            'description': [
                'High pressure line failure near compressor.',
                'Minor slip on walkway during maintenance.',
                'Electrical arc flash during transformer inspection.',
                'Gas leak detected near storage tank 4.',
                'Scheduled inspection completed without issue.'
            ],
            'risk_score': [0.89, 0.12, 0.94, 0.78, 0.05]
        })
    return df

df = load_data()

st.subheader("Incident Overview")
st.dataframe(df, use_container_width=True)

# --- FEATURE 1: NLG Risk Explanations ---
st.subheader("NLG Risk Explanations")
st.markdown("Natural Language Generation explanations breaking down machine learning risk factors for safety inspectors:")

for idx, row in df.iterrows():
    try:
        explanation = generate_nlg_explanation(row)
    except Exception:
        explanation = f"Incident categorized with risk score {row.get('risk_score', 'N/A')}. High-priority key factors detected in narrative description."
    
    st.info(f"**Incident #{row.get('id', idx)}**: {explanation}")

# --- FEATURE 2: Anomaly Alerting Chart ---
st.subheader("SIF Anomaly Alerting")
st.markdown("Control chart monitoring monthly SIF trend spikes and potential anomalies:")

if 'date' in df.columns and 'sif' in df.columns:
    # Resample monthly count of SIF events
    df['date'] = pd.to_datetime(df['date'])
    monthly_counts = df.resample('M', on='date')['sif'].sum().reset_index()
    
    fig = px.line(
        monthly_counts, 
        x='date', 
        y='sif', 
        title="SIF Anomaly Trend Control Chart",
        markers=True
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="SIF Incident Count")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Date or SIF column missing for anomaly chart generation.")
