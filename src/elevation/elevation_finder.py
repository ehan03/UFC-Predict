# standard library imports
import json
import os
import sqlite3
import time
from typing import Dict, List, Tuple

# third party imports
import pandas as pd
import requests
from geopy.geocoders import Nominatim

# local imports
from src.databases.create_statements import CREATE_LOCATION_ELEVATIONS_TABLE
from src.databases.elevation_queries import (
    COMPLETED_EVENT_LOCATIONS_QUERY,
    UPCOMING_EVENT_LOCATIONS_QUERY,
)


class ElevationFinder:
    """
    Class for finding elevation of event locations
    """

    def __init__(self, location_type: str):
        """
        Initialize ElevationFinder class
        """

        assert location_type in ["completed", "upcoming"]
        self.location_type = location_type
        self.conn = sqlite3.connect(
            os.path.join("..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_LOCATION_ELEVATIONS_TABLE)

    def get_lat_long(self, location: str) -> Tuple[float, float]:
        """
        Get latitude, longitude from location string
        """

        geolocator = Nominatim(user_agent="ufcpredict", timeout=30)  # type: ignore
        location_info = geolocator.geocode(location)

        return location_info.latitude, location_info.longitude  # type: ignore

    def get_elevations(self, lat_long_list: List[Tuple[float, float]]) -> List[Dict]:
        """
        Get elevation in meters from list of latitude, longitude pairs
        """

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        locations = []
        for latitude, longitude in lat_long_list:
            location_dict = {"latitude": latitude, "longitude": longitude}
            locations.append(location_dict)
        data = json.dumps({"locations": locations})

        response = requests.post(
            "https://api.open-elevation.com/api/v1/lookup",
            headers=headers,
            data=data,
        ).json()

        return response["results"]

    def __call__(self):
        """
        Get location elevations
        """

        if self.location_type == "completed":
            location_names = self.cur.execute(
                COMPLETED_EVENT_LOCATIONS_QUERY
            ).fetchall()
        else:
            location_names = self.cur.execute(UPCOMING_EVENT_LOCATIONS_QUERY).fetchall()

        lat_long_list = []
        for name in location_names:
            pair = self.get_lat_long(name[0])
            lat_long_list.append(pair)
            time.sleep(1.1)

        if lat_long_list:
            elevations = []
            lat_long_list_chunked = [
                lat_long_list[i : i + 50] for i in range(0, len(lat_long_list), 50)
            ]
            for chunk in lat_long_list_chunked:
                elevations.extend(self.get_elevations(chunk))

            dict_df = []
            for name, elevation_dict in zip(location_names, elevations):
                dict_df.append(
                    {
                        "LOCATION": name[0],
                        "LATITUDE": elevation_dict["latitude"],
                        "LONGITUDE": elevation_dict["longitude"],
                        "ELEVATION_METERS": elevation_dict["elevation"],
                    }
                )

            elevations_df = pd.DataFrame(dict_df)
            elevations_df.to_sql(
                "LOCATION_ELEVATIONS", self.conn, if_exists="append", index=False
            )

        self.conn.commit()
        self.conn.close()
