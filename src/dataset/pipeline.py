import pandas as pd
import numpy as np


def load_and_preprocess_data(dataframe, fill_method='ffill'):
    """
    Initial data loading and preprocessing, including handling missing values.
    """
    dataframe.fillna(method=fill_method, inplace=True)
    return dataframe


def normalize_and_remove_outliers(data):
    """
    Normalize sensor data using Z-score and remove outliers.
    """
    normalized_data = (data - data.mean()) / data.std()
    lower_bound = normalized_data.quantile(0.01)
    upper_bound = normalized_data.quantile(0.99)
    return normalized_data[(normalized_data > lower_bound) & (normalized_data < upper_bound)]


def segment_data(data, window_size_seconds=5):
    """
    Segment data into fixed-size windows using the 'timestamp' field to group data.
    This function calculates the time delta since the first timestamp and divides it into fixed-sized windows.
    """
    # Ensure 'timestamp' is a datetime object
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
    
    # Calculate windows based on the time difference in seconds from the start
    start_time = data['timestamp'].min()
    data['seconds_since_start'] = (data['timestamp'] - start_time).dt.total_seconds()
    data['window_id'] = (data['seconds_since_start'] // window_size_seconds).astype(int)
    
    return data


import pandas as pd
import numpy as np
from scipy.stats import kurtosis, skew
from scipy.signal import find_peaks, periodogram
from scipy.stats import median_abs_deviation
from scipy.signal import welch  # For spectral density estimation

def calculate_sway_area(data_x, data_y):
    """
    Calculate the integral of the absolute difference between data_x and data_y.
    """
    return np.trapz(abs(data_x - data_y))

def calculate_sway_volume(data_x, data_y, data_z):
    """
    Calculate a simplistic version of the sway volume as the product of integrals in all three dimensions.
    """
    area_xy = calculate_sway_area(data_x, data_y)
    area_yz = calculate_sway_area(data_y, data_z)
    area_xz = calculate_sway_area(data_x, data_z)
    return area_xy + area_yz + area_xz  # simple additive approximation

def calculate_gait_features(acc_data):
    """
    Calculate gait-related features such as steps, cadence, velocity, and residual step length.
    """
    g_mag = np.sqrt(np.sum(np.square(acc_data), axis=1))  # magnitude of gravity corrected acceleration
    peaks, _ = find_peaks(g_mag, height=np.mean(g_mag) + np.std(g_mag))  # detecting peaks
    steps = len(peaks)
    cadence = steps / (len(acc_data) / 50 / 60)  # steps per minute using a 50 Hz sampling rate
    return steps, cadence

def calculate_statistical_features(data):
    """
    Calculate skewness and kurtosis from data.
    """
    return skew(data), kurtosis(data)

def calculate_harmonics(data):
    """
    Calculate Total Harmonic Distortion (THD) using a periodogram.
    """
    freqs, pxx = periodogram(data)
    fundamental = np.abs(pxx[1])
    harmonics = np.abs(pxx[2:6])
    thd = np.sum(harmonics**2)**0.5 / fundamental
    return thd

def calculate_velocity_and_residual(acc_data, steps):
    """
    Calculate average velocity and residual step length of gait.
    """
    if steps > 0:
        avg_velocity = np.sum(acc_data) / steps  # Simplified version
        residual_step_length = avg_velocity - np.mean(acc_data)
    else:
        avg_velocity, residual_step_length = 0, 0
    return avg_velocity, residual_step_length

def calculate_frequency_ratio(data):
    """
    Calculate the ratio of high to low frequency energy.
    """
    frequencies, power_spectrum = welch(data)
    high_freq_power = np.sum(power_spectrum[frequencies > 1.0])  # Arbitrary cutoff frequency
    low_freq_power = np.sum(power_spectrum[frequencies <= 1.0])
    return high_freq_power / low_freq_power if low_freq_power != 0 else 0

def calculate_band_power(data):
    """
    Calculate band power of the signal.
    """
    _, power_spectrum = welch(data)
    return np.sum(power_spectrum)

def calculate_signal_noise_ratio(data):
    """
    Estimate the signal to noise ratio.
    """
    signal_power = np.mean(data**2)
    noise_power = np.var(data)
    return 10 * np.log10(signal_power / noise_power) if noise_power != 0 else 0

def calculate_features(data):
    """
    Calculate all derived features as specified.
    """
    grouped = data.groupby('window_id')
    derived_features = grouped.apply(lambda df: pd.Series({
        'XY_sway_area': calculate_sway_area(df['gyro_x_smartphone'], df['gyro_y_smartphone']),
        'YZ_sway_area': calculate_sway_area(df['gyro_y_smartphone'], df['gyro_z_smartphone']),
        'XZ_sway_area': calculate_sway_area(df['gyro_x_smartphone'], df['gyro_z_smartphone']),
        'Sway_volume': calculate_sway_volume(df['gyro_x_smartphone'], df['gyro_y_smartphone'], df['gyro_z_smartphone']),
        'Steps': calculate_gait_features(df[['acc_x_smartphone', 'acc_y_smartphone', 'acc_z_smartphone']])[0],
        'Cadence': calculate_gait_features(df[['acc_x_smartphone', 'acc_y_smartphone', 'acc_z_smartphone']])[1],
        'Avg_velocity': calculate_velocity_and_residual(df['acc_z_smartphone'], steps)[0],
        'Residual_step_length': calculate_velocity_and_residual(df['acc_z_smartphone'], steps)[1],
        'Frequency_ratio': calculate_frequency_ratio(df['acc_z_smartphone']),
        'Band_power': calculate_band_power(df['acc_z_smartphone']),
        'Signal_noise_ratio': calculate_signal_noise_ratio(df['acc_z_smartphone']),
        'Skewness': calculate_statistical_features(df['acc_z_smartphone'])[0],
        'Kurtosis': calculate_statistical_features(df['acc_z_smartphone'])[1],
        'Total_harmonic_distortion': calculate_harmonics(df['acc_z_smartphone'])
    }))
    return derived_features.reset_index()

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew
from scipy.signal import find_peaks, periodogram, welch

def compute_mean_and_variance(data):
    """ Compute mean and variance of the data. """
    return np.mean(data), np.var(data)

def calculate_velocity_features(df):
    """ Calculate mean and variance for velocity data (smartwatch). """
    mean_x, var_x = compute_mean_and_variance(df['acc_x_smartwatch'])
    mean_y, var_y = compute_mean_and_variance(df['acc_y_smartwatch'])
    mean_z, var_z = compute_mean_and_variance(df['acc_z_smartwatch'])
    return mean_x, var_x, mean_y, var_y, mean_z, var_z

def calculate_angular_velocity_features(df):
    """ Calculate mean and variance for angular velocity data (smartwatch). """
    mean_yaw, var_yaw = compute_mean_and_variance(df['gyro_z_smartwatch'])
    mean_pitch, var_pitch = compute_mean_and_variance(df['gyro_x_smartwatch'])
    mean_roll, var_roll = compute_mean_and_variance(df['gyro_y_smartwatch'])
    return mean_yaw, var_yaw, mean_pitch, var_pitch, mean_roll, var_roll

def calculate_combined_features(df):
    """ Calculate derived features for both smartwatch and smartphone data comprehensively. """
    steps_smartwatch, cadence_smartwatch = calculate_gait_features(df[['acc_x_smartwatch', 'acc_y_smartwatch', 'acc_z_smartwatch']])
    velocity_mean_x, velocity_var_x, velocity_mean_y, velocity_var_y, velocity_mean_z, velocity_var_z = calculate_velocity_features(df)
    angular_mean_yaw, angular_var_yaw, angular_mean_pitch, angular_var_pitch, angular_mean_roll, angular_var_roll = calculate_angular_velocity_features(df)

    return pd.Series({
        'Steps_smartphone': steps_smartwatch,   # Assuming analogous function for smartphone, modify as needed
        'Cadence_smartphone': cadence_smartwatch,
        'Frequency_ratio': calculate_frequency_ratio(df['acc_z_smartwatch']),
        'Residual_step_length': calculate_velocity_and_residual(df[['acc_x_smartwatch', 'acc_y_smartwatch', 'acc_z_smartwatch']], steps_smartwatch)[1],
        'Velocity_mean_X': velocity_mean_x,
        'Velocity_variance_X': velocity_var_x,
        'Velocity_mean_Y': velocity_mean_y,
        'Velocity_variance_Y': velocity_var_y,
        'Velocity_mean_Z': velocity_mean_z,
        'Velocity_variance_Z': velocity_var_z,
        'Angular_velocity_mean_Yaw': angular_mean_yaw,
        'Angular_velocity_variance_Yaw': angular_var_yaw,
        'Angular_velocity_mean_Pitch': angular_mean_pitch,
        'Angular_velocity_variance_Pitch': angular_var_pitch,
        'Angular_velocity_mean_Roll': angular_mean_roll,
        'Angular_velocity_variance_Roll': angular_var_roll
    })

def calculate_features(data):
    """ Wrapper to apply all combined metric calculations over grouped time windows. """
    return data.groupby('window_id').apply(calculate_combined_features).reset_index()

# This updated function provides a complete set of features from both the smartphone and smartwatch metrics, tailor-made for profound insights into the data.


def calculate_combined_features(df):
    """ Calculate combined derived features for both smartphone and smartwatch data. """
    steps, cadence = calculate_gait_features(df[['acc_x_smartphone', 'acc_y_smartphone', 'acc_z_smartphone']])
    return pd.Series({
        'XY_sway_area_smartphone': calculate_sway_area(df['gyro_x_smartphone'], df['gyro_y_smartphone']),
        'YZ_sway_area_smartphone': calculate_sway_area(df['gyro_y_smartphone'], df['gyro_z_smartphone']),
        'XZ_sway_area_smartphone': calculate_sway_area(df['gyro_x_smartphone'], df['gyro_z_smartphone']),
        'Sway_volume_smartphone': calculate_sway_volume(df['gyro_x_smartphone'], df['gyro_y_smartphone'], df['gyro_z_smartphone']),
        'Steps_smartphone': steps,
        'Cadence_smartphone': cadence,
        'Band_power_smartphone': calculate_band_power(df['acc_z_smartphone']),
        'Signal_noise_ratio_smartphone': calculate_signal_noise_ratio(df['acc_z_smartphone']),
        'Skewness_smartphone': calculate_statistical_features(df['acc_z_smartphone'])[0],
        'Kurtosis_smartphone': calculate_statistical_features(df['acc_z_smartphone'])[1],
        'Total_harmonic_distortion_smartphone': calculate_harmonics(df['acc_z_smartphone']),
        'XY_sway_area_smartwatch': calculate_sway_area(df['gyro_x_smartwatch'], df['gyro_y_smartwatch']),
        'YZ_sway_area_smartwatch': calculate_sway_area(df['gyro_y_smartwatch'], df['gyro_z_smartwatch']),
        'XZ_sway_area_smartwatch': calculate_sway_area(df['gyro_x_smartwatch'], df['gyro_z_smartwatch']),
        'Sway_volume_smartwatch': calculate_sway_volume(df['gyro_x_smartwatch'], df['gyro_y_smartwatch'], df['gyro_z_smartwatch']),
        'Band_power_smartwatch': calculate_band_power(df['acc_z_smartwatch']),
        'Signal_noise_ratio_smartwatch': calculate_signal_noise_ratio(df['acc_z_smartwatch'])
    })

def calculate_features(data):
    """ Apply all derived feature calculations across windowed data. """
    return data.groupby('window_id').apply(calculate_combined_features).reset_index()


def sensor_data_pipeline(raw_data):
    """
    Unified function to run the entire ETL pipeline.
    """
    preprocessed_data = load_and_preprocess_data(raw_data)
    cleaned_data = normalize_and_remove_outliers(preprocessed_data)
    segmented_data = segment_data(cleaned_data)
    features = calculate_features(segmented_data)
    return features
