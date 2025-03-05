import streamlit as st
import streamlit_shadcn_ui as shadcn
from database import init_db, check_login
from datetime import datetime

# Initialize the database (if not already done)
init_db()

st.title("Login")

with st.form("login_form"):
    username = shadcn.TextInput(label="Username", placeholder="Enter your username")
    password = shadcn.PasswordInput(label="Password", placeholder="Enter your password")
    submitted = st.form_submit_button("Login")

if submitted:
    user = check_login(username, password)
    if user:
        st.session_state["user"] = user
        st.success("Logged in successfully!")
        # If the user has not completed onboarding (e.g. missing dob), send them there; else go to simulation.
        next_page = "onboarding" if not user.get("dob") else "simulation"
        st.experimental_set_query_params(page=next_page)
        st.experimental_rerun()
    else:
        st.error("Invalid credentials. Please try again.")
