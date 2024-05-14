import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# g / ml
_labelspace = {
    "[0.00]",  # sobriety
    "(0.00-0.05)",  # minimal impairment
    "[0.05-0.08)",  # mild impairment
    "[0.08-0.15)",  # moderate impairment
    "[0.15-0.25)",  # severe impairment
    "[0.25+)"  # life-threatening impairment
}


def generate_coherent_demographic_features(num_entries):
    """
    Generate coherent demographic features (height, weight, gender) for synthetic data generation
    with gender-specific variations for heights, based on paper statistics.
    """
    genders = np.random.choice(['male', 'female'], num_entries)
    heights = np.zeros(num_entries).astype(int)
    
    for i in range(num_entries):
        if genders[i] == 'male':
            heights[i] = int(np.random.normal(175, 7))
        elif genders[i] == 'female':
            heights[i] = int(np.random.normal(163, 7))
    
    weights = []
    for i in range(num_entries):
        base_weight = 50 + (heights[i] - 150) * 0.5  # Basic weight increases linearly with height.
        if genders[i] == 'male':
            weights.append(int(np.random.normal(base_weight + 10, 10)))
        elif genders[i] == 'female':
            weights.append(int(np.random.normal(base_weight, 10)))

    return heights, weights, genders


def compute_sensor_variance(height, weight):
    """
    Compute sensor variance based on body structure.
    """
    base_variance = 0.5  # Arbitrary base variance
    height_factor = (height - 150) / 50  # Normalize height influence
    weight_factor = (weight - 50) / 50  # Normalize weight influence
    return base_variance * (1 + height_factor + weight_factor)


def generate_synthetic_trajectory_with_devices(participant_key: str, trajectory_key: int, duration_seconds: int, label: str, frequency: int = 50):
    """
    Generates a synthetic dataset resembling sensor data from both a smartphone and a smartwatch during a walking trajectory.
    Parameters:
        participant_key: Unique identifier for the participant.
        trajectory_key: Unique identifier for the trajectory.
        duration_seconds: Duration of the trajectory in seconds.
        label: Label corresponding to BAC level or impairment category.
        frequency: Sampling frequency in Hz.
    Returns:
        Two DataFrames: metadata and time series data.
    """
    assert label in _labelspace, f"unknown label; should be one of {_labelspace}"

    # Number of samples
    num_samples = duration_seconds * frequency
    
    # Generate participant demographics
    heights, weights, genders = generate_coherent_demographic_features(1)
    height = heights[0]
    weight = weights[0]
    gender = genders[0]
    
    # Compute sensor variance
    sensor_variance = compute_sensor_variance(height, weight)
    
    # Simulate smartphone and smartwatch data
    np.random.seed(participant_key)  # Reproducibility based on participant
    acc_data_smartphone = np.random.normal(loc=0, scale=sensor_variance, size=(num_samples, 3))
    gyro_data_smartphone = np.random.normal(loc=0, scale=sensor_variance / 2, size=(num_samples, 3))
    acc_data_smartwatch = np.random.normal(loc=0, scale=sensor_variance * 1.5, size=(num_samples, 3))
    gyro_data_smartwatch = np.random.normal(loc=0, scale=sensor_variance, size=(num_samples, 3))
    
    # Generate timestamps
    start_time = datetime.now()
    timestamps = [start_time + timedelta(seconds=i/frequency) for i in range(num_samples)]
    
    # Choosing two random smartphone and smartwatch models
    device_setup_types = np.random.choice([
        ('Samsung Galaxy S21', 'Samsung Galaxy Watch 3'),
        ('iPhone 12', 'Apple Watch Series 6'),
        ('Google Pixel 5', 'Fitbit Versa 2')
    ])
    smartphone_type = device_setup_types[0]
    smartwatch_type = device_setup_types[1]
    
    # Creating the metadata DataFrame
    metadata_df = pd.DataFrame({
        'participant_key': [participant_key],
        'trajectory_key': [trajectory_key],
        'duration_seconds': [duration_seconds],
        'BAC_range': [label],
        'sampling_frequency': [frequency],
        'smartphone_type': [smartphone_type],
        'smartwatch_type': [smartwatch_type],
        'height': [height],
        'weight': [weight],
        'gender': [gender]
    })
    
    # Creating the time series DataFrame
    timeseries_df = pd.DataFrame({
        'timestamp': timestamps,
        'acc_x_smartphone': acc_data_smartphone[:, 0],
        'acc_y_smartphone': acc_data_smartphone[:, 1],
        'acc_z_smartphone': acc_data_smartphone[:, 2],
        'gyro_x_smartphone': gyro_data_smartphone[:, 0],
        'gyro_y_smartphone': gyro_data_smartphone[:, 1],
        'gyro_z_smartphone': gyro_data_smartphone[:, 2],
        'acc_x_smartwatch': acc_data_smartwatch[:, 0],
        'acc_y_smartwatch': acc_data_smartwatch[:, 1],
        'acc_z_smartwatch': acc_data_smartwatch[:, 2],
        'gyro_x_smartwatch': gyro_data_smartwatch[:, 0],
        'gyro_y_smartwatch': gyro_data_smartwatch[:, 1],
        'gyro_z_smartwatch': gyro_data_smartwatch[:, 2]
    })
    
    return metadata_df, timeseries_df


if __name__ == "__main__":
    metadata_df, timeseries_df = generate_synthetic_trajectory_with_devices(participant_key=1, trajectory_key=1, duration_seconds=60, label="[0.00]", frequency=50)
    print(metadata_df)
    print(timeseries_df)
