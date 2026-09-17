import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Isolated Heatmap Feature", layout="wide")

st.subheader("Site × Life-Saving Rule Vulnerability Matrix")
st.caption("Testing isolated heatmap component with mock data.")

# 1. Mock dataset simulating the main pipeline output
mock_data = {
    'site': ['Rig-3', 'Tank Farm A', 'Rig-3', 'Plant B', 'Plant B', 'Yard C', 'Rig-3', 'Tank Farm A'],
    'sif': ['HIGH', 'HIGH', 'HIGH', 'HIGH', 'LOW', 'HIGH', 'HIGH', 'HIGH'],
    'rules': [
        ['Line of Fire', 'Safe Mechanical Lifting'],
        ['Confined Space', 'Work Authorization'],
        ['Line of Fire'],
        ['Energy Isolation', 'Bypassing Safety Controls'],
        ['Driving'],
        ['Line of Fire', 'Working at Height'],
        ['Safe Mechanical Lifting'],
        ['Confined Space']
    ]
}
df = pd.DataFrame(mock_data)

# 2. Isolate HIGH risk reports and split the nested rule lists
high_risk_df = df[df['sif'] == 'HIGH'].copy()
exploded_df = high_risk_df.explode('rules')

# Remove unclassified rows to keep the matrix clean
exploded_df = exploded_df[exploded_df['rules'] != 'Unclassified']

if not exploded_df.empty:
    # 3. Generate the cross-tabulation matrix (Sites = Rows, Rules = Columns)
    heatmap_data = pd.crosstab(exploded_df['site'], exploded_df['rules'])
    
    # 4. Render the Plotly heatmap
    fig_heat = px.imshow(
        heatmap_data,
        text_auto=True,  # Displays exact count inside cells
        aspect="auto",
        color_continuous_scale="Reds",
        labels=dict(x="Life-Saving Rule", y="Location", color="Incident Count")
    )
    
    # Clean up axes and angle text for readability
    fig_heat.update_layout(
        xaxis_title="",
        yaxis_title="",
        xaxis=dict(tickangle=-30, side="bottom")
    )
    
    st.plotly_chart(fig_heat, width="stretch")
else:
    st.info("Not enough HIGH SIF data mapped to specific rules to generate the vulnerability matrix.")