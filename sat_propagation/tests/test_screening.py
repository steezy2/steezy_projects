from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from sgp4.api import jday

from src.screening import load_satellites, screen

START = datetime(2026, 11, 9, tzinfo=timezone.utc)


def omm(norad_id, inclination, mean_anomaly, mean_motion=15.5):
    """GP record shaped like Space-Track's JSON (all values are strings)."""
    return {
        "OBJECT_NAME": f"SAT {norad_id}", "NORAD_CAT_ID": str(norad_id), "OBJECT_ID": "2026-001A",
        "CLASSIFICATION_TYPE": "U", "EPHEMERIS_TYPE": "0", "ELEMENT_SET_NO": "999", "REV_AT_EPOCH": "1",
        "EPOCH": START.strftime("%Y-%m-%dT%H:%M:%S.%f"), "MEAN_MOTION": str(mean_motion),
        "ECCENTRICITY": "0.0001", "INCLINATION": str(inclination), "RA_OF_ASC_NODE": "0",
        "ARG_OF_PERICENTER": "0", "MEAN_ANOMALY": str(mean_anomaly), "BSTAR": "0",
        "MEAN_MOTION_DOT": "0", "MEAN_MOTION_DDOT": "0",
    }


# Two orbits 30 degrees apart in inclination that reach their shared ascending node together
# 2.6 minutes after START, crossing at ~4 km/s (then again every half orbit); a GEO object
# that can never get close.
CATALOG = load_satellites([omm(1, 50, -10), omm(2, 80, -10), omm(3, 0, 0, mean_motion=1.0027)])


def true_minimum(primary, secondary):
    """Brute-force closest approach on a 0.1 s grid around the expected crossing."""
    seconds = np.arange(0, 6 * 60, 0.1)
    jd, fr = np.full_like(seconds, jday(2026, 11, 9, 0, 0, 0)[0]), seconds / 86400
    _, rp, _ = primary.sgp4_array(jd, fr)
    _, rs, _ = secondary.sgp4_array(jd, fr)
    rng = np.linalg.norm(rs - rp, axis=-1)
    return rng.min(), START + timedelta(seconds=float(seconds[rng.argmin()]))


@pytest.mark.parametrize("primary_ids", [[1], [1, 2]])
def test_screen_finds_the_closest_approach_between_coarse_samples(primary_ids):
    primaries = [s for s in CATALOG if s.satnum in primary_ids]
    miss, tca = true_minimum(CATALOG[0], CATALOG[1])

    [conj] = screen(primaries, CATALOG, START, days=0.02, threshold_km=50)

    assert (conj.primary, conj.secondary) == ("SAT 1 (1)", "SAT 2 (2)")
    assert conj.miss_km == pytest.approx(miss, abs=0.05)
    assert abs((conj.tca - tca).total_seconds()) < 0.5
    assert np.hypot(conj.radial_km, np.hypot(conj.in_track_km, conj.cross_track_km)) == pytest.approx(conj.miss_km)
    assert conj.speed_km_s == pytest.approx(4.0, abs=0.2)
    assert conj.tle_age_days == pytest.approx((conj.tca - START).total_seconds() / 86400, abs=1e-6)


def test_screen_ignores_approaches_beyond_the_threshold():
    miss, _ = true_minimum(CATALOG[0], CATALOG[1])
    assert screen(CATALOG[:1], CATALOG, START, days=0.02, threshold_km=miss - 0.01) == []
