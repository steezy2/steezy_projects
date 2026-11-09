"""Conjunction screening: SGP4-propagate primaries against the catalog and refine each close approach."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
from scipy.optimize import brentq
from sgp4 import omm
from sgp4.api import Satrec, SatrecArray, jday

from src.config import ALTITUDE_PAD_KM, COARSE_STEP_S

CHUNK_SAT_STEPS = 1_500_000  # satellite x time samples propagated together: ~70 MB of state


class Satellite(Satrec):
    """Satrec with a display name."""


@dataclass(frozen=True)
class Conjunction:
    """A predicted close approach; offsets are the secondary relative to the primary's RIC frame."""

    primary: str
    secondary: str
    tca: datetime
    miss_km: float
    radial_km: float
    in_track_km: float
    cross_track_km: float
    speed_km_s: float
    tle_age_days: float  # age at TCA of the older of the two element sets


def load_satellites(records):
    """Build Satellites from Space-Track GP OMM records, skipping elements SGP4 rejects."""
    sats = []
    for record in records:
        sat = Satellite()
        omm.initialize(sat, record)
        if sat.error == 0:
            sat.name = f"{record['OBJECT_NAME']} ({record['NORAD_CAT_ID']})"
            sats.append(sat)
    return sats


def screen(primaries, catalog, start, days, threshold_km):
    """Return every approach closer than threshold_km between a primary and another catalog object.

    Covers `days` from `start` (an aware UTC datetime), soonest first. Each pair is reported once,
    including pairs of two primaries.
    """
    jd0, fr0 = jday(start.year, start.month, start.day, start.hour, start.minute,
                    start.second + start.microsecond / 1e6)
    # One step past the window, so an approach in the last partial step still shows a turning range rate.
    minutes = np.arange(0, days * 1440 + 2 * COARSE_STEP_S / 60, COARSE_STEP_S / 60)
    fr = fr0 + minutes / 1440
    jd = np.full_like(fr, jd0)

    pairs = _candidate_pairs(primaries, catalog, threshold_km)
    rp, vp = _propagate(primaries, jd, fr)
    candidates = np.flatnonzero(pairs.any(axis=0))
    chunk = max(1, CHUNK_SAT_STEPS // len(minutes))
    found = []
    for first in range(0, len(candidates), chunk):
        cols = candidates[first:first + chunk]
        rs, vs = _propagate([catalog[c] for c in cols], jd, fr)
        for i, primary in enumerate(primaries):
            keep = pairs[i, cols]
            for j, k in _coarse_minima(rp[i], vp[i], rs[keep], vs[keep], threshold_km):
                secondary = catalog[cols[keep][j]]
                tca = brentq(lambda t: _range_rate(primary, secondary, jd0, fr0, t), minutes[k], minutes[k + 1])
                conj = _conjunction(primary, secondary, jd0, fr0, start, tca)
                if conj.miss_km < threshold_km and tca <= days * 1440:
                    found.append(conj)
    return sorted(found, key=lambda c: c.tca)


def _candidate_pairs(primaries, catalog, threshold_km):
    """(primary, catalog) mask of pairs whose altitude bands overlap, each unordered pair once."""
    ids = np.array([s.satnum for s in catalog])
    perigee = np.array([s.altp for s in catalog])
    apogee = np.array([s.alta for s in catalog])
    is_primary = np.isin(ids, [p.satnum for p in primaries])
    radius_km = primaries[0].radiusearthkm
    return np.array([
        ((np.maximum(p.altp, perigee) - np.minimum(p.alta, apogee)) * radius_km < threshold_km + ALTITUDE_PAD_KM)
        & (~is_primary | (ids > p.satnum))
        for p in primaries
    ])


def _propagate(sats, jd, fr):
    err, r, v = SatrecArray(sats).sgp4(jd, fr)
    r[err != 0] = np.nan  # decayed or diverged: NaN fails every comparison below
    return r, v


def _coarse_minima(rp, vp, rs, vs, threshold_km):
    """(secondary, step) pairs where range bottoms out between steps step and step+1 and could be under threshold."""
    dr, dv = rs - rp, vs - vp
    rng = np.linalg.norm(dr, axis=-1)
    rate = np.einsum("ntk,ntk->nt", dr, dv)
    travel = np.linalg.norm(dv, axis=-1)[:, :-1] * COARSE_STEP_S
    # The relative path between samples is nearly straight, so the true minimum is at most half a
    # step's travel below the nearer sample; a full step leaves margin for curvature.
    reachable = np.minimum(rng[:, :-1], rng[:, 1:]) - travel < threshold_km
    turning = (rate[:, :-1] < 0) & (rate[:, 1:] >= 0)
    return zip(*np.nonzero(turning & reachable))


def _relative_state(primary, secondary, jd0, fr0, minute):
    fr = fr0 + minute / 1440
    _, rp, vp = primary.sgp4(jd0, fr)
    _, rs, vs = secondary.sgp4(jd0, fr)
    return np.array(rp), np.array(vp), np.subtract(rs, rp), np.subtract(vs, vp)


def _range_rate(primary, secondary, jd0, fr0, minute):
    _, _, dr, dv = _relative_state(primary, secondary, jd0, fr0, minute)
    return dr @ dv


def _conjunction(primary, secondary, jd0, fr0, start, minute):
    rp, vp, dr, dv = _relative_state(primary, secondary, jd0, fr0, minute)
    radial = rp / np.linalg.norm(rp)
    cross = np.cross(rp, vp)
    cross /= np.linalg.norm(cross)
    in_track = np.cross(cross, radial)
    tca_jd = jd0 + fr0 + minute / 1440
    return Conjunction(
        primary=primary.name,
        secondary=secondary.name,
        tca=start + timedelta(minutes=minute),
        miss_km=float(np.linalg.norm(dr)),
        radial_km=float(dr @ radial),
        in_track_km=float(dr @ in_track),
        cross_track_km=float(dr @ cross),
        speed_km_s=float(np.linalg.norm(dv)),
        tle_age_days=float(max(tca_jd - s.jdsatepoch - s.jdsatepochF for s in (primary, secondary))),
    )
