🌱 AgriSense Morocco

AI-Powered Smart Agriculture Decision Support System

AgriSense Morocco is an interactive web application that uses environmental data and machine learning to support sustainable agricultural decision-making in Morocco. It helps farmers, students, and decision-makers identify suitable crops, irrigation needs, and climate risks through a simple visual dashboard.

🎯 Objectives

Support sustainable agriculture and food security

Use AI and environmental indicators to guide crop selection

Provide accessible decision support for non-technical users

Demonstrate real-world AI application in agriculture

🧠 How It Works

User selects a location in Morocco (map or coordinates)

Real-time weather data is fetched (temperature, humidity, rainfall)

Vegetation health is estimated using a simulated NDVI indicator

A machine-learning model analyzes the data

The app recommends:

Best-suited crop

Irrigation level

Risk awareness through visual indicators

🛠️ Technologies Used

Python 3.11

Streamlit – interactive web app

Scikit-learn – machine learning (Random Forest)

Pandas & NumPy – data processing

Plotly – interactive charts & maps

OpenWeatherMap API – real-time weather data

ReportLab – PDF export

📊 Features

Interactive map (Morocco-focused)

Real-time weather integration

AI-based crop and irrigation prediction

NDVI-based vegetation insight

What-if climate scenario analysis

Downloadable PDF report

Simple UI designed for accessibility

🌍 Sustainability & Food Security

AgriSense Morocco contributes to climate-smart agriculture, helping optimize resource use, reduce water waste, and improve crop resilience—supporting long-term sustainability and food security goals.

🚀 How to Run Locally
pip install -r requirements.txt
streamlit run app.py

🌐 Live Demo

👉 (Streamlit Cloud URL goes here)
Scan the QR code to access the app on mobile.

📁 Project Structure
AgriSense-Morocco/
│── app.py
│── requirements.txt
│── README.md

📚 References

Pettorelli, N. (2013). The Normalized Difference Vegetation Index. Oxford University Press.

Liakos, K. G., et al. (2018). Machine learning in agriculture. Computers and Electronics in Agriculture.

Lobell, D. B., & Burke, M. B. (2010). Climate change and crop yield models. Agricultural and Forest Meteorology.

👤 Author

Mohamed Amine Jaghouti
AI & Digital Engineering Student
Project developed for academic, innovation, and hackathon purposes.
