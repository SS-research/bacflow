from bisect import insort
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from bacflow.modeling import simulation_F, simulation_M
from bacflow.schemas import Drink, Person
from bacflow.simulation import simulate


# Load drink information
drink_info = pd.read_csv("../../resources/dataset.csv")

# UI Components
st.title("BACflow: Estimate your Blood Alcohol Concentration (BAC)")

st.sidebar.header("Enter your information")
sex = st.sidebar.selectbox("Sex", ["M", "F"])
age = st.sidebar.slider("Age", 18, 100, 18)
height = st.sidebar.slider("Height (cm)", 140, 210, 170)
weight = st.sidebar.slider("Weight (kg)", 40, 150, 82)
absorption_halflife = st.sidebar.slider("Absorption halflife (min)", 6, 18, 12) * 60
simulation = st.sidebar.multiselect(
    "Select simulation models",
    simulation_male if sex == "Male" else simulation_female,
    default=["seidl"],
    format_func=lambda model: model if model == "average" else model.capitalize()
)

st.sidebar.header("Add a drink")
drink_type = st.sidebar.selectbox("Drink type", drink_info['drink'])
volume = st.sidebar.slider(
    "Volume (cl)", 1, 120,
    int(drink_info[drink_info['drink'] == drink_type]['volume'].iloc[0])
)
alc_perc = st.sidebar.slider(
    "Percent alcohol", 0, 100,
    int(drink_info[drink_info['drink'] == drink_type]['alc_prop'].iloc[0] * 100)
)
drink_time_str = st.sidebar.text_input(
    "Time of consumption (YYYY-MM-DD HH:MM)",
    placeholder=datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
)
interval_duration = st.sidebar.slider("Interval duration (minutes)", 1, 60, 1)
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

        insort(
            st.session_state.drinks,
            Drink(
                name=drink_type,
                vol=volume / 100,
                alc_prop=alc_perc / 100,
                time=drink_time,
                sip_interval=interval_duration
            ),
            key=lambda x: x.time
        )
    except ValueError:
        st.sidebar.error("Incorrect time format. Please use YYYY-MM-DD HH:MM.")

# Display added drinks with delete option
st.header("Drunken drinks")
for i, drink in enumerate(st.session_state.drinks):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"{drink.name} - {drink.vol*100} cl, {drink.alc_prop*100}% at {drink.time.strftime('%Y-%m-%d %H:%M')} in {drink.sip_interval} minutes")
    with col2:
        if st.button("🗑️", key=f"delete_drink_{i}"):
            st.session_state.drinks.pop(i)
            st.experimental_rerun()

person = Person(age=age, height=height / 100, weight=weight, sex=sex)

# Calculate BAC
if st.session_state.drinks:
    if not simulation:
        st.error("Please select one or more simulation models.")
    else:
        results = simulate(
            st.session_state.drinks, person, absorption_halflife, simulation
        )

        st.header("BAC over time")
        st.write("Note: The BAC percentage is equivalent to g/dL.")

        fig = go.Figure()
        for model, bac_ts in results.items():
            fig.add_trace(go.Scatter(
                x=bac_ts['time'],
                y=bac_ts['bac_perc'],
                mode='lines',
                name=model if model == "average" else model.capitalize()
            ))

        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='BAC (%)'
        )

        st.plotly_chart(fig)
else:
    st.write("No drinks added yet.")

st.write("Coded by SS R&D (2024), with MIT License.")
st.write("This app is intended for entertainment purposes and might be extremely misleading. Never use it for any serious purpose!")
