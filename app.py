import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import plotly.graph_objects as go
from io import BytesIO
from reportlab.pdfgen import canvas
import qrcode

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(page_title="GreenLife", layout="wide", page_icon="🌱")

# =====================================================
# STYLE
# =====================================================

st.markdown("""
<style>
* { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial !important; }
.stButton>button { border-radius: 12px; background-color:#D97706; color:white; height:45px; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# SESSION
# =====================================================

if "page" not in st.session_state:
    st.session_state.page = "intro"

# =====================================================
# DATA FUNCTIONS
# =====================================================

def get_ndvi(lat, lon):

    try:

        url = f"https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?latitude={lat}&longitude={lon}&band=NDVI&startDate=A2023001&endDate=A2023365"

        r = requests.get(url, timeout=10).json()

        values = r["subset"][0]["data"]

        clean = [v for v in values if v != -3000]

        ndvi = np.mean(clean) / 10000

        return float(ndvi)

    except:

        return float(np.clip(np.random.normal(0.55, 0.1), 0.2, 0.85))


def get_soil_data(lat, lon):

    try:

        url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property=phh2o&property=ocd&property=clay&depth=0-5cm"

        r = requests.get(url, timeout=10).json()

        layers = r["properties"]["layers"]

        soil = {}

        for layer in layers:

            soil[layer["name"]] = layer["depths"][0]["values"]["mean"]

        return {
            "ph": soil.get("phh2o", 7),
            "carbon": soil.get("ocd", 10),
            "clay": soil.get("clay", 20)
        }

    except:

        return {"ph": 7, "carbon": 10, "clay": 20}


# =====================================================
# INTRO PAGE
# =====================================================

def intro_page():

    st.title("🌱 GreenLife")

    st.subheader("AI-powered Sustainable Agriculture")

    st.write("""
GreenLife helps farmers make **data-driven agricultural decisions** using:

• Artificial Intelligence  
• Climate data  
• Satellite vegetation monitoring  
• Soil chemistry analysis
""")

    if st.button("🚀 Open Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()


# =====================================================
# DASHBOARD
# =====================================================

def dashboard_page():

    st.sidebar.title("📍 Region")

    cities = {
        "Tangier": (35.7595, -5.8340),
        "Tetouan": (35.5889, -5.3626),
        "Al Hoceima": (35.2440, -3.9317)
    }

    selected_city = st.sidebar.selectbox(
        "City (Tanger-Tetouan-Al Hoceima)",
        list(cities.keys())
    )

    lat, lon = cities[selected_city]

    # ================= MAP =================

    map_df = pd.DataFrame({"lat": [lat], "lon": [lon]})

    fig_map = go.Figure(go.Scattermapbox(
        lat=map_df["lat"],
        lon=map_df["lon"],
        mode="markers",
        marker=go.scattermapbox.Marker(size=14),
        text=[selected_city]
    ))

    fig_map.update_layout(
        mapbox=dict(style="open-street-map", zoom=6, center=dict(lat=lat, lon=lon)),
        height=400
    )

    st.plotly_chart(fig_map, use_container_width=True)

    # ================= WEATHER =================

    API_KEY = "YOUR_OPENWEATHER_API_KEY"

    temp = 25
    humidity = 50
    rain = 0
    city_name = selected_city

    try:

        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"

        response = requests.get(url, timeout=10)

        if response.status_code == 200:

            weather = response.json()

            temp = weather["main"]["temp"]
            humidity = weather["main"]["humidity"]
            rain = weather.get("rain", {}).get("1h", 0)

            city_name = weather["name"]

        else:

            st.warning("Weather API returned an error")

    except:

        st.warning("Weather API unavailable — using demo values")

    if st.button("🔄 Refresh Weather"):
        st.rerun()

    # ================= NDVI =================

    ndvi = get_ndvi(lat, lon)

    # ================= SOIL =================

    soil = get_soil_data(lat, lon)

    soil_ph = soil["ph"]
    soil_carbon = soil["carbon"]
    soil_clay = soil["clay"]

    # ================= METRICS =================

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("🌡 Temperature", f"{temp:.1f} °C")
    c2.metric("🌧 Rainfall", f"{rain:.1f} mm")
    c3.metric("💧 Humidity", f"{humidity}%")
    c4.metric("🌿 NDVI", f"{ndvi:.2f}")
    c5.metric("🧪 Soil pH", f"{soil_ph:.2f}")

    # ================= AI MODEL =================

    crops = ["wheat", "olives", "tomatoes", "citrus", "grapes", "almonds", "vegetables"]

    irrigation = ["low", "low", "high", "medium", "medium", "low", "high"]

    df = pd.DataFrame({

        "temperature": np.linspace(temp-3, temp+3, len(crops)),
        "rainfall": np.linspace(max(rain-10, 0), rain+10, len(crops)),
        "ndvi": np.linspace(ndvi-0.05, ndvi+0.05, len(crops)),
        "soil_ph": [soil_ph]*len(crops),
        "soil_carbon": [soil_carbon]*len(crops),
        "soil_clay": [soil_clay]*len(crops),
        "crop": crops,
        "irrigation": irrigation

    })

    X = df[["temperature", "rainfall", "ndvi", "soil_ph", "soil_carbon", "soil_clay"]]

    crop_enc = LabelEncoder()
    irr_enc = LabelEncoder()

    y_crop = crop_enc.fit_transform(df["crop"])
    y_irr = irr_enc.fit_transform(df["irrigation"])

    crop_model = RandomForestClassifier(200)
    irr_model = RandomForestClassifier(200)

    crop_model.fit(X, y_crop)
    irr_model.fit(X, y_irr)

    X_input = pd.DataFrame([[temp, rain, ndvi, soil_ph, soil_carbon, soil_clay]], columns=X.columns)

    crop_pred = crop_enc.inverse_transform(crop_model.predict(X_input))[0]
    irr_pred = irr_enc.inverse_transform(irr_model.predict(X_input))[0]

    probs = crop_model.predict_proba(X_input)[0]

    st.success(f"🌾 Recommended Crop: **{crop_pred.capitalize()}**")
    st.info(f"💦 Irrigation Level: **{irr_pred.capitalize()}**")

    # ================= CHART =================

    fig = go.Figure(go.Bar(
        x=crop_enc.classes_,
        y=probs
    ))

    fig.update_layout(title="Crop Suitability")

    st.plotly_chart(fig, use_container_width=True)

    # ================= SUSTAINABILITY =================

    SI = 0.4*ndvi + 0.3*(rain/20) + 0.3*(soil_carbon/50)

    SI = np.clip(SI, 0, 1)

    st.metric("🌍 Sustainability Index", f"{SI*10:.1f}/10")

    # ================= PDF =================

    def generate_pdf():

        buffer = BytesIO()

        c = canvas.Canvas(buffer)

        c.drawString(50, 800, "GreenLife Report")

        lines = [
            f"Region: {city_name}",
            f"Temperature: {temp}",
            f"Rainfall: {rain}",
            f"NDVI: {ndvi}",
            f"Soil pH: {soil_ph}",
            f"Recommended Crop: {crop_pred}"
        ]

        y = 760

        for line in lines:
            c.drawString(50, y, line)
            y -= 20

        c.save()

        buffer.seek(0)

        return buffer

    if st.button("📄 Export Report"):

        st.download_button(
            "Download PDF",
            generate_pdf(),
            file_name="GreenLife_report.pdf",
            mime="application/pdf"
        )

    # ================= QR =================

    qr = qrcode.make("https://your-streamlit-app-url")

    buf = BytesIO()

    qr.save(buf)

    buf.seek(0)

    st.image(buf, width=150)


# =====================================================
# ROUTER
# =====================================================

if st.session_state.page == "intro":
    intro_page()

else:
    dashboard_page()
