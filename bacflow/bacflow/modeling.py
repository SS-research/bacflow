from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from schemas import Drink, Model, Person, Sex


simulation_M = [Model.Forrest, Model.Seidl, Model.Widmark, Model.Watson, Model.average, Model.Ulrich]
simulation_F = [Model.Forrest, Model.Seidl, Model.Widmark, Model.Watson, Model.average]


class UnsupportedModelException(Exception):
    def __init__(self, model: Model, sex: Sex):
        self.message = f"The model {model} is not supported for subjects of sex {sex}"

    def __str__(self):
        return self.message


def _F_calculate_body_factor(person: Person, model: str) -> float: ...
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
    """body factor $r$ of subjects with a model of the Widmark family"""
    return _M_calculate_body_factor(person, model) if person.sex == Sex.M else _F_calculate_body_factor(person, model)


def calc_aer(sex: Sex, bac: float) -> float:
    """alcohol elimination rate (AER) [1]_

    References:
    .. [1] M. Simic, and M. Tasic, 2007, 
       https://pubmed.ncbi.nlm.nih.gov/17196778
    """
    if sex == Sex.F:
        aer = 0.16 + (bac * 0.05)

    if sex == Sex.M:
        aer = 0.14 + (bac * 0.05)

    aer = np.clip(aer, 0.009, 0.035)

    return aer


def calculate_bac_for_model(
    person: Person
    absorption: pd.DataFrame, 
    model: Model,
    absorption_end_idx: int
) -> tuple[pd.DataFrame, int]:
    r = calculate_body_factor(person, model)

    model_bac_ts = absorption.copy()
    model_bac_ts['bac_excluding_elimination'] = model_bac_ts['kg_absorbed'] / (r * person.weight)
    model_bac_ts['eliminated'] = 0.0 

    for i in range(1, len(model_bac_ts)):
        # Available alcohol at current step (before elimination)
        current_bac = model_bac_ts.at[i, 'bac_excluding_elimination'] - model_bac_ts.at[i-1, 'eliminated']
        # Compute dynamic elimination rate using previous BAC value
        prev_bac = model_bac_ts.at[i-1, 'bac']
        current_aer = calc_aer(person.sex, prev_bac)
        # For a 1-minute interval, elimination is current_aer divided by 60
        elimination_interval = current_aer / 60
        model_bac_ts.at[i, 'eliminated'] = model_bac_ts.at[i-1, 'eliminated'] + min(current_bac, elimination_interval)

    model_bac_ts['bac'] = model_bac_ts['bac_excluding_elimination'] - model_bac_ts['eliminated']
    model_bac_ts['bac_perc'] = model_bac_ts['bac'] * 100

    bac_zero_idx = model_bac_ts.loc[absorption_end_idx:].loc[model_bac_ts['bac'] == 0.0].index.min()

    if pd.isna(bac_zero_idx):
        bac_zero_idx = len(model_bac_ts)

    return model_bac_ts, bac_zero_idx
