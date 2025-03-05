import streamlit as st
import streamlit_shadcn_ui as shadcn
from datetime import datetime, timedelta, timezone
import pandas as pd

from database import get_drinks, get_food
from bacflow.schemas import Drink, Food, Person, Model, Sex
from bacflow.simulation import simulate, aggregate_simulation_results, identify_threshold_times
from bacflow.plotting import plot_simulation

if "user" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

user = st.session_state["user"]

st.title("BAC Simulation")

# Fixed simulation parameters: simulation length is 24 hours from now, dt is 10 minutes.
now = datetime.now(timezone.utc)
simulation_start = now
simulation_end = now + timedelta(hours=24)
dt = 600  # 10 minutes in seconds
default_halflife = 720  # default 12 minutes in seconds
initial_alc = 0.0

# Retrieve drinks and food intake for the user from the past 24 hours.
from_time = now - timedelta(hours=24)
to_time = now
drinks_data = get_drinks(user["id"], from_time, to_time)
food_data = get_food(user["id"], from_time, to_time)

# Convert drinks data (dicts) into Drink objects.
drinks = []
from bacflow.schemas import Drink as DrinkSchema, Food as FoodSchema
for d in drinks_data:
    drink = DrinkSchema(
        name=d["name"],
        vol=d["vol"],
        alc_prop=d["alc_prop"],
        time=d["time"] if isinstance(d["time"], (datetime,)) else datetime.strptime(d["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
        sip_interval=d["sip_interval"]
    )
    drinks.append(drink)

# Convert food data into Food objects.
food_intakes = []
for f in food_data:
    food = FoodSchema(
        name=f["name"],
        time=f["time"] if isinstance(f["time"], (datetime,)) else datetime.strptime(f["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
        category=f["category"]
    )
    food_intakes.append(food)

# Construct Person object from user details.
person = Person(
    age=(datetime.now().year - int(user["dob"][:4])) if user.get("dob") else 30,
    height=float(user["height"]) / 100 if user.get("height") else 1.75,
    weight=float(user["weight"]) if user.get("weight") else 70,
    sex=Sex(user["sex"]) if user.get("sex") else Sex.M
)

# Choose a simulation model (for simplicity, a single model is used).
sim_models = [Model.Seidl]

st.write("Running simulation...")

sim_results = simulate(
    drinks,
    person,
    simulation_start,
    simulation_end,
    dt,
    default_halflife,
    initial_alc,
    sim_models,
    food_intakes
)

if sim_results:
    aggregated = aggregate_simulation_results(sim_results)
    drive_safe_time, sober_time = identify_threshold_times(aggregated, driving_limit=0.02)
    
    st.header("Simulation Results")
    st.write("Key Thresholds:")
    st.write(f"Driving Safe Time: {drive_safe_time}")
    st.write(f"Sober Time: {sober_time}")
    
    fig = plot_simulation(aggregated, driving_limit=0.02)
    st.plotly_chart(fig)
else:
    st.error("No simulation results. Please add drinks to see simulation output.")
