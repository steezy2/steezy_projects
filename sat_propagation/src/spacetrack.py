"""Space-Track.org client: current GP catalog (OMM JSON) and public conjunction data messages."""

import json
import time

import requests

from src.config import CATALOG_CACHE, CATALOG_MAX_AGE_S, REQUEST_TIMEOUT_S, SPACE_TRACK_URL

QUERY_URL = f"{SPACE_TRACK_URL}/basicspacedata/query/class"
# Space-Track's recommended query for the current on-orbit catalog.
CATALOG_QUERY = f"{QUERY_URL}/gp/decay_date/null-val/epoch/>now-30/orderby/norad_cat_id/format/json"


class SpaceTrackError(RuntimeError):
    """Space-Track rejected the request."""


class SpaceTrack:
    """Logged-in Space-Track session, used as a context manager."""

    def __init__(self, user, password, session=None):
        self._credentials = {"identity": user, "password": password}
        self._session = session or requests.Session()

    def __enter__(self):
        resp = self._session.post(
            f"{SPACE_TRACK_URL}/ajaxauth/login", data=self._credentials, timeout=REQUEST_TIMEOUT_S
        )
        resp.raise_for_status()
        # A wrong password still returns HTTP 200, with a "Login Failed" body.
        if "Failed" in resp.text:
            raise SpaceTrackError("login failed: check SPACETRACK_USER and SPACETRACK_PASSWORD")
        return self

    def __exit__(self, *exc):
        self._session.close()

    def catalog(self, cache=CATALOG_CACHE):
        """Return OMM records for every on-orbit object, reusing a cached copy younger than an hour."""
        if cache.exists() and time.time() - cache.stat().st_mtime < CATALOG_MAX_AGE_S:
            return json.loads(cache.read_text())
        records = self._get(CATALOG_QUERY)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(records))
        return records

    def conjunctions(self, norad_ids):
        """Return upcoming public CDMs (cdm_public) involving any of norad_ids, soonest first."""
        ids = ",".join(map(str, norad_ids))
        cdms = {
            cdm["CDM_ID"]: cdm
            for side in ("SAT_1_ID", "SAT_2_ID")
            for cdm in self._get(f"{QUERY_URL}/cdm_public/TCA/>now/{side}/{ids}/format/json")
        }
        return sorted(cdms.values(), key=lambda cdm: cdm["TCA"])

    def _get(self, url):
        resp = self._session.get(url, timeout=REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        body = resp.json()
        # Query errors (rate limits, bad fields) also come back as HTTP 200.
        if isinstance(body, dict) and "error" in body:
            raise SpaceTrackError(body["error"])
        return body
