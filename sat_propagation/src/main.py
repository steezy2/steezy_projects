"""Screen satellites against the Space-Track catalog and list Space-Track's own conjunction warnings."""

import argparse
import os
import sys
from datetime import datetime, timezone

import requests

from src.config import SCREENING_DAYS, SCREENING_DISTANCE_KM
from src.screening import load_satellites, screen
from src.spacetrack import SpaceTrack, SpaceTrackError


def main():
    """Run the screening for the NORAD IDs given on the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("norad_ids", type=int, nargs="+", help="NORAD catalog IDs to protect")
    parser.add_argument("--days", type=float, default=SCREENING_DAYS, help="screening window (days)")
    parser.add_argument("--distance", type=float, default=SCREENING_DISTANCE_KM, help="miss distance to report (km)")
    args = parser.parse_args()

    user, password = os.environ.get("SPACETRACK_USER"), os.environ.get("SPACETRACK_PASSWORD")
    if not (user and password):
        sys.exit("Set SPACETRACK_USER and SPACETRACK_PASSWORD to your space-track.org login.")

    try:
        with SpaceTrack(user, password) as space_track:
            catalog = load_satellites(space_track.catalog())
            cdms = space_track.conjunctions(args.norad_ids)
    except (requests.RequestException, SpaceTrackError) as e:
        sys.exit(f"Space-Track request failed: {e}")

    by_id = {sat.satnum: sat for sat in catalog}
    missing = sorted(set(args.norad_ids) - by_id.keys())
    if missing:
        sys.exit(f"Not in the current catalog (decayed or wrong ID): {missing}")
    primaries = [by_id[i] for i in dict.fromkeys(args.norad_ids)]

    print(f"Screening {len(primaries)} satellite(s) against {len(catalog)} objects for {args.days:g} day(s)...")
    conjunctions = screen(primaries, catalog, datetime.now(timezone.utc), args.days, args.distance)

    print(f"\nSGP4 screening, miss < {args.distance:g} km (candidates: TLEs carry no covariance, so no Pc):")
    for c in conjunctions:
        print(f"  {c.tca:%Y-%m-%d %H:%M:%S}Z  {c.primary} vs {c.secondary}\n"
              f"      miss {c.miss_km:.2f} km (R {c.radial_km:+.2f}, I {c.in_track_km:+.2f}, C {c.cross_track_km:+.2f})"
              f"  {c.speed_km_s:.1f} km/s  TLE age {c.tle_age_days:.1f} d")
    if not conjunctions:
        print("  none")

    print("\nSpace-Track conjunction warnings (cdm_public):")
    for cdm in cdms:
        print(f"  {cdm['TCA']}Z  {cdm['SAT_1_NAME']} ({cdm['SAT_1_ID']}) vs {cdm['SAT_2_NAME']} ({cdm['SAT_2_ID']})\n"
              f"      min range {cdm['MIN_RNG']} m  Pc {cdm['PC']}"
              f"{'  EMERGENCY REPORTABLE' if cdm.get('EMERGENCY_REPORTABLE') == 'Y' else ''}")
    if not cdms:
        print("  none")


if __name__ == "__main__":
    main()
