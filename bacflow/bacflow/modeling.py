from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from bacflow.schemas import Drink, Model, Person, Sex

simulation_M = [Model.Forrest, Model.Seidl, Model.Widmark, Model.Watson, Model.average, Model.Ulrich]
simulation_F = [Model.Forrest, Model.Seidl, Model.Widmark, Model.Watson, Model.average]

class UnsupportedModelException(Exception):
    def __init__(self, model: Model, sex: Sex):
        self.message = f"The model {model} is not supported for subjects of sex {sex}"
    def __str__(self):
        return self.message

def _F_calculate_body_factor(person: Person, model: str) -> float:
    if person.sex == Sex.F and model not in simulation_F:
        raise UnsupportedModelException(model, person.sex)
    age, height, weight = person.age, person.height, person.weight
    match model:
        case Model.Forrest:
            r = 0.8736 - 0.0124 * weight / height**2
        case Model.Seidl:
            r = 0.31223 - 0.006446 * weight + 0.4466 * height
        case Model.Widmark:
            r = 0.55
        case Model.Watson:
            r = 0.29218 + (12.666 * height - 2.4846) / weight
        case Model.average:
            r = 0.50766 + 0.11165 * height - weight * (0.001612 + 0.0031 / height**2) - (1 / weight) * (0.62115 - 3.1665 * height)
    return np.clip(r, 0.44, 0.8)

def _M_calculate_body_factor(person: Person, model: str) -> float:
    if person.sex == Sex.M and model not in simulation_M:
        raise UnsupportedModelException(model, person.sex)
    age, height, weight = person.age, person.height, person.weight
    match model:
        case Model.Forrest:
            r = 1.0178 - 0.012127 * weight / height**2
        case Model.Seidl:
            r = 0.31608 - 0.004821 * weight + 0.4632 * height
        case Model.Widmark:
            r = 0.68
        case Model.Watson:
            r = 0.39834 + (12.725 * height - 0.11275 * age + 2.8993) / weight
        case Model.average:
            r = 0.62544 + 0.13664 * height - weight * (0.00189 + 0.002425 / height**2) + (1 / weight) * (0.57986 + 2.545 * height - 0.02255 * age)
        case Model.Ulrich:
            r = 0.715 - 0.00462 * weight + 0.22 * height
    return np.clip(r, 0.60, 0.87)

def calculate_body_factor(person: Person, model: str) -> float:
    """Body factor r of subjects using a Widmark-family model."""
    return _M_calculate_body_factor(person, model) if person.sex == Sex.M else _F_calculate_body_factor(person, model)

def calc_aer(sex: Sex, bac: float) -> float:
    """Alcohol elimination rate (AER) based on Simic & Tasic (2007)."""
    if sex == Sex.F:
        aer = 0.16 + (bac * 0.05)
    else:  # Sex.M
        aer = 0.14 + (bac * 0.05)
    return np.clip(aer, 0.009, 0.035)

def calculate_bac_for_model(
    person: Person,
    absorption: pd.DataFrame, 
    model: Model,
    simulation_dt: float  # time step in seconds
) -> pd.DataFrame:
    """
    Given a cumulative absorption timeseries (with 'kg_absorbed'),
    compute the BAC timeseries for a given model.
    The elimination is computed at each time step (adjusted by simulation_dt).
    Returns a DataFrame with columns 'time', 'bac', and 'bac_perc'.
    """
    r = calculate_body_factor(person, model)
    model_bac_ts = absorption.copy()
    model_bac_ts['bac_excluding_elimination'] = model_bac_ts['kg_absorbed'] / (r * person.weight)
    model_bac_ts['eliminated'] = 0.0 

    for i in range(1, len(model_bac_ts)):
        current_bac = model_bac_ts.at[i, 'bac_excluding_elimination'] - model_bac_ts.at[i-1, 'eliminated']
        prev_bac = model_bac_ts.at[i-1, 'bac'] if 'bac' in model_bac_ts.columns else 0
        current_aer = calc_aer(person.sex, prev_bac)
        elimination_interval = current_aer * (simulation_dt / 60)
        model_bac_ts.at[i, 'eliminated'] = model_bac_ts.at[i-1, 'eliminated'] + min(current_bac, elimination_interval)
    
    model_bac_ts['bac'] = model_bac_ts['bac_excluding_elimination'] - model_bac_ts['eliminated']
    model_bac_ts['bac_perc'] = model_bac_ts['bac'] * 100
    return model_bac_ts
