import numpy as np
import pandas as pd
from datetime import datetime

from schemas import Drink

def calc_body_factor(age: int, height: int, weight: int, sex: str, model: str):
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
            r_female = 0.
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
        raise ValueError(f"unknown sex — {sex}")

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

def calc_bac_ts(
    drinks: list[Drink], 
    age: int,
    height: float, 
    weight: float, 
    sex: str, 
    absorption_halflife: float, 
    beta: float, 
    start_time: datetime, 
    end_time: datetime, 
    simulation: list[str]
) -> dict[str, pd.DataFrame]:
    if not drinks:
        return {}

    absorption = cumulative_absorption(drinks, absorption_halflife, start_time, end_time)
    results = {}

    for model in simulation:
        results[model] = calculate_bac_for_model(age, height, weight, sex, beta, absorption, model)

    return results

def calculate_bac_for_model(
    age: int,
    height: float, 
    weight: float, 
    sex: str, 
    beta: float, 
    absorption: pd.DataFrame, 
    model: str
) -> pd.DataFrame:
    r = calc_body_factor(age, height, weight, sex, model)

    model_bac_ts = absorption.copy()
    model_bac_ts['bac_excluding_elimination'] = model_bac_ts['kg_absorbed'] / (r * weight)
    model_bac_ts['eliminated'] = 0.0 

    for i in range(1, len(model_bac_ts)):
        current_bac = model_bac_ts.at[i, 'bac_excluding_elimination'] - model_bac_ts.at[i-1, 'eliminated']
        model_bac_ts.at[i, 'eliminated'] = model_bac_ts.at[i-1, 'eliminated'] + min(current_bac, beta * 60)

    model_bac_ts['bac'] = model_bac_ts['bac_excluding_elimination'] - model_bac_ts['eliminated']
    model_bac_ts['bac_perc'] = model_bac_ts['bac'] * 100

    return model_bac_ts