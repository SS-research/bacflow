import streamlit as st
import streamlit_shadcn_ui as shadcn

# Configure the page
st.set_page_config(page_title="BACflow", layout="wide")

def main():
    # Read query parameters to determine the current page.
    query_params = st.experimental_get_query_params()
    current_page = query_params.get("page", ["login"])[0]

    # Create a top navigation bar with modern shadcn components.
    # (Assuming shadcn.Navbar is a hypothetical component for navigation.)
    nav_options = ["Login", "Onboarding", "Drinks", "Food", "Simulation"]
    selected = shadcn.Select(
        label="Navigate",
        options=nav_options,
        default=current_page.capitalize() if current_page else "Login"
    )
    # Convert selected option to lower-case to use as page key.
    selected_page = selected.lower()

    # If the user selects a different page, update the query parameters.
    if selected_page != current_page:
        st.experimental_set_query_params(page=selected_page)
        st.experimental_rerun()

    # Route to the appropriate page based on the query parameter.
    if selected_page == "login":
        import pages.login as login_page
        login_page.main()
    elif selected_page == "onboarding":
        import pages.onboarding as onboarding_page
        onboarding_page.main()
    elif selected_page == "drinks":
        import pages.drinks as drinks_page
        drinks_page.main()
    elif selected_page == "food":
        import pages.food as food_page
        food_page.main()
    elif selected_page == "simulation":
        import pages.simulation as simulation_page
        simulation_page.main()
    else:
        st.error("Page not found.")

if __name__ == "__main__":
    main()
