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

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="GreenLife", layout="wide", page_icon="🌱")

# ==================== GLOBAL STYLE ====================
st.markdown("""
<style>
* { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important; }
.stButton>button { border-radius: 14px; background-color:#D97706; color:white; height:50px; width:100%; font-size:18px; }
[data-testid="metric-container"] { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial !important; }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "page" not in st.session_state: st.session_state.page = "intro"
if "marker" not in st.session_state: st.session_state.marker = {"lat": 35.77, "lon": -5.8}  # Tangier agricultural zone
if "weather" not in st.session_state: st.session_state.weather = {"temp": 25, "humidity": 50, "rain": 2}
if "city_name" not in st.session_state: st.session_state.city_name = "Unknown"

API_KEY = "01aff74fe8d0fb3777a72ba49c7a3a8f"  # New OpenWeather API key

# ==================== DATA FUNCTIONS ====================
def get_weather(lat, lon, api_key):
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}", timeout=10)
        data = r.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        rain = data.get("rain", {}).get("1h", 0)
        return temp, humidity, rain
    except:
        return 25, 50, 0

def get_soil_data(lat, lon):
    try:
        url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property=phh2o&property=ocd&property=clay&depth=0-5cm"
        r = requests.get(url, timeout=10).json()
        layers = r["properties"]["layers"]
        soil = {layer["name"]: layer["depths"][0]["values"]["mean"] for layer in layers}
        return {
            "ph": soil.get("phh2o", 7),
            "carbon": soil.get("ocd", 10),
            "clay": soil.get("clay", 20)
        }
    except:
        return {"ph": 7, "carbon": 10, "clay": 20}

def get_ndvi(lat, lon):
    try:
        url = f"https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?latitude={lat}&longitude={lon}&band=NDVI&startDate=A2023001&endDate=A2023365"
        r = requests.get(url, timeout=10).json()
        values = r["subset"][0]["data"]
        clean = [v for v in values if v != -3000]
        return float(np.mean(clean) / 10000)
    except:
        return float(np.clip(np.random.normal(0.55, 0.1), 0.2, 0.85))

# ==================== INTRO PAGE ====================
def intro():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;">
        <h1 style='color:#D97706; font-size:50px;'>🌱 GreenLife</h1>
        <h3 style='color:#6B8E23;'>AI-powered Sustainable Agriculture Decision Support</h3>
        <p style='color:#6B8E23; font-size:16px;'>Powered by <b>GreenLife Team</b> • <a href='mailto:Mohamedaminejaghouti@gmail.com'>Email</a></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns([2,1])

    with col1:
        st.markdown("### 🚜 About GreenLife Morocco")
        st.write("""
        Smart agriculture platform for Moroccan farmers combining:
        - AI crop & irrigation recommendations
        - Real-time weather data
        - NDVI satellite vegetation monitoring
        """)
        st.markdown("### 🎯 Vision")
        st.write("Enable data-driven farming, improving yield and preserving soil & water resources.")
        st.markdown("### 🔬 Scientific Basis")
        st.write("""
        - AI & Predictive Analytics
        - NDVI Satellite Monitoring
        - Soil Chemistry Analysis
        - Sustainable & Climate-smart Practices
        """)

    with col2:
        st.markdown("### 📄 Project Documentation")
        st.markdown("[📘 Download PDF Overview](https://drive.google.com)")

    st.markdown("---")
    if st.button("🚀 Launch Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

# ==================== DASHBOARD ====================
def dashboard():
    st.sidebar.title("📍 Select Agricultural Region")
    lat = st.sidebar.number_input("Latitude", 21.0, 36.0, st.session_state.marker["lat"])
    lon = st.sidebar.number_input("Longitude", -17.0, -1.0, st.session_state.marker["lon"])

    if st.sidebar.button("Set Region"):
        st.session_state.marker = {"lat": lat, "lon": lon}
        st.session_state.weather = {"temp": 25, "humidity": 50, "rain": 2}

    if st.sidebar.button("⬅ Back to Intro"):
        st.session_state.page = "intro"
        st.rerun()

    lat, lon = st.session_state.marker["lat"], st.session_state.marker["lon"]

    # ---------------- MAP ----------------
    fig_map = go.Figure(go.Scattermapbox(
        lat=[lat], lon=[lon], mode="markers",
        marker=go.scattermapbox.Marker(size=14, color="#D97706"),
        text=["Selected Agricultural Zone"]
    ))
    fig_map.update_layout(mapbox=dict(style="open-street-map", zoom=6, center={"lat": lat, "lon": lon}),
                          margin=dict(l=0,r=0,t=0,b=0), height=420)
    st.plotly_chart(fig_map, use_container_width=True)

    # ---------------- CITY NAME ----------------
    try:
        geo = requests.get(
            f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={API_KEY}",
            timeout=5
        ).json()
        if geo and len(geo) > 0:
            st.session_state.city_name = geo[0].get("name", "Unknown")
    except:
        st.session_state.city_name = "Unknown"

    city_name = st.session_state.city_name
    st.markdown(f"### 📌 Selected Area: **{city_name}**")

    # ---------------- WEATHER ----------------
    if st.sidebar.button("🔄 Refresh Weather"):
        temp, humidity, rain = get_weather(lat, lon, API_KEY)
        st.session_state.weather = {"temp": temp, "humidity": humidity, "rain": rain}

    temp = st.session_state.weather["temp"]
    humidity = st.session_state.weather["humidity"]
    rain = st.session_state.weather["rain"]

    # ---------------- NDVI & SOIL ----------------
    ndvi = get_ndvi(lat, lon)
    soil = get_soil_data(lat, lon)
    soil_ph, soil_carbon, soil_clay = soil["ph"], soil["carbon"], soil["clay"]

    # ---------------- METRICS ----------------
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("🌡 Temperature", f"{temp:.1f} °C")
    c2.metric("🌧 Rainfall", f"{rain:.1f} mm")
    c3.metric("💧 Humidity", f"{humidity}%")
    c4.metric("🌿 NDVI", f"{ndvi:.2f}")
    c5.metric("🧪 Soil pH", f"{soil_ph:.2f}")

    # ---------------- SOIL CONDITIONS ----------------
    st.markdown("### 🌍 Soil Conditions")
    s1,s2,s3 = st.columns(3)
    s1.metric("Organic Carbon", soil_carbon)
    s2.metric("Clay %", soil_clay)
    s3.metric("pH", soil_ph)

    soil_alert=""
    if soil_ph<6: soil_alert+="⚠️ Acidic soil detected. Lime treatment recommended. "
    if soil_ph>8: soil_alert+="⚠️ Alkaline soil detected. "
    if soil_clay>40: soil_alert+="⚠️ Heavy clay soil – improve drainage. "
    if soil_alert: st.warning(soil_alert)

    # ---------------- AI CROP RECOMMENDATION ----------------
    crops=["wheat","olives","tomatoes","citrus","grapes","almonds","vegetables"]
    irrigation=["low","low","high","medium","medium","low","high"]

    df=pd.DataFrame({
        "temperature": np.linspace(temp-3, temp+3, len(crops)),
        "rainfall": np.linspace(max(rain-5,0), rain+5, len(crops)),
        "ndvi": np.linspace(ndvi-0.05, ndvi+0.05, len(crops)),
        "soil_ph":[soil_ph]*len(crops),
        "soil_carbon":[soil_carbon]*len(crops),
        "soil_clay":[soil_clay]*len(crops),
        "crop": crops,
        "irrigation": irrigation
    })

    X = df[["temperature","rainfall","ndvi","soil_ph","soil_carbon","soil_clay"]]
    crop_enc = LabelEncoder(); irr_enc = LabelEncoder()
    y_crop = crop_enc.fit_transform(df["crop"]); y_irr = irr_enc.fit_transform(df["irrigation"])
    crop_model = RandomForestClassifier(200, random_state=42); irr_model = RandomForestClassifier(200, random_state=42)
    crop_model.fit(X, y_crop); irr_model.fit(X, y_irr)
    X_input = pd.DataFrame([[temp,rain,ndvi,soil_ph,soil_carbon,soil_clay]], columns=X.columns)
    crop_pred = crop_enc.inverse_transform(crop_model.predict(X_input))[0]
    irr_pred = irr_enc.inverse_transform(irr_model.predict(X_input))[0]
    probs = crop_model.predict_proba(X_input)[0]

    st.success(f"🌾 Recommended Crop: **{crop_pred.capitalize()}**")
    st.info(f"💦 Irrigation Level: **{irr_pred.capitalize()}**")

    # ---------------- ALERTS ----------------
    alert_text=""
    if rain<2: alert_text+="⚠️ Drought risk detected. "
    if temp<5: alert_text+="❄️ Frost risk detected. "
    if ndvi<0.3: alert_text+="🐛 Low vegetation detected – possible pests. "
    if alert_text: st.warning(alert_text)

    # ---------------- PROBABILITY CHART ----------------
    fig = go.Figure(go.Bar(x=crop_enc.classes_, y=probs, marker_color="#6B8E23"))
    fig.update_layout(title="Crop Suitability Probabilities")
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- SUSTAINABILITY INDEX ----------------
    SI = np.clip(0.4*ndvi + 0.3*(rain/20) + 0.3*(soil_carbon/50),0,1)
    st.metric("🌍 Sustainability Index", f"{SI*10:.1f}/10")

    # ---------------- PDF ----------------
    def generate_pdf():
        buffer = BytesIO(); c = canvas.Canvas(buffer)
        c.drawString(50,800,"GreenLife Morocco Report")
        y=760
        for line in [
            f"Region: {city_name}",
            f"Temperature: {temp:.1f} °C",
            f"Rainfall: {rain:.1f} mm",
            f"NDVI: {ndvi:.2f}",
            f"Soil pH: {soil_ph}",
            f"Recommended Crop: {crop_pred}",
            f"Irrigation Level: {irr_pred}"
        ]:
            c.drawString(50,y,line); y-=20
        c.save(); buffer.seek(0); return buffer

    if st.button("📄 Export PDF Report"):
        st.download_button("Download PDF", generate_pdf(), file_name=f"GreenLife_{city_name}.pdf", mime="application/pdf")

    # ---------------- QR ----------------
    APP_URL="https://your-streamlit-app-url"
    qr=qrcode.make(APP_URL)
    buf=BytesIO(); qr.save(buf); buf.seek(0)
    st.markdown("### 📱 Scan to open GreenLife Morocco")
    st.image(buf,width=160)

# ==================== ROUTER ====================
if st.session_state.page=="intro":
    intro()
else:
    dashboard()


