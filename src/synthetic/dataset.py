from datetime import datetime, timedelta

import numpy as np
import pandas as pd


_labelspace = {
    "[0.00]",  # sobriety
    "(0.00-0.05)",  # minimal impairment
    "[0.05-0.08)",  # mild impairment
    "[0.08-0.15)",  # moderate impairment
    "[0.15-0.25)",  # severe impairment
    "[0.25+)"  # life-threatening impairment
}


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
        DataFrame containing synthetic trajectory data with smartphone and smartwatch readings.
    """
    assert label in _labelspace, f"unknown label; should be one of {_labelspace}"

    # Number of samples
    num_samples = duration_seconds * frequency
    
    # Simulate smartphone and smartwatch data
    np.random.seed(participant_key)  # Reproducibility based on participant
    acc_data_smartphone = np.random.normal(loc=0, scale=0.75, size=(num_samples, 3))
    gyro_data_smartphone = np.random.normal(loc=0, scale=0.35, size=(num_samples, 3))
    acc_data_smartwatch = np.random.normal(loc=0, scale=1, size=(num_samples, 3))
    gyro_data_smartwatch = np.random.normal(loc=0, scale=0.5, size=(num_samples, 3))
    
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
    
    # Creating the DataFrame
    trajectory_df = pd.DataFrame({
        'timestamp': timestamps,
        'participant_key': participant_key,
        'trajectory_key': trajectory_key,
        'smartphone_type': smartphone_type,
        'acc_x_smartphone': acc_data_smartphone[:, 0],
        'acc_y_smartphone': acc_data_smartphone[:, 1],
        'acc_z_smartphone': acc_data_smartphone[:, 2],
        'gyro_x_smartphone': gyro_data_smartphone[:, 0],
        'gyro_y_smartphone': gyro_data_smartphone[:, 1],
        'gyro_z_smartphone': gyro_data_smartphone[:, 2],
        'smartwatch_type': smartwatch_type,
        'acc_x_smartwatch': acc_data_smartwatch[:, 0],
        'acc_y_smartwatch': acc_data_smartwatch[:, 1],
        'acc_z_smartwatch': acc_data_smartwatch[:, 2],
        'gyro_x_smartwatch': gyro_data_smartwatch[:, 0],
        'gyro_y_smartwatch': gyro_data_smartwatch[:, 1],
        'gyro_z_smartwatch': gyro_data_smartwatch[:, 2],
        'label': label
    })
    
    return trajectory_df
