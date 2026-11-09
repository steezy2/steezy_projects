import json

import pytest

from src.spacetrack import SpaceTrack, SpaceTrackError


class FakeResponse:
    def __init__(self, body):
        self.text = body if isinstance(body, str) else json.dumps(body)

    def raise_for_status(self):
        pass

    def json(self):
        return json.loads(self.text)


class FakeSession:
    """Answers the login POST with login_body and each GET with the first matching canned body."""

    def __init__(self, login_body="", gets=None):
        self.login_body, self.gets, self.urls = login_body, gets or {}, []

    def post(self, url, data, timeout):
        return FakeResponse(self.login_body)

    def get(self, url, timeout):
        self.urls.append(url)
        return FakeResponse(next(body for key, body in self.gets.items() if key in url))

    def close(self):
        pass


def test_login_failure_with_http_200_raises():
    with pytest.raises(SpaceTrackError):
        with SpaceTrack("me", "wrong", FakeSession(login_body='{"Login":"Failed"}')):
            pass


def test_query_error_with_http_200_raises_and_is_not_cached(tmp_path):
    cache = tmp_path / "gp.json"
    session = FakeSession(gets={"class/gp": {"error": "You've violated your query rate limit."}})
    with SpaceTrack("me", "pw", session) as space_track:
        with pytest.raises(SpaceTrackError, match="rate limit"):
            space_track.catalog(cache)
    assert not cache.exists()


def test_catalog_reuses_a_fresh_cache(tmp_path):
    cache = tmp_path / "gp.json"
    session = FakeSession(gets={"class/gp": [{"NORAD_CAT_ID": "1"}]})
    with SpaceTrack("me", "pw", session) as space_track:
        first = space_track.catalog(cache)
        second = space_track.catalog(cache)

    assert first == second == [{"NORAD_CAT_ID": "1"}]
    assert len(session.urls) == 1


def test_conjunctions_merge_both_sides_once_soonest_first():
    shared = {"CDM_ID": "2", "TCA": "2026-11-10T00:00:00"}
    session = FakeSession(gets={
        "SAT_1_ID": [{"CDM_ID": "1", "TCA": "2026-11-11T00:00:00"}, shared],
        "SAT_2_ID": [shared],
    })
    with SpaceTrack("me", "pw", session) as space_track:
        cdms = space_track.conjunctions([25544, 48274])

    assert [c["CDM_ID"] for c in cdms] == ["2", "1"]
    assert all("/25544,48274/" in url for url in session.urls)
