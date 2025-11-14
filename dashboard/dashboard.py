"""
Streamlit dashboard for CrisisMesh AI MVP.

Shows:
- Neighbor table (from /api/v1/topology)
- Failure predictions (from /api/v1/predictions)
"""

import time

import requests
import streamlit as st

# Set this to the mesh IP of the gateway node running api.py
BACKEND_URL = "http://10.0.0.1:5000"


def fetch_json(path: str):
    r = requests.get(f"{BACKEND_URL}{path}", timeout=3)
    r.raise_for_status()
    return r.json()


st.set_page_config(page_title="CrisisMesh Dashboard", layout="wide")
st.title("CrisisMesh AI – Mesh Topology & Failure Predictions")

auto = st.sidebar.checkbox("Auto-refresh (every 2s)", value=False)
status_placeholder = st.sidebar.empty()

while True:
    try:
        topo = fetch_json("/api/v1/topology")
        preds = fetch_json("/api/v1/predictions")
        status_placeholder.success("Connected to backend")
    except Exception as e:
        status_placeholder.error(f"Error contacting backend: {e}")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Neighbors")
        st.table(topo["neighbors"])

    with col2:
        if "predictions" in preds:
            st.subheader("Failure Predictions")
            st.table(preds["predictions"])
        else:
            st.subheader("Failure Predictions")
            st.write("Model not loaded or predictions unavailable.")

    if not auto:
        break

    time.sleep(2)
    st.experimental_rerun()
