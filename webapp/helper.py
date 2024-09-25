import numpy as np
import pandas as pd

def calc_widmark_factor(height, weight, sex):
    r_female = 0.31223 - 0.006446 * weight + 0.4466 * height
    r_male = 0.31608 - 0.004821 * weight + 0.4632 * height
    r_female = np.clip(r_female, 0.44, 0.8)
    r_male = np.clip(r_male, 0.60, 0.87)

    if sex == "Female":
        return r_female
    elif sex == "Male":
        return r_male
    else:
        return (r_male + r_female) / 2

def cumulative_absorption(drinks, absorption_halflife, start_time, end_time):
    t_sec = np.arange(start_time, end_time, 60)
    absorption_mat = np.zeros((len(drinks), len(t_sec)))

    for i, drink in enumerate(drinks):
        absorption_mat[i, :] = drink['alc_kg'] * (1 - np.exp(-(t_sec - drink['time']) * np.log(2) / absorption_halflife))

    absorption_mat[absorption_mat < 0] = 0
    kg_absorbed = absorption_mat.sum(axis=0)

    df = pd.DataFrame({'kg_absorbed': kg_absorbed, 'time': t_sec})
    df['time'] = pd.to_datetime(df['time'], unit='s')

    return df

def calc_bac_ts(drinks, height, weight, sex, absorption_halflife, beta, start_time, end_time):
    if not drinks:
        return pd.DataFrame()
    for drink in drinks:
        drink['alc_vol'] = drink['vol'] * drink['alc_prop']
        drink['alc_kg'] = drink['alc_vol'] * 0.789

    r = calc_widmark_factor(height, weight, sex)
    bac_ts = cumulative_absorption(drinks, absorption_halflife, start_time, end_time)

    bac_ts['bac_excluding_elimination'] = bac_ts['kg_absorbed'] / (r * weight)
    bac_ts['eliminated'] = 0.0 

    for i in range(1, len(bac_ts)):
        current_bac = bac_ts.at[i, 'bac_excluding_elimination'] - bac_ts.at[i-1, 'eliminated']
        bac_ts.at[i, 'eliminated'] = bac_ts.at[i-1, 'eliminated'] + min(current_bac, beta * 60)

    bac_ts['bac'] = bac_ts['bac_excluding_elimination'] - bac_ts['eliminated']
    bac_ts['bac_perc'] = bac_ts['bac'] * 100

    return bac_ts