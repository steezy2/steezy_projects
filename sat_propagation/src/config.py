"""Screening defaults and Space-Track settings."""

from pathlib import Path

SPACE_TRACK_URL = "https://www.space-track.org"
REQUEST_TIMEOUT_S = 120  # the full catalog is ~20 MB

# Space-Track asks clients to download the full GP catalog at most once per hour.
CATALOG_CACHE = Path(__file__).resolve().parent.parent / "cache" / "gp_catalog.json"
CATALOG_MAX_AGE_S = 3600

SCREENING_DAYS = 1.0
# TLE positions are ~1 km off at epoch and drift a few km per day, so screen wider than that.
SCREENING_DISTANCE_KM = 5.0
COARSE_STEP_S = 60.0
# Mean-element apogee/perigee differ from the true orbital radius by tens of km.
ALTITUDE_PAD_KM = 50.0
