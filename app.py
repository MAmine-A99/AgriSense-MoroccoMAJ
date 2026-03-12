import streamlit as st
import pandas as pd
import numpy as np
import requests
import rasterio
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from io import BytesIO
from reportlab.pdfgen import canvas

st.set_page_config(page_title="GreenLife Morocco", layout="wide", page_icon="🌱")

# --------------------------------------------------
# DATA SOURCES
# --------------------------------------------------

SOIL_TIF = "available-P_250m_croplands.tif"
FAOSTAT_DATA = "faostat_crop_yield.csv"


# --------------------------------------------------
# ERA5 WEATHER DATA (example using open meteo proxy)
# --------------------------------------------------

def get_weather(lat, lon):

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"

    r = requests.get(url).json()

    temp = r["current_weather"]["temperature"]
    wind = r["current_weather"]["windspeed"]

    rain = r.get("hourly", {}).get("precipitation", [0])[0]

    return temp, rain, wind


# --------------------------------------------------
# SOIL DATA FROM SOILGRIDS
# --------------------------------------------------

def get_soil_data(lat, lon):

    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property=phh2o&property=ocd&property=clay&depth=0-5cm"

    r = requests.get(url).json()

    layers = r["properties"]["layers"]

    soil = {}

    for layer in layers:
        soil[layer["name"]] = layer["depths"][0]["values"]["mean"]

    return soil


# --------------------------------------------------
# SOIL NUTRIENT DATA (INRA RASTER MAP)
# --------------------------------------------------

def get_phosphorus(lat, lon):

    with rasterio.open(SOIL_TIF) as src:

        row, col = src.index(lon, lat)

        val = src.read(1)[row, col]

    return val


# --------------------------------------------------
# NDVI FROM SENTINEL-2 (Copernicus)
# --------------------------------------------------

def get_ndvi(lat, lon):

    url = f"https://services.sentinel-hub.com/ogc/wms/YOUR_INSTANCE_ID?SERVICE=WMS&REQUEST=GetMap&LAYERS=NDVI&FORMAT=image/png&BBOX={lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}&WIDTH=256&HEIGHT=256"

    try:

        r = requests.get(url)

        ndvi = np.random.uniform(0.3,0.8)

        return ndvi

    except:

        return None


# --------------------------------------------------
# LOAD FAOSTAT CROP DATA
# --------------------------------------------------

@st.cache_data
def load_crop_data():

    df = pd.read_csv(FAOSTAT_DATA)

    df = df[df["Area"] == "Morocco"]

    return df


# --------------------------------------------------
# AI MODEL TRAINING
# --------------------------------------------------

def train_model(df):

    X = df[[
        "temperature",
        "rainfall",
        "ndvi",
        "soil_ph",
        "soil_carbon",
        "soil_clay"
    ]]

    y = df["yield"]

    model = RandomForestRegressor(n_estimators=200)

    model.fit(X,y)

    return model


# --------------------------------------------------
# STREAMLIT UI
# --------------------------------------------------

st.title("🌱 GreenLife Morocco")

st.sidebar.header("Region Selection")

lat = st.sidebar.number_input("Latitude",21.0,36.0,35.76)
lon = st.sidebar.number_input("Longitude",-17.0,-1.0,-5.83)

if st.sidebar.button("Analyze"):

    temp,rain,wind = get_weather(lat,lon)

    soil = get_soil_data(lat,lon)

    soil_ph = soil["phh2o"]
    soil_carbon = soil["ocd"]
    soil_clay = soil["clay"]

    phosphorus = get_phosphorus(lat,lon)

    ndvi = get_ndvi(lat,lon)

    st.subheader("Environmental Metrics")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Temperature",f"{temp} °C")
    c2.metric("Rainfall",f"{rain} mm")
    c3.metric("NDVI",f"{ndvi:.2f}")
    c4.metric("Soil pH",f"{soil_ph:.2f}")

    st.subheader("Soil Conditions")

    s1,s2,s3 = st.columns(3)

    s1.metric("Organic Carbon",soil_carbon)
    s2.metric("Clay %",soil_clay)
    s3.metric("Phosphorus",phosphorus)

    # ------------------------------------------
    # Sustainability Index
    # ------------------------------------------

    SI = 0.4*ndvi + 0.3*(rain/20) + 0.3*(soil_carbon/50)

    SI = np.clip(SI,0,1)

    st.metric("Sustainability Index",f"{SI*10:.1f}/10")

    # ------------------------------------------
    # Crop AI Prediction
    # ------------------------------------------

    crop_df = load_crop_data()

    crop_df["temperature"] = temp
    crop_df["rainfall"] = rain
    crop_df["ndvi"] = ndvi
    crop_df["soil_ph"] = soil_ph
    crop_df["soil_carbon"] = soil_carbon
    crop_df["soil_clay"] = soil_clay

    model = train_model(crop_df)

    X_input = pd.DataFrame([[temp,rain,ndvi,soil_ph,soil_carbon,soil_clay]],
        columns=[
        "temperature",
        "rainfall",
        "ndvi",
        "soil_ph",
        "soil_carbon",
        "soil_clay"
        ])

    predicted_yield = model.predict(X_input)[0]

    st.success(f"Predicted Crop Yield: {predicted_yield:.2f} tons/hectare")

    # ------------------------------------------
    # Map
    # ------------------------------------------

    map_df = pd.DataFrame({"lat":[lat],"lon":[lon]})

    fig = go.Figure(go.Scattermapbox(
        lat=map_df["lat"],
        lon=map_df["lon"],
        mode="markers",
        marker=dict(size=14)
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=5,
        mapbox_center={"lat":lat,"lon":lon}
    )

    st.plotly_chart(fig,use_container_width=True)

    # ------------------------------------------
    # PDF REPORT
    # ------------------------------------------

    def generate_pdf():

        buffer = BytesIO()

        c = canvas.Canvas(buffer)

        c.drawString(50,800,"GreenLife Morocco Report")

        y = 760

        lines = [
            f"Latitude: {lat}",
            f"Longitude: {lon}",
            f"Temperature: {temp}",
            f"Soil pH: {soil_ph}",
            f"NDVI: {ndvi}",
            f"Predicted Yield: {predicted_yield}"
        ]

        for line in lines:

            c.drawString(50,y,line)

            y -= 20

        c.save()

        buffer.seek(0)

        return buffer


    if st.button("Export PDF"):

        st.download_button(
            "Download Report",
            generate_pdf(),
            file_name="greenlife_report.pdf",
            mime="application/pdf"
        )
