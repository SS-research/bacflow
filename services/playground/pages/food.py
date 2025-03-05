import streamlit as st
import streamlit_shadcn_ui as shadcn
from datetime import datetime, timedelta, timezone
from database import get_food, add_food, delete_food, update_food
import pandas as pd

if "user" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

user = st.session_state["user"]
user_id = user["id"]

st.title("Food Intake History")

now = datetime.now(timezone.utc)
from_time = now - timedelta(hours=24)
to_time = now

foods = get_food(user_id, from_time, to_time)

st.write("Your food intake in the last 24 hours:")
if foods:
    df = pd.DataFrame(foods)
    st.dataframe(df)
else:
    st.info("No food intake recorded in the last 24 hours.")

st.header("Add Food Intake")
with st.form("add_food_form"):
    name = shadcn.TextInput(label="Food Name", placeholder="e.g., Sandwich")
    time_str = shadcn.TextInput(label="Time of Consumption (YYYY-MM-DD HH:MM)", placeholder=now.strftime("%Y-%m-%d %H:%M"))
    category = shadcn.Select(label="Food Category", options=["snack", "light", "moderate", "full", "heavy"])
    submit = st.form_submit_button("Add Food")

if submit:
    try:
        food_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if food_time > now:
            st.error("Cannot add food intake in the future.")
        elif food_time < now - timedelta(hours=24):
            st.error("Can only add food intake from the past 24 hours.")
        else:
            add_food(user_id, name, food_time, category)
            st.success("Food intake added!")
            st.experimental_rerun()
    except Exception as e:
        st.error(f"Error: {e}")

st.header("Manage Food Intake")
for food in foods:
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.write(f"{food['name']} ({food['category']}) at {food['time']}")
    with col2:
        if st.button("Delete", key=f"delete_food_{food['id']}"):
            delete_food(user_id, food["id"])
            st.experimental_rerun()
    with col3:
        if st.button("Edit", key=f"edit_food_{food['id']}"):
            st.session_state["edit_food"] = food
            st.experimental_set_query_params(page="food", action="edit", food_id=food["id"])
            st.experimental_rerun()

query_params = st.experimental_get_query_params()
if query_params.get("action") == ["edit"] and "edit_food" in st.session_state:
    food = st.session_state["edit_food"]
    st.subheader("Edit Food Intake")
    with st.form("edit_food_form"):
        name = shadcn.TextInput(label="Food Name", value=food["name"])
        time_str = shadcn.TextInput(label="Time (YYYY-MM-DD HH:MM)", value=food["time"])
        category = shadcn.Select(label="Food Category", options=["snack", "light", "moderate", "full", "heavy"], value=food["category"])
        updated = st.form_submit_button("Update Food")
    if updated:
        try:
            new_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            if new_time > now:
                st.error("Cannot set a future time.")
            elif new_time < now - timedelta(hours=24):
                st.error("Can only update food intake from the past 24 hours.")
            else:
                update_food(user_id, food["id"], name, new_time, category)
                st.success("Food intake updated!")
                del st.session_state["edit_food"]
                st.experimental_set_query_params(page="food")
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Error: {e}")
