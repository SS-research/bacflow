import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure


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

def cumalative_absorption(drinks, absorption_halflife, start_time, end_time):
    t_sec = np.arange(start_time, end_time, 60)
    absorption_mat = np.zeros((len(drinks), len(t_sec)))

    for i, drink in enumerate(drinks):
        absorption_mat[i, :] = drink['alc_kg'] * (1 - np.exp(-(t_sec - drink['time']) * np.log(2) / absorption_halflife))

    absorption_mat[absorption_mat < 0] = 0
    kg_absorbed = absorption_mat.sum(axis=0)

    return pd.DataFrame({'kg_absorbed': kg_absorbed, 'time': t_sec})

def calc_bac_ts(drinks, height, weight, sex, absorption_halflife, beta, start_time, end_time) -> pd.DataFrame:
    if not drinks: return pd.DataFrame()
    for drink in drinks:
        drink['alc_vol'] = drink['vol'] * drink['alc_prop']
        drink['alc_kg'] = drink['alc_vol'] * 0.789

    r = calc_widmark_factor(height, weight, sex)
    bac_ts = cumalative_absorption(drinks, absorption_halflife, start_time, end_time)

    bac_ts['bac_excluding_elimination'] = bac_ts['kg_absorbed'] / (r * weight)
    bac_ts['eliminated'] = 0.0 

    for i in range(1, len(bac_ts)):
        current_bac = bac_ts.at[i, 'bac_excluding_elimination'] - bac_ts.at[i-1, 'eliminated']
        bac_ts.at[i, 'eliminated'] = bac_ts.at[i-1, 'eliminated'] + min(current_bac, beta * 60)

    bac_ts['bac'] = bac_ts['bac_excluding_elimination'] - bac_ts['eliminated']
    bac_ts['bac_perc'] = bac_ts['bac'] * 100

    try:
        ts_end_i = max(bac_ts[bac_ts['bac'] > 0].index[-1], 5 * 60)
    except IndexError:
        ts_end_i = 0

    return bac_ts.iloc[:ts_end_i+1]

def plot_bac_ts(bac_ts, drink_info) -> Figure:
    figure = plt.figure(figsize=(10, 5))
    plt.plot(bac_ts['time'] / 3600, bac_ts['bac_perc'], color='skyblue', linewidth=2, label="BAC")
    plt.fill_between(bac_ts['time'] / 3600, bac_ts['bac_perc'], color='skyblue', alpha=0.3)
    
    plt.xlabel('Time (hours)')
    plt.ylabel('BAC (%)')
    plt.title('Blood Alcohol Concentration Over Time')
    plt.grid(True)

    return figure
