import streamlit as st
import pandas as pd
import time
import os

st.set_page_config(page_title="HITL Retraining", layout="wide")

st.subheader("👨‍🔧 Human-in-the-Loop: Borderline Review")
st.caption("Flagged predictions (40%-60% confidence) awaiting HSE expert verification.")

# 1. Mock borderline data that the model struggled with
if "review_queue" not in st.session_state:
    st.session_state.review_queue = pd.DataFrame({
        "Report": [
            "Worker used a makeshift step stool to reach a valve.",
            "Gas monitor beeped once but then stopped, work continued.",
            "Slight oil sheen noticed near the hot work area."
        ],
        "Model Prediction": ["LOW", "LOW", "HIGH"],
        "Confidence": ["58%", "45%", "52%"],
        "Corrected Label": ["Select", "Select", "Select"]
    })

# 2. Interactive editor for the human expert
edited_df = st.data_editor(
    st.session_state.review_queue,
    column_config={
        "Corrected Label": st.column_config.SelectboxColumn(
            "Verify / Correct",
            help="Select the true SIF potential",
            options=["Select", "HIGH", "LOW"],
            required=True
        )
    },
    disabled=["Report", "Model Prediction", "Confidence"],
    hide_index=True,
    width="stretch"
)

# 3. Save corrections to the queue
if st.button("💾 Log Corrections to Queue"):
    corrections = edited_df[edited_df["Corrected Label"] != "Select"]
    if not corrections.empty:
        # In a real app, you would do: corrections.to_csv("data/pending_retrain.csv", mode='a')
        st.success(f"{len(corrections)} reports added to the reinforcement learning queue!")
        st.dataframe(corrections[["Report", "Corrected Label"]], width="stretch")
    else:
        st.warning("No labels corrected yet.")

st.divider()

# 4. Mock Retraining Trigger
st.subheader("⚙️ Model Lifecycle Management")
if st.button("🚀 Trigger Model Retraining", type="primary"):
    with st.spinner("Compiling new dataset and extracting embeddings..."):
        time.sleep(2)  # Simulate MiniLM embedding time
    with st.spinner("Refitting XGBoost pipeline..."):
        time.sleep(1.5) # Simulate training time
    
    st.success("Retraining complete! New weights deployed to production.")
    
    col1, col2 = st.columns(2)
    col1.metric("Previous Model F1-Score", "0.85")
    col2.metric("New Model F1-Score", "0.88", delta="0.03")
    
    st.info("The model has successfully adapted to the new edge cases.")