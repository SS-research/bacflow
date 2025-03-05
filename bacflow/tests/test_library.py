import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta, timezone

# Import functions from the library modules
from bacflow.simulation import (
    compute_halflife_vector,
    cumulative_absorption,
    simulate,
    aggregate_simulation_results,
    identify_threshold_times,
)
from bacflow.modeling import calculate_bac_for_model, simulation_M, simulation_F
from bacflow.plotting import plot_simulation
from bacflow.schemas import Drink, Food, Person, Model, Sex

# Use a fixed base time for testing (UTC)
BASE_TIME = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_person():
    # A sample person: 30 years old male, 1.75m tall, 70kg.
    return Person(age=30, height=1.75, weight=70, sex=Sex.M)

@pytest.fixture
def sample_drink():
    # A sample drink at 00:10 on Jan 1, 2024.
    dt = datetime(2024, 1, 1, 0, 10)
    # For example, 330ml beer at 5% alcohol → 0.33 L * 0.05 * 0.789 ≈ 0.0130 kg alcohol.
    return Drink(name="Beer", vol=0.33, alc_prop=0.05, time=dt, sip_interval=1)

@pytest.fixture
def sample_food():
    # A sample food intake at 00:05 on Jan 1, 2024.
    dt = datetime(2024, 1, 1, 0, 5)
    return Food(name="Burger", time=dt, category="heavy")

# ------------------------------------------------------------------------------
# Tests for dynamic absorption: compute_halflife_vector
# ------------------------------------------------------------------------------

def test_compute_halflife_vector_no_food():
    """When no food intake is provided, all halflife values should equal the default."""
    t_sec = np.array([BASE_TIME.timestamp() + i * 60 for i in range(5)])
    default_halflife = 720  # 12 minutes in seconds
    halflife_vector = compute_halflife_vector(t_sec, [], default_halflife)
    np.testing.assert_allclose(halflife_vector, np.full(t_sec.shape, default_halflife))

def test_compute_halflife_vector_with_food():
    """When food intakes are provided, the effective halflife should update after events."""
    # Create two food events: one at +5 minutes ("light" → 9 min) and one at +15 minutes ("heavy" → 18 min)
    food1 = Food(name="Meal", time=BASE_TIME + timedelta(minutes=5), category="light")
    food2 = Food(name="Snack", time=BASE_TIME + timedelta(minutes=15), category="heavy")
    food_intakes = [food1, food2]
    t_sec = np.array([BASE_TIME.timestamp() + i * 60 for i in range(30)])  # 30-minute simulation
    default_halflife = 720  # default: 12 minutes (720 sec)
    halflife_vector = compute_halflife_vector(t_sec, food_intakes, default_halflife)
    
    # Before first food event, use default.
    for i in range(5):
        assert halflife_vector[i] == default_halflife
    # Between 5 and 15 minutes, use food1's value ("light": 9 minutes = 540 sec).
    for i in range(5, 15):
        assert halflife_vector[i] == 9 * 60
    # After 15 minutes, use food2's value ("heavy": 18 minutes = 1080 sec).
    for i in range(15, len(t_sec)):
        assert halflife_vector[i] == 18 * 60

# ------------------------------------------------------------------------------
# Tests for cumulative absorption
# ------------------------------------------------------------------------------

def test_cumulative_absorption():
    """Test that absorption is computed correctly for a single drink."""
    # Create one drink that starts at BASE_TIME + 2 minutes.
    drink_time = BASE_TIME + timedelta(minutes=2)
    drink = Drink(name="Beer", vol=0.5, alc_prop=0.05, time=drink_time, sip_interval=1)
    drinks = [drink]
    
    start_time = BASE_TIME
    end_time = BASE_TIME + timedelta(minutes=30)
    dt = 60  # 1-minute time step
    default_halflife = 720  # 12 minutes in seconds
    
    # Compute absorption with no food intake and no initial alcohol.
    absorption_df = cumulative_absorption(
        drinks, start_time, end_time, dt, default_halflife, food_intakes=[], initial_alc=0.0
    )
    
    # Verify that time column is increasing with dt intervals.
    times = absorption_df["time"]
    assert all(times.diff().dropna() >= pd.Timedelta(seconds=dt))
    
    # Before the drink time, absorption should equal the initial_alc (0.0)
    idx_before_drink = absorption_df[absorption_df["time"] < drink_time].index
    np.testing.assert_allclose(absorption_df.loc[idx_before_drink, "kg_absorbed"], 0.0)
    
    # After the drink time, absorption should be > 0 and monotonically increasing.
    idx_after_drink = absorption_df[absorption_df["time"] >= drink_time].index
    values = absorption_df.loc[idx_after_drink, "kg_absorbed"].values
    assert np.all(np.diff(values) >= 0)

# ------------------------------------------------------------------------------
# Tests for simulate function
# ------------------------------------------------------------------------------

def test_simulate():
    """Test simulate produces a dictionary of DataFrames with expected columns."""
    # Create two drinks.
    drink1 = Drink(name="Wine", vol=0.2, alc_prop=0.12, time=BASE_TIME + timedelta(minutes=1), sip_interval=1)
    drink2 = Drink(name="Beer", vol=0.33, alc_prop=0.05, time=BASE_TIME + timedelta(minutes=5), sip_interval=1)
    drinks = [drink1, drink2]
    
    # Define a Person (male).
    person = Person(age=30, height=1.75, weight=70, sex=Sex.M)
    
    start_time = BASE_TIME
    end_time = BASE_TIME + timedelta(minutes=60)
    dt = 60  # 1-minute intervals
    default_halflife = 720
    initial_alc = 0.0
    
    # Use a single model from simulation_M.
    models = [Model.Seidl]
    sim_results = simulate(drinks, person, start_time, end_time, dt, default_halflife, initial_alc, models, food_intakes=[])
    
    assert isinstance(sim_results, dict)
    assert Model.Seidl in sim_results
    df = sim_results[Model.Seidl]
    # Check for required columns.
    for col in ["time", "bac", "bac_perc"]:
        assert col in df.columns

# ------------------------------------------------------------------------------
# Tests for aggregation of simulation results
# ------------------------------------------------------------------------------

def test_aggregate_simulation_results():
    """Test that aggregating two simulation outputs computes mean and variance correctly."""
    times = pd.date_range(start=BASE_TIME, periods=10, freq="T")
    df1 = pd.DataFrame({"time": times, "bac": np.linspace(0.1, 0.0, 10)})
    df2 = pd.DataFrame({"time": times, "bac": np.linspace(0.2, 0.0, 10)})
    sim_results = {Model.Seidl: df1, Model.Widmark: df2}
    
    aggregated = aggregate_simulation_results(sim_results)
    # Expected columns.
    assert set(aggregated.columns) == {"time", "mean_bac", "var_bac"}
    # Mean BAC.
    np.testing.assert_allclose(aggregated["mean_bac"], (df1["bac"] + df2["bac"]) / 2)
    # Variance.
    expected_var = (((df1["bac"] - (df1["bac"] + df2["bac"]) / 2) ** 2 +
                     (df2["bac"] - (df1["bac"] + df2["bac"]) / 2) ** 2) / 2)
    np.testing.assert_allclose(aggregated["var_bac"], expected_var)

# ------------------------------------------------------------------------------
# Tests for threshold identification
# ------------------------------------------------------------------------------

def test_identify_threshold_times():
    """Test that threshold identification returns plausible driving-safe and sober times."""
    times = pd.date_range(start=BASE_TIME, periods=20, freq="T")
    # Create a linearly decreasing BAC from 0.05 to 0.0.
    mean_bac = np.linspace(0.05, 0.0, 20)
    var_bac = np.zeros(20)
    aggregated = pd.DataFrame({"time": times, "mean_bac": mean_bac, "var_bac": var_bac})
    driving_limit = 0.02
    
    drive_safe_time, sober_time = identify_threshold_times(aggregated, driving_limit)
    
    # Both times should be identified.
    assert drive_safe_time is not None
    assert sober_time is not None
    # Since our series is strictly decreasing, the sober time should equal the last time.
    assert sober_time == aggregated["time"].iloc[-1]

# ------------------------------------------------------------------------------
# Tests for calculate_bac_for_model in modeling
# ------------------------------------------------------------------------------
def test_calculate_bac_for_model():
    """Test that BAC computation returns a DataFrame with expected structure and non-negative values."""
    times = pd.date_range(start=BASE_TIME, periods=10, freq="T")
    kg_absorbed = np.linspace(0, 0.1, 10)
    absorption_df = pd.DataFrame({"time": times, "kg_absorbed": kg_absorbed})
    
    person = Person(age=30, height=1.75, weight=70, sex=Sex.M)
    model = Model.Seidl
    dt = 60  # 1 minute
    
    result_df = calculate_bac_for_model(person, absorption_df, model, dt)
    # Expected columns.
    for col in ["time", "bac", "bac_perc"]:
        assert col in result_df.columns
    # Check that bac_perc is 100 times bac.
    np.testing.assert_allclose(result_df["bac_perc"], result_df["bac"] * 100)
    # Ensure non-negative values.
    assert (result_df["bac"] >= 0).all()

# ------------------------------------------------------------------------------
# Tests for plotting function
# ------------------------------------------------------------------------------
def test_plot_simulation():
    """Test that the plotting function returns a Plotly Figure with the expected traces."""
    times = pd.date_range(start=BASE_TIME, periods=10, freq="T")
    mean_bac = np.linspace(0.1, 0.0, 10)
    var_bac = np.linspace(0.001, 0.0, 10)
    aggregated = pd.DataFrame({"time": times, "mean_bac": mean_bac, "var_bac": var_bac})
    driving_limit = 0.02
    
    fig = plot_simulation(aggregated, driving_limit)
    # Import Plotly Figure for type checking.
    from plotly.graph_objs import Figure
    assert isinstance(fig, Figure)
    # Ensure that at least three traces exist (mean, confidence band, driving limit).
    assert len(fig.data) >= 3
