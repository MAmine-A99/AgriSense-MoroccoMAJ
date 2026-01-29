import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.pdfgen import canvas

# -------------------------------
# PAGE CONFIG & DESIGN
# -------------------------------
st.set_page_config(page_title="AgriSense Morocco", layout="wide", page_icon="🌱")

st.markdown("""
<style>
.stButton>button {
    border-radius: 15px;
    background-color:#D97706;
    color:white;
    height:40px;
    width:100%;
    margin-bottom:10px;
}
.stMetric {
    border-radius: 15px;
    box-shadow: 2px 2px 10px #ccc;
    padding: 15px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#D97706'>🌱 AgriSense Morocco</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#6B8E23'>AI-powered agriculture decision support system</p>", unsafe_allow_html=True)

# -------------------------------
# REGION SELECTION
# -------------------------------
st.sidebar.header("Select Region (Morocco)")

if 'marker' not in st.session_state:
    st.session_state['marker'] = {'lat':31.6295,'lon':-7.9811}  # Marrakech default

lat_input = st.sidebar.number_input("Latitude", min_value=21.0, max_value=36.0, value=st.session_state['marker']['lat'])
lon_input = st.sidebar.number_input("Longitude", min_value=-17.0, max_value=-1.0, value=st.session_state['marker']['lon'])
if st.sidebar.button("Set Region"):
    st.session_state['marker'] = {'lat':lat_input,'lon':lon_input}

lat, lon = st.session_state['marker']['lat'], st.session_state['marker']['lon']

# -------------------------------
# MAP DISPLAY
# -------------------------------
map_df = pd.DataFrame([st.session_state['marker']])
fig_map = px.scatter_map(
    map_df,
    lat="lat",
    lon="lon",
    zoom=5,
    height=400,
)
fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, width='stretch')

# -------------------------------
# REVERSE GEOCODING
# -------------------------------
API_KEY = "be87b67bc35d53a2b6db5abe4f569460"
try:
    geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"
    geo_resp = requests.get(geo_url, timeout=5).json()
    city_name = geo_resp[0]['name'] if geo_resp else "Unknown"
except:
    city_name = "Unknown"

st.markdown(f"**Selected Region / City:** {city_name} (Lat: {lat:.2f}, Lon: {lon:.2f})")

# -------------------------------
# WEATHER FETCH
# -------------------------------
weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

default_temp, default_humidity, default_rain = 25, 50, 0

if st.sidebar.button("Refresh Weather") or 'weather_data' not in st.session_state:
    try:
        response = requests.get(weather_url, timeout=5)
        data = response.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        rain_data = data.get("rain", {})
        if "1h" in rain_data:
            rain = rain_data["1h"]
        elif "3h" in rain_data:
            rain = rain_data["3h"]/3
        else:
            rain = 0
        st.session_state['weather_data'] = {"temp": temp, "humidity": humidity, "rain": rain}
    except:
        st.warning("Could not fetch weather, using default demo data.")
        temp, humidity, rain = default_temp, default_humidity, default_rain
        st.session_state['weather_data'] = {"temp": temp, "humidity": humidity, "rain": rain}
else:
    temp = st.session_state['weather_data']['temp']
    humidity = st.session_state['weather_data']['humidity']
    rain = st.session_state['weather_data']['rain']

# -------------------------------
# SIMULATED NDVI
# -------------------------------
ndvi = np.random.uniform(0.3,0.7)

# -------------------------------
# AI CROP PREDICTION
# -------------------------------
crops = ["wheat","olives","vegetables","tomatoes","citrus","almonds","grapes"]
num_crops = len(crops)

temperature_arr = np.linspace(temp-2, temp+2, num_crops)
rainfall_arr = np.linspace(max(rain-20,0), rain+20, num_crops)
ndvi_arr = np.linspace(ndvi-0.05, ndvi+0.05, num_crops)
irrigation_levels = ["low","medium","high","medium","low","high","medium"]

data = pd.DataFrame({
    "temperature":temperature_arr,
    "rainfall":rainfall_arr,
    "ndvi":ndvi_arr,
    "crop":crops,
    "irrigation":irrigation_levels
})

X = data[["temperature","rainfall","ndvi"]]
y_crop = data["crop"]
y_irrigation = data["irrigation"]

crop_encoder = LabelEncoder()
irrigation_encoder = LabelEncoder()
y_crop_encoded = crop_encoder.fit_transform(y_crop)
y_irrigation_encoded = irrigation_encoder.fit_transform(y_irrigation)

crop_model = RandomForestClassifier(n_estimators=100, random_state=42)
irrigation_model = RandomForestClassifier(n_estimators=100, random_state=42)
crop_model.fit(X,y_crop_encoded)
irrigation_model.fit(X,y_irrigation_encoded)

# Use DataFrame for prediction to avoid sklearn warnings
X_input = pd.DataFrame([[temp, rain, ndvi]], columns=["temperature","rainfall","ndvi"])
crop_pred = crop_model.predict(X_input)
irrigation_pred = irrigation_model.predict(X_input)

crop_result = crop_encoder.inverse_transform(crop_pred)[0]
irrigation_result = irrigation_encoder.inverse_transform(irrigation_pred)[0]

# -------------------------------
# DASHBOARD CARDS
# -------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Temperature (°C)", temp)
col2.metric("💧 Rainfall (mm)", rain)
col3.metric("💦 Humidity (%)", humidity)
col4.metric("📈 NDVI", f"{ndvi:.2f} (0–1, higher=healthier)")

st.success(f"🌾 Recommended Crop: **{crop_result.capitalize()}**")
st.info(f"💧 Irrigation Level: **{irrigation_result.capitalize()}**")

# -------------------------------
# CROP PROBABILITY CHART
# -------------------------------
probs = crop_model.predict_proba(X_input)[0]
fig = go.Figure([go.Bar(x=crop_encoder.classes_, y=probs, marker_color=["#6B8E23","#D97706","#F5F5DC","#FFD700","#FFA500","#8B4513","#A0522D"])])
fig.update_layout(title="Crop Suitability Probability", yaxis=dict(title="Probability"))
st.plotly_chart(fig, width='stretch')

# -------------------------------
# WHAT-IF ANALYSIS
# -------------------------------
st.markdown("### 🔄 What-If Analysis: +20mm Rainfall")
X_whatif = pd.DataFrame([[temp, rain+20, ndvi]], columns=["temperature","rainfall","ndvi"])
crop_whatif = crop_encoder.inverse_transform(crop_model.predict(X_whatif))[0]
irrigation_whatif = irrigation_encoder.inverse_transform(irrigation_model.predict(X_whatif))[0]
st.markdown(f"If rainfall increases by 20mm:")
st.markdown(f"- Crop: **{crop_whatif.capitalize()}**")
st.markdown(f"- Irrigation: **{irrigation_whatif.capitalize()}**")

# -------------------------------
# EXPORT PDF
# -------------------------------
def generate_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(595, 842))  # letter size
    c.setFont("Helvetica-Bold",16)
    c.drawString(50,750,f"AgriSense Morocco Report")
    c.setFont("Helvetica",12)
    c.drawString(50,720,f"Region: {city_name} (Lat: {lat:.2f}, Lon: {lon:.2f})")
    c.drawString(50,700,f"Temperature: {temp} °C")
    c.drawString(50,680,f"Rainfall: {rain} mm")
    c.drawString(50,660,f"Humidity: {humidity} %")
    c.drawString(50,640,f"NDVI: {ndvi:.2f}")
    c.drawString(50,620,f"Recommended Crop: {crop_result.capitalize()}")
    c.drawString(50,600,f"Irrigation Level: {irrigation_result.capitalize()}")
    c.drawString(50,580,f"Prepared by: MOHAMED AMINE JAGHOUTI")
    c.save()
    buffer.seek(0)
    return buffer

if st.button("📄 Export PDF Report"):
    pdf_bytes = generate_pdf()
    st.download_button("Download PDF", pdf_bytes, file_name=f"AgriSense_{city_name}_{lat}_{lon}.pdf", mime="application/pdf")
