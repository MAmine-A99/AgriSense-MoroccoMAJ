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

st.set_page_config(page_title="GreenLife Morocco", layout="wide", page_icon="🌱")

# ---------------------------------------------
# WEATHER DATA
# ---------------------------------------------

def get_weather(lat, lon, api_key):

    try:
        url=f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"

        r=requests.get(url,timeout=10)
        data=r.json()

        temp=data["main"]["temp"]
        humidity=data["main"]["humidity"]
        rain=data.get("rain",{}).get("1h",0)

        return temp,humidity,rain

    except:
        return 25,50,0


# ---------------------------------------------
# SOIL DATA FROM SOILGRIDS
# ---------------------------------------------

def get_soil_data(lat,lon):

    try:

        url=f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property=phh2o&property=ocd&property=clay&depth=0-5cm"

        r=requests.get(url,timeout=10).json()

        layers=r["properties"]["layers"]

        soil={}

        for layer in layers:

            name=layer["name"]

            val=layer["depths"][0]["values"]["mean"]

            soil[name]=val

        return {
            "ph":soil.get("phh2o",7),
            "carbon":soil.get("ocd",10),
            "clay":soil.get("clay",20)
        }

    except:

        return {"ph":7,"carbon":10,"clay":20}


# ---------------------------------------------
# SATELLITE NDVI (MODIS)
# ---------------------------------------------

def get_ndvi(lat,lon):

    try:

        url=f"https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?latitude={lat}&longitude={lon}&band=NDVI&startDate=A2023001&endDate=A2023365"

        r=requests.get(url,timeout=10).json()

        values=r["subset"][0]["data"]

        clean=[v for v in values if v!=-3000]

        ndvi=np.mean(clean)/10000

        return float(ndvi)

    except:

        return float(np.clip(np.random.normal(0.55,0.1),0.2,0.85))


# ---------------------------------------------
# INTRO PAGE
# ---------------------------------------------

def intro():

    st.title("🌱 GreenLife Morocco")

    st.subheader("AI Powered Sustainable Agriculture")

    st.write("""
GreenLife Morocco combines **AI + satellite data + soil science + climate analytics**
to help farmers optimize crop choice and irrigation.

Technologies:
• Machine Learning  
• Satellite NDVI monitoring  
• Soil chemistry analysis  
• Sustainability scoring
""")

    if st.button("🚀 Launch Dashboard"):
        st.session_state.page="dashboard"


# ---------------------------------------------
# DASHBOARD
# ---------------------------------------------

def dashboard():

    API_KEY="YOUR_OPENWEATHER_API_KEY"

    st.sidebar.title("Region Selection")

    lat=st.sidebar.number_input("Latitude",21.0,36.0,31.63)
    lon=st.sidebar.number_input("Longitude",-17.0,-1.0,-8.0)

    if st.sidebar.button("Analyze Region"):
        st.session_state.lat=lat
        st.session_state.lon=lon

    lat=st.session_state.get("lat",lat)
    lon=st.session_state.get("lon",lon)

    st.markdown(f"### Location: {lat:.2f} , {lon:.2f}")

    # -----------------------------------------
    # MAP
    # -----------------------------------------

    fig=go.Figure(go.Scattermapbox(
        lat=[lat],
        lon=[lon],
        mode="markers",
        marker=dict(size=14,color="green")
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=5,
        mapbox_center={"lat":lat,"lon":lon},
        height=400
    )

    st.plotly_chart(fig,use_container_width=True)

    # -----------------------------------------
    # DATA COLLECTION
    # -----------------------------------------

    temp,humidity,rain=get_weather(lat,lon,API_KEY)

    soil=get_soil_data(lat,lon)

    soil_ph=soil["ph"]
    soil_carbon=soil["carbon"]
    soil_clay=soil["clay"]

    ndvi=get_ndvi(lat,lon)

    # -----------------------------------------
    # METRICS
    # -----------------------------------------

    c1,c2,c3,c4,c5=st.columns(5)

    c1.metric("🌡 Temperature",f"{temp:.1f} °C")
    c2.metric("🌧 Rainfall",f"{rain:.1f} mm")
    c3.metric("💧 Humidity",f"{humidity}%")
    c4.metric("🌿 NDVI",f"{ndvi:.2f}")
    c5.metric("🧪 Soil pH",f"{soil_ph:.2f}")

    # -----------------------------------------
    # SOIL CONDITIONS
    # -----------------------------------------

    st.markdown("### 🌍 Soil Conditions")

    s1,s2,s3=st.columns(3)

    s1.metric("Organic Carbon",soil_carbon)
    s2.metric("Clay Content",soil_clay)
    s3.metric("Soil pH",soil_ph)

    soil_text=""

    if soil_ph<6:
        soil_text+="⚠️ Acidic soil detected. Lime treatment recommended."

    if soil_ph>8:
        soil_text+=" ⚠️ Alkaline soil detected."

    if soil_clay>40:
        soil_text+=" ⚠️ Heavy clay soil – improve drainage."

    if soil_text:
        st.warning(soil_text)

    # -----------------------------------------
    # AI MODEL
    # -----------------------------------------

    crops=["wheat","olives","tomatoes","citrus","grapes","almonds"]

    irrigation=["low","low","high","medium","medium","low"]

    df=pd.DataFrame({

        "temperature":np.linspace(temp-3,temp+3,len(crops)),
        "rainfall":np.linspace(max(rain-5,0),rain+5,len(crops)),
        "ndvi":np.linspace(ndvi-0.05,ndvi+0.05,len(crops)),
        "soil_ph":[soil_ph]*len(crops),
        "soil_carbon":[soil_carbon]*len(crops),
        "soil_clay":[soil_clay]*len(crops),
        "crop":crops,
        "irrigation":irrigation
    })

    X=df[[
    "temperature",
    "rainfall",
    "ndvi",
    "soil_ph",
    "soil_carbon",
    "soil_clay"
    ]]

    crop_enc=LabelEncoder()
    irr_enc=LabelEncoder()

    y_crop=crop_enc.fit_transform(df["crop"])
    y_irr=irr_enc.fit_transform(df["irrigation"])

    from sklearn.ensemble import RandomForestClassifier

    crop_model=RandomForestClassifier(200)
    irr_model=RandomForestClassifier(200)

    crop_model.fit(X,y_crop)
    irr_model.fit(X,y_irr)

    X_input=pd.DataFrame([[temp,rain,ndvi,soil_ph,soil_carbon,soil_clay]],
    columns=X.columns)

    crop_pred=crop_enc.inverse_transform(crop_model.predict(X_input))[0]
    irr_pred=irr_enc.inverse_transform(irr_model.predict(X_input))[0]

    st.success(f"🌾 Recommended Crop: {crop_pred}")
    st.info(f"💦 Irrigation Level: {irr_pred}")

    # -----------------------------------------
    # SUSTAINABILITY INDEX
    # -----------------------------------------

    SI=0.4*ndvi+0.3*(rain/20)+0.3*(soil_carbon/50)
    SI=np.clip(SI,0,1)

    st.metric("🌍 Sustainability Index",f"{SI*10:.1f}/10")

    # -----------------------------------------
    # PDF REPORT
    # -----------------------------------------

    def generate_pdf():

        buffer=BytesIO()

        c=canvas.Canvas(buffer)

        c.drawString(50,800,"GreenLife Morocco Report")

        y=760

        lines=[
        f"Temperature: {temp}",
        f"Rainfall: {rain}",
        f"NDVI: {ndvi}",
        f"Soil pH: {soil_ph}",
        f"Recommended Crop: {crop_pred}"
        ]

        for line in lines:
            c.drawString(50,y,line)
            y-=20

        c.save()

        buffer.seek(0)

        return buffer

    if st.button("📄 Export Report"):

        st.download_button(
        "Download PDF",
        generate_pdf(),
        file_name="greenlife_report.pdf",
        mime="application/pdf"
        )


# ---------------------------------------------
# ROUTER
# ---------------------------------------------

if "page" not in st.session_state:
    st.session_state.page="intro"

if st.session_state.page=="intro":
    intro()
else:
    dashboard()

