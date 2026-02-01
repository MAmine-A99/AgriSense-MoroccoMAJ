import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
import qrcode

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="AgriSense Morocco",
    page_icon="🌱",
    layout="wide"
)

# =====================================================
# GLOBAL STYLE (Apple-like)
# =====================================================
st.markdown("""
<style>
* {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, Helvetica, Arial, sans-serif !important;
}
.stButton>button {
    border-radius: 16px;
    height: 52px;
    font-size: 18px;
    background-color: #D97706;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# SESSION STATE
# =====================================================
if "page" not in st.session_state:
    st.session_state.page = "intro"

if "refresh_weather" not in st.session_state:
    st.session_state.refresh_weather = 0

if "refresh_ndvi" not in st.session_state:
    st.session_state.refresh_ndvi = 0

# =====================================================
# INTRO PAGE
# =====================================================
def intro_page():

    st.markdown("""
    <h1 style='text-align:center; color:#D97706;'>🌱 AgriSense Morocco</h1>
    <h3 style='text-align:center; color:#6B8E23;'>
    AI-Driven Decision Support for Sustainable Agriculture
    </h3>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 📘 Documentation
    with st.expander("📘 Project Documentation (Concept & AI Logic)"):
        st.info("This document explains the first conceptual code, AI logic, and decision workflow.")
        st.markdown("📄 Upload your PDF as `docs/agrisense_documentation.pdf`")
        try:
            with open("docs/agrisense_documentation.pdf", "rb") as f:
                st.download_button("⬇️ Download Documentation", f, "AgriSense_Documentation.pdf")
        except:
            st.warning("Documentation file not found.")

    st.markdown("---")

    col1, col2 = st.columns([2,1])

    with col1:
        st.markdown("### 🚜 Project Idea")
        st.write("""
        AgriSense Morocco transforms environmental indicators into
        **AI-based agricultural decisions**, helping farmers adapt
        to climate stress and regional constraints.
        """)

        st.markdown("### 🎯 Objectives")
        st.markdown("""
        - Sustainable agriculture  
        - Water optimization  
        - Regional decision-making  
        - AI accessibility  
        """)

    with col2:
        st.markdown("### 🇲🇦 Why Morocco?")
        st.write("""
        Morocco faces strong climate variability and water scarcity.
        AgriSense adapts AI recommendations to **regional agricultural realities**.
        """)

    st.markdown("---")

    # 🗺️ Morocco Map
    st.markdown("### 🗺️ Agricultural Regions Overview")
    m = folium.Map(location=[31.8, -7.1], zoom_start=6)

    regions = {
        "Souss-Massa": [30.4, -9.6],
        "Gharb": [34.3, -6.3],
        "Saïss": [34.0, -4.9],
        "Haouz": [31.6, -8.0],
        "Oriental": [34.6, -2.9],
        "Draa-Tafilalet": [31.9, -5.5]
    }

    for r, coord in regions.items():
        folium.Marker(coord, popup=r).add_to(m)

    st_folium(m, height=400, width=700)

    if st.button("🚀 Launch Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

# =====================================================
# DASHBOARD PAGE
# =====================================================
def dashboard_page():

    st.sidebar.title("🌍 Configuration")

    region = st.sidebar.selectbox(
        "Moroccan Region",
        ["Souss-Massa", "Gharb", "Saïss", "Haouz", "Oriental", "Draa-Tafilalet"]
    )

    crop = st.sidebar.selectbox(
        "Crop of Interest",
        ["Wheat", "Olives", "Tomatoes", "Citrus", "Dates"]
    )

    if st.sidebar.button("🔄 Update Weather Data"):
        st.session_state.refresh_weather += 1

    if st.sidebar.button("🔄 Update NDVI"):
        st.session_state.refresh_ndvi += 1

    if st.sidebar.button("⬅ Back"):
        st.session_state.page = "intro"
        st.rerun()

    # ---------------- Simulated Data ----------------
    np.random.seed(len(region) + st.session_state.refresh_weather)
    temperature = np.random.uniform(10, 35)
    rainfall = np.random.uniform(0, 50)

    np.random.seed(len(region) + st.session_state.refresh_ndvi)
    ndvi = np.clip(np.random.normal(0.55, 0.1), 0.25, 0.85)

    # ---------------- Metrics ----------------
    m1, m2, m3 = st.columns(3)
    m1.metric("🌡 Temperature", f"{temperature:.1f} °C")
    m2.metric("🌧 Rainfall", f"{rainfall:.1f} mm")
    m3.metric("🌿 Vegetation Index (NDVI)", f"{ndvi:.2f}")

    st.markdown("---")

    # ---------------- AI Model ----------------
    data = pd.DataFrame({
        "temp": np.linspace(temperature-5, temperature+5, 6),
        "rain": np.linspace(max(rainfall-20,0), rainfall+20, 6),
        "ndvi": np.linspace(ndvi-0.1, ndvi+0.1, 6),
        "crop": ["Wheat","Olives","Tomatoes","Citrus","Dates","Wheat"],
        "irrigation": ["High","Low","High","Medium","Low","High"]
    })

    X = data[["temp","rain","ndvi"]]
    le_crop = LabelEncoder()
    le_irr = LabelEncoder()

    y_crop = le_crop.fit_transform(data["crop"])
    y_irr = le_irr.fit_transform(data["irrigation"])

    crop_model = RandomForestClassifier(n_estimators=120)
    irr_model = RandomForestClassifier(n_estimators=120)

    crop_model.fit(X, y_crop)
    irr_model.fit(X, y_irr)

    X_input = pd.DataFrame([[temperature, rainfall, ndvi]], columns=X.columns)
    crop_pred = le_crop.inverse_transform(crop_model.predict(X_input))[0]
    irr_pred = le_irr.inverse_transform(irr_model.predict(X_input))[0]

    st.success(f"🌾 Recommended Crop: **{crop_pred}**")
    st.info(f"💧 Suggested Irrigation: **{irr_pred}**")

    # ---------------- Chart ----------------
    probs = crop_model.predict_proba(X_input)[0]
    fig = go.Figure(go.Bar(x=le_crop.classes_, y=probs))
    fig.update_layout(title="Crop Suitability (AI Estimated)")
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- AI Insight ----------------
    st.markdown("### 🤖 AI Insight")
    st.write(f"""
    In **{region}**, AI analysis suggests **{crop_pred}** as the optimal crop
    under current environmental pressure, with **{irr_pred.lower()} irrigation**
    to enhance sustainability.
    """)

    # ---------------- PDF REPORT ----------------
    if st.button("📄 Generate AI Report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0,10,f"AgriSense Morocco Report – {region}", ln=True)
        pdf.ln(5)
        pdf.multi_cell(0,10,
            f"Temperature: {temperature:.1f} °C\n"
            f"Rainfall: {rainfall:.1f} mm\n"
            f"NDVI: {ndvi:.2f}\n\n"
            f"Recommended Crop: {crop_pred}\n"
            f"Irrigation Level: {irr_pred}"
        )
        pdf.output("AgriSense_Report.pdf")
        st.download_button("⬇️ Download Report", open("AgriSense_Report.pdf","rb"), "AgriSense_Report.pdf")

    st.markdown("---")

    # ---------------- QR CODE ----------------
    st.markdown("### 🔗 Access AgriSense Morocco")
    qr = qrcode.make("https://agrisense-morocco.streamlit.app")
    qr.save("qr.png")
    st.image("qr.png", width=160, caption="Scan to access the platform")

# =====================================================
# ROUTER
# =====================================================
if st.session_state.page == "intro":
    intro_page()
else:
    dashboard_page()

