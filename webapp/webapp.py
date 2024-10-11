from bisect import insort
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from helper import calc_bac_ts
from schemas import Drink

# Load drink information
drink_info = pd.read_csv("dataset.csv")

# UI Components
st.title("pydrink: Estimate your Blood Alcohol Concentration (BAC)")

st.sidebar.header("Enter your information")
sex = st.sidebar.selectbox("Sex", ["Male", "Female"])
height = st.sidebar.slider("Height (cm)", 140, 210, 170)
weight = st.sidebar.slider("Weight (kg)", 40, 150, 82)
absorption_halflife = st.sidebar.slider("Absorption halflife (min)", 6, 18, 12) * 60
beta = st.sidebar.slider("Alcohol elimination (%/h)", 0.009, 0.035, 0.018) / 100 / 3600

st.sidebar.header("Add a drink")
drink_type = st.sidebar.selectbox("Drink type", drink_info['drink'])
volume = st.sidebar.slider("Volume (cl)", 1, 120, int(drink_info[drink_info['drink'] == drink_type]['volume'].iloc[0]))
alc_perc = st.sidebar.slider("Percent alcohol", 0, 100, int(drink_info[drink_info['drink'] == drink_type]['alc_prop'].iloc[0] * 100))
drink_time_str = st.sidebar.text_input("Time of consumption (YYYY-MM-DD HH:MM)", placeholder=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"))
add_drink = st.sidebar.button("Add drink")

# Initialize session state for drinks
if 'drinks' not in st.session_state:
    st.session_state.drinks = []

# Add drink to session state
if add_drink:
    try:
        if drink_time_str:
            drink_time = datetime.strptime(drink_time_str, "%Y-%m-%d %H:%M").astimezone()
        else:
            drink_time = datetime.now().astimezone()

        insort(st.session_state.drinks, Drink(name=drink_type, vol=volume / 100, alc_prop=alc_perc / 100, time=drink_time), key=lambda x: x.time)
    except ValueError:
        st.sidebar.error("Incorrect time format. Please use YYYY-MM-DD HH:MM.")    


# Display added drinks
st.header("Drunken drinks")
for drink in st.session_state.drinks:
    st.write(f"{drink.name} - {drink.vol*100} cl, {drink.alc_prop*100}% at {drink.time.strftime('%H:%M')}")

# Calculate BAC
if st.session_state.drinks:
    start_time = min(drink.time for drink in st.session_state.drinks)
    end_time = max(drink.time for drink in st.session_state.drinks) + timedelta(seconds=60 * 60 * 24)

    bac_ts = calc_bac_ts(st.session_state.drinks, height / 100, weight, sex, absorption_halflife, beta, start_time, end_time)

    st.header("BAC over time")
    st.write("N.B. - The BAC percentage is equivalent to g/dL.")
    st.line_chart(bac_ts.set_index('time')['bac_perc'], x_label="time", y_label="BAC (%)")
else:
    st.write("No drinks added yet.")

st.write("Coded by soberspace AI (2024), licensed under the MIT License.")
st.write("This app is intended for entertainment purposes and might be extremely misleading. Never use it for any serious purpose!")