from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from schemas import Drink


simulation_male = ["forrest", "seidl", "widmark", "ulrich", "watson", "average"]
simulation_female = ["forrest", "seidl", "widmark", "watson", "average"]


def calc_body_factor(age: int, height: int, weight: int, sex: str, model: str):
    """Volume distribution of alcohol (VDA) in the body."""
    match model:
        case "forrest":
            r_female = 0.8736 - 0.0124 * weight / height**2
            r_male = 1.0178 - 0.012127 * weight / height**2
        case "seidl":
            r_female = 0.31223 - 0.006446 * weight + 0.4466 * height
            r_male = 0.31608 - 0.004821 * weight + 0.4632 * height
        case "widmark":
            r_female = 0.55
            r_male = 0.68
        case "ulrich":
            r_female = 0.0
            r_male = 0.715 - 0.00462 * weight + 0.22 * height
        case "watson":
            r_female = 0.29218 + (12.666 * height - 2.4846) / weight
            r_male = 0.39834 + (12.725 * height - 0.11275 * age + 2.8993) / weight
        case "average":
            r_female = (
                0.50766
                + 0.11165 * height
                - weight * (0.001612 + 0.0031 / height**2)
                - (1 / weight) * (0.62115 - 3.1665 * height)
            )
            r_male = (
                0.62544
                + 0.13664 * height
                - weight * (0.00189 + 0.002425 / height**2)
                + (1 / weight) * (0.57986 + 2.545 * height - 0.02255 * age)
            )
        case _:
            raise ValueError(f"Model '{model}' is not supported")

    r_female = np.clip(r_female, 0.44, 0.8)
    r_male = np.clip(r_male, 0.60, 0.87)

    if sex == "Female":
        if model == "ulrich":
            raise ValueError("The Ulrich model supports only male subjects")
        return r_female
    elif sex == "Male":
        return r_male
    else:
        raise ValueError(f"Unknown sex — {sex}")


def calc_aer(sex: str, bac: float) -> float:
    """alcohol elimination rate (AER) [1]_

    References:
    .. [1] M. Simic, and M. Tasic, 2007, 
       https://pubmed.ncbi.nlm.nih.gov/17196778
    """
    if sex == 'Female':
        aer = 0.16 + (bac * 0.05)
    elif sex == 'Male':
        aer = 0.14 + (bac * 0.05)
    else:
        raise ValueError(f"Unknown sex: {sex}")

    aer = np.clip(aer, 0.009, 0.035)

    return aer


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
