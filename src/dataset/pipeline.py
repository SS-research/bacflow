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


def calculate_features(data):
    """
    Calculate derived features for each window.
    Applied to normalized and cleaned segment data.
    """
    derived_features = data.groupby('window_id').apply(
        lambda df: pd.Series({
            'sway_area': calculate_sway_area(df['gyro_x_smartphone'], df['gyro_y_smartphone']),
            'cadence': calculate_cadence(df['acc_z_smartwatch'], 50)
        })
    )
    return derived_features


def sensor_data_pipeline(raw_data):
    """
    Unified function to run the entire ETL pipeline.
    """
    preprocessed_data = load_and_preprocess_data(raw_data)
    cleaned_data = normalize_and_remove_outliers(preprocessed_data)
    segmented_data = segment_data(cleaned_data)
    features = calculate_features(segmented_data)
    return features
