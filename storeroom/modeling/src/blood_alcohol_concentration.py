def calc_widmark_factor(height, weight, sex):
    r_female = 0.31223 - 0.006446 * weight + 0.4466 * height
    r_male = 0.31608 - 0.004821 * weight + 0.4632 * height
    r_female[r_female < 0.44] = 0.44
    r_female[r_female > 0.8] = 0.8
    r_male[r_male < 0.60] = 0.60
    r_male[r_male > 0.87] = 0.87
    
    if sex == "female":
        return r_female
    elif sex == "male":
        return r_male
    else:  # take the mean if sex is unspecified
        return (r_male + r_female) / 2

def cumulative_absorption(drinks, absorption_halflife, start_time, end_time):
    absorption_minutes = round((end_time - start_time) / 60)
    t_sec = list(range(start_time, end_time, 60))
    absorption_mat = [[0] * absorption_minutes for _ in range(max(len(drinks), 1))]
    for i in range(len(drinks)):
        absorption_mat[i] = [drinks["alc_kg"][i] * (1 - exp(-(t - drinks["time"][i]) * log(2) / absorption_halflife)) for t in t_sec]
    absorption_mat = [[max(x, 0) for x in row] for row in absorption_mat]
    kg_absorbed = [sum(row) for row in absorption_mat]
    return {"kg_absorbed": kg_absorbed, "time": t_sec}

def calc_bac_ts(drinks, height, weight, sex, absorption_halflife, beta, start_time, end_time):
    drinks["alc_vol"] = drinks["vol"] * drinks["alc_prop"]  # in litres
    drinks["alc_kg"] = drinks["alc_vol"] * 0.789  # 0.789 is the weight of one liter of alcohol
    r = calc_widmark_factor(height, weight, sex)
    
    # "Starting" a data.frame time series to hold information about different aspects of
    # the Blood Alcohol Concentration (bac)
    bac_ts = cumulative_absorption(drinks, absorption_halflife, start_time, end_time)
    bac_ts["time"] = pd.to_datetime(bac_ts["time"], origin="1970-01-01", tz="UTC")
    
    bac_ts["bac_excluding_elimination"] = bac_ts["kg_absorbed"] / (r * weight)
    bac_ts["eliminated"] = [0] * len(bac_ts)
    for i in range(2, len(bac_ts)):
        current_bac = bac_ts["bac_excluding_elimination"][i] - bac_ts["eliminated"][i - 1]
        bac_ts["eliminated"][i] = bac_ts["eliminated"][i - 1] + min(current_bac, beta * 60)  # We can't eliminate more bac than we got...
    
    bac_ts["bac"] = bac_ts["bac_excluding_elimination"] - bac_ts["eliminated"]
    bac_ts["bac_perc"] = bac_ts["bac"] * 100
    # Removing the end of the time series
    ts_end_i = max(bac_ts[bac_ts["bac"] > 0].index, 5 * 60)
    bac_ts = bac_ts.iloc[:ts_end_i, :]
    return bac_ts

##### Other support functions #####

def plot_bac_ts(bac_ts, drinks, time_now, drink_info):
    drink_color = {drink: color for drink, color in zip(drink_info["drink"], drink_info["color"])}
    
    import matplotlib.pyplot as plt
    import numpy as np
    
    plt.subplot(1, 2, 1)
    plt.plot(bac_ts["time"], bac_ts["bac_perc"], color="k", ylim=(0, max(bac_ts["bac_perc"])), bty="L", yaxs="i", xlabel="", ylabel="% Blood Alcohol Concentration")
    plt.plot(bac_ts[bac_ts["time"] <= time_now]["time"], bac_ts[bac_ts["time"] <= time_now]["bac_perc"], color="skyblue", lwd=4)
    plt.plot(bac_ts[bac_ts["time"] > time_now]["time"], bac_ts[bac_ts["time"] > time_now]["bac_perc"], color="skyblue", lwd=4, lty=2)
    if time_now >= min(bac_ts["time"]) and time_now <= max(bac_ts["time"]):
        curr_i = np.argmin(np.abs(bac_ts["time"] - time_now))
        plt.plot(bac_ts["time"][curr_i], bac_ts["bac_perc"][curr_i], color="orange", pch=19, lwd=4)
        plt.text(bac_ts["time"][curr_i], bac_ts["bac_perc"][curr_i], f"{round(bac_ts['bac_perc'][curr_i], 3)}%", lwd=4, fontdict={"va": "top", "ha": "left"}, position=(0, 1))
    
    plt.subplot(1, 2, 2)
    plt.plot([], [], color="k", label="")
    if len(drinks) > 0:
        drink_y_pos = -((np.arange(len(drinks)) - 1) % 3)
        plt.plot(drinks["time"], drink_y_pos, pch=19, ylim=(-2.5, 0.5), color=[drink_color[drink] for drink in drinks["name"]], xlabel="", ylabel="", xlim=plt.xlim(bac_ts["time"]))
        plt.text(drinks["time"], drink_y_pos, [drink for drink in drinks["name"]], color=[drink_color[drink] for drink in drinks["name"]], fontdict={"va": "top", "ha": "left"}, position=(0, 1))
    else:
        plt.plot([], [], color="k", label="")
    
    plt.show()