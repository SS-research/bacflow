from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from bacflow.modeling import calculate_bac_for_model
from bacflow.schemas import Drink, Model, Person, Food

# Mapping of food categories to absorption halflife in seconds (6, 9, 12, 15, 18 minutes)
FOOD_HALFLIFE_MAP = {
    "snack": 6 * 60,
    "light": 9 * 60,
    "moderate": 12 * 60,
    "full": 15 * 60,
    "heavy": 18 * 60,
}

def compute_halflife_vector(t_sec: np.ndarray, food_intakes: list[Food], default_halflife: float) -> np.ndarray:
    """
    Given a vector of time stamps (in seconds), compute an effective absorption halflife for each time point.
    For each t in t_sec, we use the most recent food intake (if any) to determine the halflife.
    If no food intake is available for a given t, default_halflife is used.
    """
    if not food_intakes:
        return np.full(t_sec.shape, default_halflife)
    # Sort food_intakes by time
    sorted_food = sorted(food_intakes, key=lambda f: f.time)
    food_times = np.array([f.time.timestamp() for f in sorted_food])
    food_values = np.array([FOOD_HALFLIFE_MAP.get(f.category.lower(), default_halflife) for f in sorted_food])
    # For each t in t_sec, find the index of the last food intake event (if any)
    indices = np.searchsorted(food_times, t_sec, side='right')
    # If no food intake before t, use default_halflife; else use the value from the most recent event.
    halflife_vector = np.where(indices > 0, food_values[indices - 1], default_halflife)
    return halflife_vector

def cumulative_absorption(
    drinks: list[Drink],
    start_time: datetime,
    end_time: datetime,
    dt: float,  # simulation time step in seconds
    default_halflife: float,
    food_intakes: list[Food] = None,
    initial_alc: float = 0.0
) -> pd.DataFrame:
    """
    Compute a time series of cumulative alcohol absorption (in kg) from a list of drinks.
    The absorption at each time step is computed using a dynamic absorption halflife derived
    from food intake data. The effective halflife vector is computed so that it has the same
    length and sampling as the simulation time vector.
    
    Parameters:
      - drinks: list of Drink objects
      - start_time: simulation starting datetime
      - end_time: simulation ending datetime
      - dt: simulation time step in seconds
      - default_halflife: default halflife (in seconds) when no food data is present (e.g. 12 min → 720 sec)
      - food_intakes: list of Food intake objects
      - initial_alc: active absorbed alcohol (in kg) at start_time
      
    Returns a DataFrame with columns 'time' and 'kg_absorbed'.
    """
    t_sec = np.arange(start_time.timestamp(), end_time.timestamp(), dt)
    halflife_vector = compute_halflife_vector(t_sec, food_intakes, default_halflife)
    ln2 = np.log(2)
    absorption_mat = np.zeros((len(drinks), len(t_sec)))
    
    for i, drink in enumerate(drinks):
        drink_start = drink.time.timestamp()
        # Compute time deltas for all simulation points
        time_deltas = t_sec - drink_start
        # For t < drink_start, absorption is 0
        positive_deltas = np.maximum(time_deltas, 0)
        # Compute absorption using the dynamic halflife at each time step
        absorption_mat[i, :] = drink.alc_kg * (1 - np.exp(- positive_deltas * ln2 / halflife_vector))
    
    kg_absorbed = absorption_mat.sum(axis=0) + initial_alc
    df = pd.DataFrame({'kg_absorbed': kg_absorbed, 'time': t_sec})
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def simulate(
    drinks: list[Drink],
    person: Person,
    start_time: datetime,
    end_time: datetime,
    dt: float,  # simulation time step in seconds
    default_halflife: float,
    initial_alc: float,
    simulation: list[Model],
    food_intakes: list[Food] = None
) -> dict[Model, pd.DataFrame]:
    """
    Runs the BAC simulation using the provided parameters.
    The simulation:
      - Computes a cumulative absorption timeseries (using dynamic halflife values).
      - For each simulation model, computes the BAC timeseries via its elimination kinetics.
    
    Returns a dict mapping each Model to its simulation DataFrame (which contains a 'bac' column).
    """
    if not drinks:
        return {}
    
    absorption = cumulative_absorption(drinks, start_time, end_time, dt, default_halflife, food_intakes, initial_alc)
    results = {}
    with ThreadPoolExecutor() as executor:
        future_to_model = {
            executor.submit(
                calculate_bac_for_model, person, absorption, model, dt
            ): model for model in simulation
        }
        for future in as_completed(future_to_model):
            model = future_to_model[future]
            results[model] = future.result()
    return results

def aggregate_simulation_results(sim_results: dict[Model, pd.DataFrame]) -> pd.DataFrame:
    """
    Aggregate simulation results from different models into a single timeseries with mean and variance.
    Assumes all simulation DataFrames have the same time sampling and include a 'bac' column.
    
    Returns a DataFrame with columns: 'time', 'mean_bac', and 'var_bac'.
    """
    df_list = []
    for idx, (model, df) in enumerate(sim_results.items()):
        df_model = df[['time', 'bac']].copy()
        df_model = df_model.set_index('time')
        df_model.rename(columns={'bac': f'bac_{idx}'}, inplace=True)
        df_list.append(df_model)
    all_bac = pd.concat(df_list, axis=1)
    mean_bac = all_bac.mean(axis=1)
    var_bac = all_bac.var(axis=1)
    aggregated = pd.DataFrame({'time': all_bac.index, 'mean_bac': mean_bac, 'var_bac': var_bac})
    return aggregated.reset_index(drop=True)

def identify_threshold_times(aggregated_ts: pd.DataFrame, driving_limit: float, tolerance: float = 1e-3) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """
    Given an aggregated BAC timeseries (with 'mean_bac'), determine:
      - drive_safe_time: The first time (of the final continuous segment) when BAC falls below the driving_limit.
      - sober_time: The first time when BAC is effectively zero (within a tolerance) and remains at zero.
    
    Returns a tuple (drive_safe_time, sober_time) or (None, None) if not found.
    """
    times = aggregated_ts['time']
    mean_bac = aggregated_ts['mean_bac']
    
    drive_safe_time = None
    sober_time = None
    
    # Identify the final contiguous segment where BAC is below driving_limit.
    below_thresh = mean_bac < driving_limit
    segments = (below_thresh != below_thresh.shift()).cumsum()
    valid_segments = aggregated_ts[below_thresh].groupby(segments)
    if valid_segments.ngroups:
        # Use the last segment (i.e. the final time BAC is below limit)
        last_seg_indices = aggregated_ts.index[segments == segments.iloc[-1]]
        drive_safe_time = aggregated_ts.loc[last_seg_indices[0], 'time']
    
    # Similarly, for sober time use a tolerance (BAC effectively zero)
    sober_bool = mean_bac <= tolerance
    segments_sober = (sober_bool != sober_bool.shift()).cumsum()
    valid_sober = aggregated_ts[sober_bool].groupby(segments_sober)
    if valid_sober.ngroups:
        last_sober_indices = aggregated_ts.index[segments_sober == segments_sober.iloc[-1]]
        sober_time = aggregated_ts.loc[last_sober_indices[0], 'time']
    
    return drive_safe_time, sober_time
