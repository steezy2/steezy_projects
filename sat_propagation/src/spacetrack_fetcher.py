# src/spacetrack_fetcher.py

import requests
from src.config import SPACE_TRACK_URL, SPACE_TRACK_USER, SPACE_TRACK_PASSWORD

def get_spacetrack_data(norad_ids):
    """Fetches TLE data from space-track.org for a list of NORAD IDs."""
    login_url = f"{SPACE_TRACK_URL}/ajaxauth/login"
    query_url = f"{SPACE_TRACK_URL}/basicspacedata/query/class/gp/NORAD_CAT_ID/{','.join(map(str, norad_ids))}/orderby/ORDINAL asc/format/3le"

    with requests.Session() as session:
        # Login to space-track.org
        login_data = {"identity": SPACE_TRACK_USER, "password": SPACE_TRACK_PASSWORD}
        resp = session.post(login_url, data=login_data)
        if resp.status_code != 200:
            raise Exception(f"Failed to login to space-track.org: {resp.text}")

        # Fetch TLE data
        resp = session.get(query_url)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch TLE data: {resp.text}")

        return resp.text
