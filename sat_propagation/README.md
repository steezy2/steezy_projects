# Satellite conjunction screening

Warns when satellites you care about may pass close to any other tracked object. It does two things:

1. **SGP4 screening.** It downloads the current Space-Track GP catalog (OMM JSON), then propagates your satellites and every object whose altitude band overlaps theirs on a 60 s grid. Each approach is refined to its exact time of closest approach (TCA). For every approach under the screening distance, it reports the TCA, the miss distance split into radial, in-track and cross-track parts, the relative speed and the TLE age.
2. **Space-Track warnings.** It lists upcoming public conjunction data messages (`cdm_public`) for your satellites. These come from the 18th Space Defense Squadron's covariance-based screening and include collision probability (Pc).

TLEs have no covariance. Their positions are about 1 km off at epoch and drift a few km per day, so step 1 finds *candidates*. The CDMs in step 2 are the authoritative warnings, and step 1 is an independent check on them.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt   # macOS/Linux: .venv/bin/python
```

You need a free [space-track.org](https://www.space-track.org) account. Pass the login through environment variables, never in code:

```bash
export SPACETRACK_USER="you@example.com"
export SPACETRACK_PASSWORD="..."
```

## Usage

```bash
python -m src.main 25544 48274 --days 3 --distance 5
```

- `norad_ids`: the satellites to protect.
- `--days`: screening window, 1 by default.
- `--distance`: miss distance to report in km, 5 by default.

Other defaults live in `src/config.py`. The catalog is cached in `cache/` for an hour, because Space-Track asks clients to pull it at most hourly. A day of screening against the full catalog (~30k objects) takes a few seconds.

## Tests

```bash
python -m pytest
```
