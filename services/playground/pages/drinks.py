import streamlit as st
import streamlit_shadcn_ui as shadcn
from datetime import datetime, timedelta, timezone
from database import get_drinks, add_drink, delete_drink, update_drink
import pandas as pd

if "user" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

user = st.session_state["user"]
user_id = user["id"]

st.title("Drinks History")

now = datetime.now(timezone.utc)
from_time = now - timedelta(hours=24)
to_time = now

drinks = get_drinks(user_id, from_time, to_time)

st.write("Your drinks in the last 24 hours:")
if drinks:
    df = pd.DataFrame(drinks)
    st.dataframe(df)
else:
    st.info("No drinks recorded in the last 24 hours.")

st.header("Add a Drink")
with st.form("add_drink_form"):
    name = shadcn.TextInput(label="Drink Name", placeholder="e.g., Beer")
    vol = shadcn.NumberInput(label="Volume (liters)", min_value=0.0, max_value=2.0, step=0.01, value=0.33)
    alc_prop = shadcn.NumberInput(label="Alcohol Proportion (0-1)", min_value=0.0, max_value=1.0, step=0.01, value=0.05)
    time_str = shadcn.TextInput(label="Time of Consumption (YYYY-MM-DD HH:MM)", placeholder=now.strftime("%Y-%m-%d %H:%M"))
    sip_interval = shadcn.NumberInput(label="Sip Interval (minutes)", min_value=1, max_value=60, step=1, value=1)
    submit = st.form_submit_button("Add Drink")

if submit:
    try:
        drink_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if drink_time > now:
            st.error("Cannot add a drink in the future.")
        elif drink_time < now - timedelta(hours=24):
            st.error("Can only add drinks from the past 24 hours.")
        else:
            add_drink(user_id, name, vol, alc_prop, drink_time, int(sip_interval))
            st.success("Drink added!")
            st.experimental_rerun()
    except Exception as e:
        st.error(f"Error: {e}")

st.header("Manage Drinks")
for drink in drinks:
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.write(f"{drink['name']} - {drink['vol']} L, {drink['alc_prop']*100}% at {drink['time']}")
    with col2:
        if st.button("Delete", key=f"delete_{drink['id']}"):
            delete_drink(user_id, drink['id'])
            st.experimental_rerun()
    with col3:
        if st.button("Edit", key=f"edit_{drink['id']}"):
            st.session_state["edit_drink"] = drink
            st.experimental_set_query_params(page="drinks", action="edit", drink_id=drink["id"])
            st.experimental_rerun()

query_params = st.experimental_get_query_params()
if query_params.get("action") == ["edit"] and "edit_drink" in st.session_state:
    drink = st.session_state["edit_drink"]
    st.subheader("Edit Drink")
    with st.form("edit_drink_form"):
        name = shadcn.TextInput(label="Drink Name", value=drink["name"])
        vol = shadcn.NumberInput(label="Volume (liters)", value=drink["vol"], min_value=0.0, max_value=2.0, step=0.01)
        alc_prop = shadcn.NumberInput(label="Alcohol Proportion (0-1)", value=drink["alc_prop"], min_value=0.0, max_value=1.0, step=0.01)
        time_str = shadcn.TextInput(label="Time (YYYY-MM-DD HH:MM)", value=drink["time"])
        sip_interval = shadcn.NumberInput(label="Sip Interval", value=drink["sip_interval"], min_value=1, max_value=60, step=1)
        updated = st.form_submit_button("Update Drink")
    if updated:
        try:
            new_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            if new_time > now:
                st.error("Cannot set a future time.")
            elif new_time < now - timedelta(hours=24):
                st.error("Can only update drinks from the past 24 hours.")
            else:
                update_drink(user_id, drink["id"], name, vol, alc_prop, new_time, int(sip_interval))
                st.success("Drink updated!")
                del st.session_state["edit_drink"]
                st.experimental_set_query_params(page="drinks")
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Error: {e}")
