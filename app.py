import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="AgriSense Morocco",
    page_icon="🌱",
    layout="wide"
)

# ------------------ SIDEBAR ------------------
st.sidebar.title("AgriSense Morocco")
page = st.sidebar.radio("Navigation", ["Intro", "Dashboard"])

# ------------------ INTRO PAGE ------------------
def intro_page():
    st.markdown("## 🌱 AgriSense Morocco")
    st.markdown("""
**AgriSense Morocco** is an AI-powered decision support system for sustainable agriculture.

It leverages:
- Climate indicators
- Vegetation indices (NDVI)
- AI-driven recommendations  

to help **farmers, agronomists, and policymakers** make climate-resilient decisions.
""")

    st.markdown("### Key Features")
    st.markdown("""
- Crop recommendation  
- Smart irrigation strategy  
- Sustainability-oriented insights  
- Morocco-focused regional analysis  
""")

# ------------------ DASHBOARD PAGE ------------------
def dashboard_page():
    st.markdown("## 📊 Agricultural Decision Dashboard")

    # ----------- REGION SELECTION -----------
    region = st.selectbox(
        "Select Moroccan Agricultural Region",
        [
            "Souss-Massa",
            "Gharb",
            "Saïss",
            "Haouz",
            "Oriental",
            "Draa-Tafilalet"
        ]
    )

    # ----------- FAKE BUT REALISTIC DATA -----------
    temperature = np.random.uniform(15, 35)
    rainfall = np.random.uniform(5, 80)
    ndvi = np.random.uniform(0.25, 0.80)

    # ----------- AI LOGIC (RULE-BASED DEMO) -----------
    if ndvi > 0.6:
        crop_pred = "Vegetables / Citrus"
    elif ndvi > 0.4:
        crop_pred = "Cereals"
    else:
        crop_pred = "Olive / Date Palm"

    if rainfall < 20:
        irr_pred = "High irrigation required"
    elif rainfall < 50:
        irr_pred = "Moderate irrigation"
    else:
        irr_pred = "Low irrigation required"

    # ----------- KPI METRICS -----------
    col1, col2, col3 = st.columns(3)
    col1.metric("Temperature (C)", f"{temperature:.1f}")
    col2.metric("Rainfall (mm)", f"{rainfall:.1f}")
    col3.metric("NDVI Index", f"{ndvi:.2f}")

    st.markdown("---")

    # ---------------- MAP ----------------
    region_coords = {
        "Souss-Massa": (30.4, -9.6),
        "Gharb": (34.3, -6.3),
        "Saïss": (34.0, -4.9),
        "Haouz": (31.6, -8.0),
        "Oriental": (34.6, -2.9),
        "Draa-Tafilalet": (31.9, -5.5)
    }

    lat, lon = region_coords[region]

    map_df = pd.DataFrame({
        "lat": [lat],
        "lon": [lon],
        "region": [region]
    })

    fig_map = go.Figure(go.Scattermapbox(
        lat=map_df["lat"],
        lon=map_df["lon"],
        mode="markers",
        marker=dict(size=16),
        text=map_df["region"]
    ))

    fig_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=5,
        mapbox_center={"lat": 31.5, "lon": -7.5},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=420
    )

    st.markdown("### 🗺️ Selected Agricultural Region")
    st.plotly_chart(fig_map, use_container_width=True)

    # ----------- AI RECOMMENDATIONS -----------
    st.markdown("### 🤖 AI Recommendations")
    st.markdown(f"""
- **Recommended Crop:** {crop_pred}  
- **Irrigation Strategy:** {irr_pred}  
""")

    # ----------- PDF GENERATION (SAFE) -----------
    st.markdown("---")
    st.markdown("### 📄 AI-Generated Report")

    if st.button("Generate Report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        report_text = (
            "AgriSense Morocco - AI Agriculture Report\n\n"
            f"Region: {region}\n"
            f"Temperature: {temperature:.1f} C\n"
            f"Rainfall: {rainfall:.1f} mm\n"
            f"NDVI Index: {ndvi:.2f}\n\n"
            f"Recommended Crop: {crop_pred}\n"
            f"Irrigation Strategy: {irr_pred}\n\n"
            "Insight:\n"
            "This report is generated using an AI-based\n"
            "decision support system tailored for Morocco."
        )

        pdf.multi_cell(0, 8, report_text)
        pdf.output("AgriSense_Report.pdf")

        with open("AgriSense_Report.pdf", "rb") as f:
            st.download_button(
                "Download PDF Report",
                f,
                file_name="AgriSense_Report.pdf",
                mime="application/pdf"
            )

# ------------------ PAGE ROUTING ------------------
if page == "Intro":
    intro_page()
else:
    dashboard_page()

