import streamlit as st
import streamlit_shadcn_ui as shadcn
from database import update_user_details
from datetime import datetime

if "user" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

user = st.session_state["user"]

if user.get("dob"):
    st.info("Your profile is already completed.")
    st.stop()

st.title("Onboarding")
st.write("Please complete your profile details. Once set, they cannot be changed.")

with st.form("onboarding_form"):
    dob = shadcn.DateInput(label="Date of Birth", default_value=datetime(2000, 1, 1))
    height = shadcn.NumberInput(label="Height (cm)", min_value=100, max_value=250, value=170)
    weight = shadcn.NumberInput(label="Weight (kg)", min_value=30, max_value=200, value=70)
    sex = shadcn.Select(label="Sex", options=["M", "F"])
    driver_profile = shadcn.Select(label="Driver Profile", options=["general", "novice", "professional"])
    submitted = st.form_submit_button("Submit")

if submitted:
    dob_str = dob.strftime("%Y-%m-%d")
    update_user_details(user["id"], dob_str, float(height), float(weight), sex, driver_profile)
    st.session_state["user"].update({
        "dob": dob_str,
        "height": float(height),
        "weight": float(weight),
        "sex": sex,
        "driver_profile": driver_profile
    })
    st.success("Profile updated!")
    st.experimental_set_query_params(page="simulation")
    st.experimental_rerun()
