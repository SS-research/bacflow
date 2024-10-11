import numpy as np
import pandas as pd
from datetime import datetime

from schemas import Drink

def calc_body_factor(height: int, weight: int, sex: str, model: str="seidl"):
    if model == "seidl":
        r_female = 0.31223 - 0.006446 * weight + 0.4466 * height
        r_male = 0.31608 - 0.004821 * weight + 0.4632 * height
    else:
        raise ValueError(f"Model '{model}' is not supported")

    r_female = np.clip(r_female, 0.44, 0.8)
    r_male = np.clip(r_male, 0.60, 0.87)

    if sex == "Female":
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
    height: float, 
    weight: float, 
    sex: str, 
    absorption_halflife: float, 
    beta: float, 
    start_time: datetime, 
    end_time: datetime, 
    model: str = "seidl"
) -> pd.DataFrame:
    if not drinks:
        return pd.DataFrame()

    r = calc_body_factor(height, weight, sex, model)
    bac_ts = cumulative_absorption(drinks, absorption_halflife, start_time, end_time)

    bac_ts['bac_excluding_elimination'] = bac_ts['kg_absorbed'] / (r * weight)
    bac_ts['eliminated'] = 0.0 

    for i in range(1, len(bac_ts)):
        current_bac = bac_ts.at[i, 'bac_excluding_elimination'] - bac_ts.at[i-1, 'eliminated']
        bac_ts.at[i, 'eliminated'] = bac_ts.at[i-1, 'eliminated'] + min(current_bac, beta * 60)

    bac_ts['bac'] = bac_ts['bac_excluding_elimination'] - bac_ts['eliminated']
    bac_ts['bac_perc'] = bac_ts['bac'] * 100

    return bac_ts