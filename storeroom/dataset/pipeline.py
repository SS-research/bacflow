import numpy as np
import pandas as pd
from scipy import signal
from scipy.signal import find_peaks, periodogram, welch
from scipy.stats import kurtosis, skew, chi2


def load_and_preprocess_data(dataframe, fill_method='ffill'):
    """
    Load and preprocess the raw sensor data.
    """
    dataframe.fillna(method=fill_method, inplace=True)
    return dataframe


def normalize_and_remove_outliers(data):
    """
    Normalize sensor data using Z-score and remove the top and bottom 1% of values.
    """
    normalized_data = (data - data.mean()) / data.std()
    lower_bound = normalized_data.quantile(0.01)
    upper_bound = normalized_data.quantile(0.99)
    filtered = normalized_data.where((normalized_data > lower_bound) & (normalized_data < upper_bound))
    return filtered.dropna()


def segment_data(data, window_size_seconds=5):
    """
    Segment data into fixed-size windows based on the timestamp.
    """
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
    start_time = data['timestamp'].min()
    data['seconds_since_start'] = (data['timestamp'] - start_time).dt.total_seconds()
    data['window_id'] = (data['seconds_since_start'] // window_size_seconds).astype(int)
    return data


def calculate_confidence_ellipse_area(x, y, confidence=0.95):
    """
    Calculate the area of the ellipse that encloses the 95% confidence interval
    of the 2D points (x, y). For a bivariate normal distribution, the area is:
      A = π * (chi2.ppf(confidence, 2)) * sqrt(det(Cov))
    """
    data = np.vstack([x, y])
    cov = np.cov(data)
    det_cov = np.linalg.det(cov)
    chi2_val = chi2.ppf(confidence, df=2)
    area = np.pi * chi2_val * np.sqrt(det_cov)
    return area


def calculate_sway_volume(data_x, data_y, data_z, confidence=0.95):
    """
    Calculate the volume of the sphere that encloses 95% of the 3D points.
    """
    points = np.vstack([data_x, data_y, data_z]).T
    center = np.mean(points, axis=0)
    distances = np.linalg.norm(points - center, axis=1)
    r = np.percentile(distances, 95)
    volume = (4/3) * np.pi * (r ** 3)
    return volume


def calculate_gait_features(acc_data, frequency=50):
    """
    Calculate gait features: number of steps and cadence.
    Returns (steps, cadence, peaks).
    """
    # Compute magnitude of accelerometer data (assumed gravity-corrected)
    g_mag = np.sqrt(np.sum(np.square(acc_data), axis=1))
    threshold = np.mean(g_mag) + np.std(g_mag)
    peaks, _ = find_peaks(g_mag, height=threshold)
    steps = len(peaks)
    duration_minutes = (len(acc_data) / frequency) / 60
    cadence = steps / duration_minutes if duration_minutes > 0 else 0
    return steps, cadence, peaks


def calculate_statistical_features(data):
    """
    Compute skewness and kurtosis of the data.
    """
    return skew(data), kurtosis(data)


def calculate_harmonics(data):
    """
    Calculate Total Harmonic Distortion (THD) using a periodogram.
    """
    freqs, pxx = periodogram(data)
    if len(pxx) < 6 or pxx[1] == 0:
        return 0
    fundamental = np.abs(pxx[1])
    harmonics = np.abs(pxx[2:6])
    thd = np.sqrt(np.sum(harmonics**2)) / fundamental
    return thd


def calculate_velocity_and_residual(acc_signal, frequency=50):
    """
    Detrend and integrate a gravity-corrected acceleration signal to obtain a velocity signal,
    then compute the average gait velocity and residual step length from detected steps.
    """
    dt = 1 / frequency
    acc_detrended = signal.detrend(acc_signal)
    velocity = np.cumsum(acc_detrended) * dt

    peaks, _ = find_peaks(acc_signal, height=np.mean(acc_signal) + np.std(acc_signal))
    if len(peaks) < 2:
        return 0, 0  # Not enough steps to compute features

    step_lengths = []
    for i in range(1, len(peaks)):
        start, end = peaks[i-1], peaks[i]
        displacement = np.trapz(velocity[start:end], dx=dt)
        step_lengths.append(displacement)
    avg_step_length = np.mean(step_lengths)
    residual_step_length = np.mean(np.abs(np.array(step_lengths) - avg_step_length))
    total_displacement = np.trapz(velocity, dx=dt)
    total_time = len(acc_signal) * dt
    avg_velocity = total_displacement / total_time if total_time > 0 else 0
    return avg_velocity, residual_step_length


def calculate_step_time_features(acc_signal, frequency=50):
    """
    Calculate average step time and residual step time from the accelerometer signal.
    """
    dt = 1 / frequency
    peaks, _ = find_peaks(acc_signal, height=np.mean(acc_signal) + np.std(acc_signal))
    if len(peaks) < 2:
        return 0, 0
    step_intervals = np.diff(peaks) * dt
    avg_step_time = np.mean(step_intervals)
    residual_step_time = np.mean(np.abs(step_intervals - avg_step_time))
    return avg_step_time, residual_step_time


def calculate_velocity_features(acc_data, frequency=50):
    """
    Calculate mean and variance for velocity signals obtained from accelerometer data.
    Expects a DataFrame with columns: 'acc_x', 'acc_y', 'acc_z'.
    """
    dt = 1 / frequency
    velocity_x = np.cumsum(acc_data['acc_x'] * dt)
    velocity_y = np.cumsum(acc_data['acc_y'] * dt)
    velocity_z = np.cumsum(acc_data['acc_z'] * dt)
    
    return (np.mean(velocity_x), np.var(velocity_x),
            np.mean(velocity_y), np.var(velocity_y),
            np.mean(velocity_z), np.var(velocity_z))


def calculate_angular_velocity_features(gyro_data, frequency=50):
    """
    Calculate mean and variance for angular velocity signals.
    Expects a DataFrame with columns: 'gyro_x', 'gyro_y', 'gyro_z'.
    """
    dt = 1 / frequency
    angular_velocity_x = np.cumsum(gyro_data['gyro_x'] * dt)
    angular_velocity_y = np.cumsum(gyro_data['gyro_y'] * dt)
    angular_velocity_z = np.cumsum(gyro_data['gyro_z'] * dt)
    
    return (np.mean(angular_velocity_x), np.var(angular_velocity_x),
            np.mean(angular_velocity_y), np.var(angular_velocity_y),
            np.mean(angular_velocity_z), np.var(angular_velocity_z))


def calculate_combined_features(df):
    """
    Calculate all high-level features for both smartphone and smartwatch data.
    """
    # Smartphone features
    smartphone_acc = df[['acc_x_smartphone', 'acc_y_smartphone', 'acc_z_smartphone']].values
    steps, cadence, _ = calculate_gait_features(smartphone_acc, frequency=50)
    avg_velocity, residual_step_length = calculate_velocity_and_residual(df['acc_z_smartphone'].values, frequency=50)
    avg_step_time, residual_step_time = calculate_step_time_features(df['acc_z_smartphone'].values, frequency=50)
    
    smartphone_acc_df = df[['acc_x_smartphone', 'acc_y_smartphone', 'acc_z_smartphone']].copy()
    smartphone_acc_df.columns = ['acc_x', 'acc_y', 'acc_z']
    velocity_feats = calculate_velocity_features(smartphone_acc_df, frequency=50)
    
    XY_sway_area = calculate_confidence_ellipse_area(df['gyro_x_smartphone'], df['gyro_y_smartphone'])
    YZ_sway_area = calculate_confidence_ellipse_area(df['gyro_y_smartphone'], df['gyro_z_smartphone'])
    XZ_sway_area = calculate_confidence_ellipse_area(df['gyro_x_smartphone'], df['gyro_z_smartphone'])
    sway_volume = calculate_sway_volume(df['gyro_x_smartphone'], df['gyro_y_smartphone'], df['gyro_z_smartphone'])
    
    freq_ratio = calculate_frequency_ratio(df['acc_z_smartphone'])
    band_power = calculate_band_power(df['acc_z_smartphone'])
    snr = calculate_signal_noise_ratio(df['acc_z_smartphone'])
    skewness, kurt = calculate_statistical_features(df['acc_z_smartphone'])
    thd = calculate_harmonics(df['acc_z_smartphone'])
    
    # Smartwatch features (accelerometer velocity and gyroscope angular velocity)
    smartwatch_acc = df[['acc_x_smartwatch', 'acc_y_smartwatch', 'acc_z_smartwatch']].copy()
    smartwatch_acc.columns = ['acc_x', 'acc_y', 'acc_z']
    velocity_feats_sw = calculate_velocity_features(smartwatch_acc, frequency=50)
    
    smartwatch_gyro = df[['gyro_x_smartwatch', 'gyro_y_smartwatch', 'gyro_z_smartwatch']].copy()
    smartwatch_gyro.columns = ['gyro_x', 'gyro_y', 'gyro_z']
    angular_velocity_feats = calculate_angular_velocity_features(smartwatch_gyro, frequency=50)
    
    XY_sway_area_sw = calculate_confidence_ellipse_area(df['gyro_x_smartwatch'], df['gyro_y_smartwatch'])
    YZ_sway_area_sw = calculate_confidence_ellipse_area(df['gyro_y_smartwatch'], df['gyro_z_smartwatch'])
    XZ_sway_area_sw = calculate_confidence_ellipse_area(df['gyro_x_smartwatch'], df['gyro_z_smartwatch'])
    sway_volume_sw = calculate_sway_volume(df['gyro_x_smartwatch'], df['gyro_y_smartwatch'], df['gyro_z_smartwatch'])
    
    return pd.Series({
        # Smartphone features
        'steps_smartphone': steps,
        'cadence_smartphone': cadence,
        'avg_velocity_smartphone': avg_velocity,
        'residual_step_length_smartphone': residual_step_length,
        'avg_step_time_smartphone': avg_step_time,
        'residual_step_time_smartphone': residual_step_time,
        'XY_sway_area_smartphone': XY_sway_area,
        'YZ_sway_area_smartphone': YZ_sway_area,
        'XZ_sway_area_smartphone': XZ_sway_area,
        'sway_volume_smartphone': sway_volume,
        'frequency_ratio_smartphone': freq_ratio,
        'band_power_smartphone': band_power,
        'signal_noise_ratio_smartphone': snr,
        'skewness_smartphone': skewness,
        'kurtosis_smartphone': kurt,
        'total_harmonic_distortion_smartphone': thd,
        'velocity_mean_X_smartphone': velocity_feats[0],
        'velocity_variance_X_smartphone': velocity_feats[1],
        'velocity_mean_Y_smartphone': velocity_feats[2],
        'velocity_variance_Y_smartphone': velocity_feats[3],
        'velocity_mean_Z_smartphone': velocity_feats[4],
        'velocity_variance_Z_smartphone': velocity_feats[5],
        # Smartwatch features
        'XY_sway_area_smartwatch': XY_sway_area_sw,
        'YZ_sway_area_smartwatch': YZ_sway_area_sw,
        'XZ_sway_area_smartwatch': XZ_sway_area_sw,
        'sway_volume_smartwatch': sway_volume_sw,
        'velocity_mean_X_smartwatch': velocity_feats_sw[0],
        'velocity_variance_X_smartwatch': velocity_feats_sw[1],
        'velocity_mean_Y_smartwatch': velocity_feats_sw[2],
        'velocity_variance_Y_smartwatch': velocity_feats_sw[3],
        'velocity_mean_Z_smartwatch': velocity_feats_sw[4],
        'velocity_variance_Z_smartwatch': velocity_feats_sw[5],
        'angular_velocity_mean_X_smartwatch': angular_velocity_feats[0],
        'angular_velocity_variance_X_smartwatch': angular_velocity_feats[1],
        'angular_velocity_mean_Y_smartwatch': angular_velocity_feats[2],
        'angular_velocity_variance_Y_smartwatch': angular_velocity_feats[3],
        'angular_velocity_mean_Z_smartwatch': angular_velocity_feats[4],
        'angular_velocity_variance_Z_smartwatch': angular_velocity_feats[5]
    })


def calculate_features(data):
    """
    Apply feature extraction on each window of segmented data.
    """
    return data.groupby('window_id').apply(calculate_combined_features).reset_index()


def sensor_data_pipeline(raw_data):
    """
    Run the complete ETL pipeline: preprocessing, outlier removal, segmentation,
    and feature extraction.
    """
    preprocessed = load_and_preprocess_data(raw_data)
    cleaned = normalize_and_remove_outliers(preprocessed)
    segmented = segment_data(cleaned)
    features = calculate_features(segmented)
    return features
