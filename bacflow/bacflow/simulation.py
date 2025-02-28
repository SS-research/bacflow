from concurrent.futures import ThreadPoolExecutor, as_completed
from deltatime import timedelta

import pandas as pd

from bacflow.modeling import calculate_bac_for_model
from bacflow.schemas import Drink, Person


def cumulative_absorption(drinks: list[Drink], absorption_halflife: int, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    t_sec = np.arange(start_time.timestamp(), end_time.timestamp(), 60)
    absorption_mat = np.zeros((len(drinks), len(t_sec)))

    for i, drink in enumerate(drinks):
        absorption_mat[i, :] = drink.alc_kg * (1 - np.exp(-(t_sec - drink.time.timestamp()) * np.log(2) / absorption_halflife))

    absorption_mat[absorption_mat < 0] = 0
    kg_absorbed = absorption_mat.sum(axis=0)

    df = pd.DataFrame({'kg_absorbed': kg_absorbed, 'time': t_sec})
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True).dt.tz_convert(start_time.tzinfo)
    return df


def simulate(
    drinks: list[Drink], 
    person: Person,
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

    with ThreadPoolExecutor() as executor:
        future_to_model = {
            executor.submit(
                calculate_bac_for_model, person, absorption, model, absorption_end_idx
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
