import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import plotly.graph_objects as go
from io import BytesIO
from reportlab.pdfgen import canvas
import qrcode

# =====================================================
# PAGE CONFIG & DESIGN
# =====================================================
st.set_page_config(page_title="AgriSense Morocco", layout="wide", page_icon="🌱")

st.markdown("""
<style>
.stButton>button {
    border-radius: 14px;
    background-color:#D97706;
    color:white;
    height:42px;
    width:100%;
}
.metric-card {
    border-radius: 14px;
    padding: 15px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#D97706'>🌱 AgriSense Morocco</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#6B8E23'>AI-powered sustainable agriculture decision support</p>", unsafe_allow_html=True)

# =====================================================
# SESSION STATE
# =====================================================
if "marker" not in st.session_state:
    st.session_state.marker = {"lat": 31.6295, "lon": -7.9811}  # Marrakech
if "weather" not in st.session_state:
    st.session_state.weather = {"temp": 25, "humidity": 50, "rain": 0}
if "city_name" not in st.session_state:
    st.session_state.city_name = "Unknown"

# =====================================================
# SIDEBAR – REGION SELECTION
# =====================================================
st.sidebar.header("📍 Select Region (Morocco)")
lat = st.sidebar.number_input("Latitude", 21.0, 36.0, st.session_state.marker["lat"])
lon = st.sidebar.number_input("Longitude", -17.0, -1.0, st.session_state.marker["lon"])

if st.sidebar.button("Set Region"):
    st.session_state.marker = {"lat": lat, "lon": lon}

lat, lon = st.session_state.marker["lat"], st.session_state.marker["lon"]

# =====================================================
# MAP
# =====================================================
map_df = pd.DataFrame([{"lat": lat, "lon": lon}])
fig_map = go.Figure(go.Scattermapbox(
    lat=map_df["lat"], lon=map_df["lon"], mode="markers",
    marker=go.scattermapbox.Marker(size=14, color="#D97706"),
    text=["Selected Region"]
))
fig_map.update_layout(
    mapbox=dict(style="open-street-map", zoom=5, center=dict(lat=lat, lon=lon)),
    margin=dict(l=0, r=0, t=0, b=0), height=400
)
st.plotly_chart(fig_map, use_container_width=True)

# =====================================================
# WEATHER FETCH – Open-Meteo
# =====================================================
import datetime

def fetch_open_meteo_weather(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,rain,relative_humidity_2m",
            "current_weather": True,
            "timezone": "auto"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Current temperature from current_weather
        current_temp = data["current_weather"]["temperature"]

        # Find closest hourly time to now for humidity & rain
        now_str = data["current_weather"]["time"]
        hourly_times = data["hourly"]["time"]
        idx = min(range(len(hourly_times)), key=lambda i: abs(pd.to_datetime(hourly_times[i]) - pd.to_datetime(now_str)))

        current_humidity = data["hourly"]["relative_humidity_2m"][idx]
        current_rain = data["hourly"]["rain"][idx]

        weather = {
            "temp": current_temp,
            "humidity": current_humidity,
            "rain": current_rain
        }

        # Set city name as coordinates (or improve later with reverse geocoding)
        city_name = f"{lat:.2f},{lon:.2f}"

        return weather, city_name

    except Exception as e:
        st.warning(f"Could not fetch weather, using last saved/demo data. Error: {e}")
        return st.session_state.weather, st.session_state.city_name


# =====================================================
# NDVI (SIMULATED)
# =====================================================
ndvi = float(np.clip(np.random.normal(0.55, 0.1), 0.2, 0.85))

# =====================================================
# AI CROP PREDICTION
# =====================================================
crops = ["wheat", "olives", "tomatoes", "citrus", "grapes", "almonds", "vegetables"]
irrigation = ["low", "low", "high", "medium", "medium", "low", "high"]

df = pd.DataFrame({
    "temperature": np.linspace(temp-3, temp+3, len(crops)),
    "rainfall": np.linspace(max(rain-10, 0), rain+10, len(crops)),
    "ndvi": np.linspace(ndvi-0.05, ndvi+0.05, len(crops)),
    "crop": crops,
    "irrigation": irrigation
})

X = df[["temperature", "rainfall", "ndvi"]]
crop_enc = LabelEncoder()
irr_enc = LabelEncoder()
y_crop = crop_enc.fit_transform(df["crop"])
y_irr = irr_enc.fit_transform(df["irrigation"])

crop_model = RandomForestClassifier(200, random_state=42)
irr_model = RandomForestClassifier(200, random_state=42)
crop_model.fit(X, y_crop)
irr_model.fit(X, y_irr)

X_input = pd.DataFrame([[temp, rain, ndvi]], columns=X.columns)
crop_pred = crop_enc.inverse_transform(crop_model.predict(X_input))[0]
irr_pred = irr_enc.inverse_transform(irr_model.predict(X_input))[0]
probs = crop_model.predict_proba(X_input)[0]

# =====================================================
# METRICS
# =====================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡 Temperature", f"{temp:.1f} °C")
c2.metric("🌧 Rainfall", f"{rain:.1f} mm")
c3.metric("💧 Humidity", f"{humidity}%")
c4.metric("🌿 NDVI", f"{ndvi:.2f}")

# =====================================================
# RESULTS
# =====================================================
st.success(f"🌾 **Recommended Crop:** {crop_pred.capitalize()} ({probs.max()*100:.1f}%)")
st.info(f"💦 **Irrigation Level:** {irr_pred.capitalize()}")

# =====================================================
# RISK ALERTS
# =====================================================
if rain < 5:
    st.warning("⚠️ Drought risk detected")
elif rain > 25:
    st.warning("⚠️ Heavy rain risk")

# =====================================================
# SUSTAINABILITY INDEX
# =====================================================
sustainability = round((ndvi*0.5 + (1 - rain/40)*0.3 + 0.2)*10, 1)
st.markdown(f"### ♻️ Sustainability Index: **{sustainability}/10**")
st.caption("Higher score = climate-resilient & water-efficient farming")

# =====================================================
# CROP PROBABILITY CHART
# =====================================================
fig = go.Figure(go.Bar(x=crop_enc.classes_, y=probs, marker_color="#6B8E23"))
fig.update_layout(title="Crop Suitability Probabilities")
st.plotly_chart(fig, use_container_width=True)

# =====================================================
# PDF EXPORT
# =====================================================
def generate_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "AgriSense Morocco Report")
    c.setFont("Helvetica", 12)
    y = 760
    for line in [
        f"Region: {city_name}",
        f"Temperature: {temp:.1f} °C",
        f"Rainfall: {rain:.1f} mm",
        f"Humidity: {humidity} %",
        f"NDVI: {ndvi:.2f}",
        f"Recommended Crop: {crop_pred.capitalize()}",
        f"Sustainability Index: {sustainability}/10",
        "Prepared by: MOHAMED AMINE JAGHOUTI"
    ]:
        c.drawString(50, y, line)
        y -= 22
    c.save()
    buffer.seek(0)
    return buffer

if st.button("📄 Export PDF Report"):
    st.download_button(
        "Download PDF",
        generate_pdf(),
        file_name=f"AgriSense_{city_name}.pdf",
        mime="application/pdf"
    )

# =====================================================
# QR CODE FOR APP
# =====================================================
APP_URL = "https://agrisense-moroccomaj-nngj5uc898kzkk7ae4j9go.streamlit.app/"
qr = qrcode.QRCode(version=1, box_size=12, border=8)
qr.add_data(APP_URL)
qr.make(fit=True)
img_qr = qr.make_image(fill_color="black", back_color="white")
buf_qr = BytesIO()
img_qr.save(buf_qr)
buf_qr.seek(0)

st.markdown("### 📱 Scan to open AgriSense Morocco online")
st.image(buf_qr, width=180)

# =====================================================
# FOOTER
# =====================================================
st.markdown("<p style='text-align:center;color:#6B8E23'>Powered by : Mohamed Amine Jaghouti</p>", unsafe_allow_html=True)

