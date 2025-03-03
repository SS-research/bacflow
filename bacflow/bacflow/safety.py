import logging

import pandas
from geopy.geocoders import Nominatim

from bacflow.schemas import DriverProfile


_geolocator = Nominatim(user_agent="BACflow")


def get_threshold_by_driver_profile_threshold(
    latitude: float, longitude: float, profile: DriverProfile, mapping: pandas.DataFrame
) -> float | None:
    """driving under the influence (DUI) threshold by location and driver profile"""
    try:
        location = _geolocator.reverse((latitude, longitude), exactly_one=True)
    except Exception as e:
        message = f"Nominatim could not decode the coordinates: {e}"
        logging.warning(message)

        return None
    
    if not location:
        message = f"Nominatim could not find the location"
        logging.warning(message)

        return None

    alpha_2 = location.raw.get("address", {}).get("country_code", "").upper()

    if not alpha_2:
        message = f"ISO alpha-2 country code is not available"
        logging.warning(message)

        return None

    record = mapping[mapping["alpha-2"] == alpha_2]

    if record.empty:
        message = f"No information about the country {alpha_2}"
        logging.warning(message)

        return None

    threshold = record.iloc[0][str(profile)]

    if pandas.isna(threshold):
        return None

    return threshold
