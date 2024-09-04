import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, UTC
import helper_function as hf

# Load drink information
drink_info = pd.read_csv('data/drink_info.csv')

# Title
st.title("drinkR: Estimate your Blood Alcohol Concentration (BAC)")

# Sidebar for personal info
st.sidebar.header("Enter your details")
sex = st.sidebar.selectbox("Sex", ["Male", "Female", "Unknown"])
height = st.sidebar.slider("Height (cm)", min_value=140, max_value=210, value=170)
weight = st.sidebar.slider("Weight (kg)", min_value=40, max_value=150, value=82)
halflife = st.sidebar.slider("Absorption halflife (min)", min_value=6, max_value=18, value=12)
elimination = st.sidebar.slider("Alcohol elimination (%/h)", min_value=0.009, max_value=0.035, value=0.018, step=0.001)

# Display height and weight in imperial units
st.sidebar.text(f"Height: {height} cm = {int(height * 0.0328084)}' {round((height * 0.0328084 % 1) * 12)}''")
st.sidebar.text(f"Weight: {weight} kg = {round(weight * 2.20462)} lbs")

# Time zone offset
timezone_offset = datetime.now().astimezone().utcoffset().total_seconds()
client_start_time = datetime.now(UTC)

# Main area for BAC graph and drink inputs
st.subheader("Your BAC over time")
if 'drinks' not in st.session_state:
    st.session_state['drinks'] = []

# Drink time input
rounded_time = client_start_time + timedelta(minutes=10) - timedelta(minutes=client_start_time.minute % 10)
drink_times = [(rounded_time + timedelta(minutes=10 * i)).strftime("%H:%M") for i in range(-72, 73)]
selected_time = st.selectbox("Drink time", drink_times)

# Drink type input
drink_type = st.selectbox("Drink type", drink_info['drink'])

# Volume and alcohol percentage input
volume = st.slider("Volume (cl)", min_value=1, max_value=120, value=int(drink_info[drink_info['drink'] == drink_type]['volume'].iloc[0]))
alc_perc = st.slider("Percent alcohol", min_value=0, max_value=100, value=int(drink_info[drink_info['drink'] == drink_type]['alc_prop'].iloc[0]) * 100)

# Add drink button
if st.button("Add drink!"):
    st.session_state['drinks'].append({
        'name': drink_type,
        'vol': volume / 100,
        'alc_prop': alc_perc / 100,
        'time': (datetime.now(UTC) - client_start_time).total_seconds() - timezone_offset
    })

# Display the BAC plot
if st.session_state['drinks']:
    bac_ts = hf.calc_bac_ts(st.session_state['drinks'], height / 100, weight, sex, halflife * 60, elimination / 100 / 3600, 0, 86400)
    figure = hf.plot_bac_ts(bac_ts, drink_info)
    st.pyplot(figure)
else:
    st.write("No drinks added yet!")

# Footer
st.markdown("""
*This app is intended for entertainment purposes and might be extremely misleading. Never use it for any serious purpose, please!*
""")
