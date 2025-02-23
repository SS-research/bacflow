from deltatime import timedelta

import pandas as pd

from bacflow.compute import calc_aer, calc_body_factor, cumulative_absorption
from bacflow.schemas import Drink


def simulate(
    drinks: list[Drink], 
    age: int,
    height: float, 
    weight: float, 
    sex: str, 
    absorption_halflife: float, 
    simulation: list[str]
) -> dict[str, pd.DataFrame]:
    """
    Runs the BAC simulation using the provided parameters.
    """
    if not drinks:
        return {}
    
    # Sort drinks based on time and split into sips.
    drinks = sorted(
        [sip for drink in drinks for sip in drink.split_into_sips()],
        key=lambda x: x.time
    )
    
    start_time = min(drink.time for drink in drinks)
    end_time = max(drink.time for drink in drinks) + timedelta(seconds=60 * 60 * 24)

    absorption = cumulative_absorption(drinks, absorption_halflife, start_time, end_time)
    absorption_end_idx = absorption['kg_absorbed'].round(3).idxmax()
    results = {}
    last_elim_idx = 0

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor() as executor:
        future_to_model = {
            executor.submit(
                calculate_bac_for_model, age, height, weight, sex, absorption, model, absorption_end_idx
            ): model for model in simulation
        }
        for future in as_completed(future_to_model):
            model = future_to_model[future]
            result, elim_idx = future.result()
            results[model] = result
            last_elim_idx = max(last_elim_idx, elim_idx)

    last_elim_idx = min(last_elim_idx + 1, len(absorption))

    for model in results:
        results[model] = results[model].loc[:last_elim_idx]

    return results


def calculate_bac_for_model(
    age: int,
    height: float, 
    weight: float, 
    sex: str, 
    absorption: pd.DataFrame, 
    model: str,
    absorption_end_idx: int
) -> tuple[pd.DataFrame, int]:
    r = calc_body_factor(age, height, weight, sex, model)

    model_bac_ts = absorption.copy()
    model_bac_ts['bac_excluding_elimination'] = model_bac_ts['kg_absorbed'] / (r * weight)
    model_bac_ts['eliminated'] = 0.0 

    for i in range(1, len(model_bac_ts)):
        # Available alcohol at current step (before elimination)
        current_bac = model_bac_ts.at[i, 'bac_excluding_elimination'] - model_bac_ts.at[i-1, 'eliminated']
        # Compute dynamic elimination rate using previous BAC value
        prev_bac = model_bac_ts.at[i-1, 'bac']
        current_aer = calc_aer(sex, prev_bac)
        # For a 1-minute interval, elimination is current_aer divided by 60
        elimination_interval = current_aer / 60
        model_bac_ts.at[i, 'eliminated'] = model_bac_ts.at[i-1, 'eliminated'] + min(current_bac, elimination_interval)

    model_bac_ts['bac'] = model_bac_ts['bac_excluding_elimination'] - model_bac_ts['eliminated']
    model_bac_ts['bac_perc'] = model_bac_ts['bac'] * 100

    bac_zero_idx = model_bac_ts.loc[absorption_end_idx:].loc[model_bac_ts['bac'] == 0.0].index.min()

    if pd.isna(bac_zero_idx):
        bac_zero_idx = len(model_bac_ts)

    return model_bac_ts, bac_zero_idx
