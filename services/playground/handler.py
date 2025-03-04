from bisect import insort
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_js_eval import get_geolocation

from bacflow.geolocation import get_threshold_by_driver_profile, decode_coordinates
from bacflow.modeling import simulation_F, simulation_M
from bacflow.plotting import plot_simulation
from bacflow.schemas import Drink, DriverProfile, Model, Person, Sex
from bacflow.simulation import simulate


def _get_coordinates() -> tuple[float| None, float | None]:
    location = get_geolocation()

    if not location:
        return None, None

    latitude, longitude = decode_coordinates(location)
    return latitude, longitude


def _get_min_age_threshold(age: int) -> datetime:
    today = datetime.now()
    day = today.day

    try:
        threshold = today.replace(year=today.year - age)
    except ValueError:
        threshold = today.replace(year=today.year - age, day=today.day - 1)

    return threshold


@st.cache_data
def fetch_DUI_mapping():
    return pandas.read_csv("../../resources/DUI-driving-limits-by-alpha-2.csv")


@st.cache_data
def fetch_dataset():
    return pandas.read_csv("../../resources/dataset.csv")


latitude, longitude = _get_coordinates()

drink_info = fetch_dataset()
DUI_mapping = fetch_DUI_mapping()
# UI Components
st.title("BACflow: Estimate your Blood Alcohol Concentration (BAC)")

st.sidebar.header("Enter your information")
profile = DriverProfile(st.sidebar.selectbox("What kind of driver are you?", [profile.value for profile in DriverProfile]))
sex = Sex(st.sidebar.selectbox("Sex", [sex.value for sex in Sex]))
DoB = st.sidebar.date_input("Date of Birth", max_value=_get_min_age_threshold(18))
height = st.sidebar.slider("Height (cm)", 140, 210, 170)
weight = st.sidebar.slider("Weight (kg)", 40, 150, 82)
absorption_halflife = st.sidebar.slider("Absorption halflife (min)", 6, 18, 12) * 60
simulation = st.sidebar.multiselect(
    "Select simulation models",
    simulation_M if sex == Sex.M else simulation_F,
    default=[Model.Seidl],
    format_func=lambda model: str(model)
)

st.sidebar.header("Add a drink")
drink_type = st.sidebar.selectbox("Drink type", drink_info['drink'])
volume = st.sidebar.slider(
    "Volume (cl)", 1, 120,
    int(drink_info[drink_info['drink'] == drink_type]['volume'].iloc[0])
)
alc_perc = st.sidebar.slider(
    "Percent alcohol", 0, 100,
    int(drink_info[drink_info['drink'] == drink_type]['proportion'].iloc[0] * 100)
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

person = Person(DoB=DoB, height=height / 100, weight=weight, sex=sex)
threshold = get_threshold_by_driver_profile(latitude, longitude, profile, DUI_mapping)

if threshold:
    st.write(f"The DUI driving limit for your profile is: {threshold} g/dL", icon="ℹ️")
else:
    st.warning("No information on the DUI driving limit for your profile.", icon="⚠️")

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

        fig = plot_simulation(results, threshold)
        st.plotly_chart(fig)
else:
    st.write("No drinks added yet.")

st.write("Coded by SS R&D (2024), with MIT License.")
st.write("This app is intended for entertainment purposes and might be extremely misleading. Never use it for any serious purpose!")
