"""
tests/test_ors_distance.py
============================
Optional OpenRouteService integration: get_driving_route(),
get_driving_distance_km(), and geocode_address() must degrade to None (or,
for route geometry specifically, an empty list) on any failure — bad auth,
malformed response, network error — rather than raising, since this is an
additive convenience alongside the always-available manual distance input.
No real HTTP calls are made — requests.post/get are mocked throughout.
"""

from unittest.mock import patch, MagicMock

from backend.ors_distance import get_driving_distance_km, get_driving_route, geocode_address

ORIGIN = {"lat": -31.4333, "lng": 152.9167}
DESTINATION = {"lat": -31.0833, "lng": 152.8333}

# A real encoded polyline (Google algorithm, precision 5 — ORS's default),
# captured from an actual ORS directions response.
REAL_ENCODED_GEOMETRY = (
    r"nk`_Eaxed\JGz@o@jAeAf@q@jAeB~@aB`AeCZVwAdDcAxAsAbB_CvBg@^}@h@qBz@iA`@w@"
    r"PiAJ}ANI@u@Ba@@_CEqBWiAQ}@WsDoA_AYkB_@eBYwFq@sCa@"
)


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


# ---------------------------------------------------------------------------
# get_driving_distance_km()
# ---------------------------------------------------------------------------
def test_driving_distance_returns_none_on_invalid_api_key():
    with patch("backend.ors_distance.requests.post", return_value=_mock_response(status_code=403)):
        result = get_driving_distance_km(ORIGIN, DESTINATION, "bad-key")
    assert result is None


def test_driving_distance_returns_none_on_malformed_response():
    malformed = _mock_response(status_code=200, json_data={"unexpected": "shape"})
    with patch("backend.ors_distance.requests.post", return_value=malformed):
        result = get_driving_distance_km(ORIGIN, DESTINATION, "good-key")
    assert result is None


def test_driving_distance_returns_correct_float_on_success():
    valid = _mock_response(status_code=200, json_data={
        "routes": [{"summary": {"distance": 42500.0, "duration": 2100.0}}],
    })
    with patch("backend.ors_distance.requests.post", return_value=valid) as mock_post:
        result = get_driving_distance_km(ORIGIN, DESTINATION, "good-key")
    assert result == 42.5
    # Coordinates must be sent as [lng, lat] pairs, origin then destination.
    sent_json = mock_post.call_args.kwargs["json"]
    assert sent_json["coordinates"] == [
        [ORIGIN["lng"], ORIGIN["lat"]],
        [DESTINATION["lng"], DESTINATION["lat"]],
    ]


def test_driving_distance_returns_none_on_request_exception():
    with patch("backend.ors_distance.requests.post", side_effect=ConnectionError("boom")):
        result = get_driving_distance_km(ORIGIN, DESTINATION, "good-key")
    assert result is None


# ---------------------------------------------------------------------------
# get_driving_route() — distance + geometry from ONE call, for the map.
# ---------------------------------------------------------------------------
def test_driving_route_returns_none_on_invalid_api_key():
    with patch("backend.ors_distance.requests.post", return_value=_mock_response(status_code=403)):
        result = get_driving_route(ORIGIN, DESTINATION, "bad-key")
    assert result is None


def test_driving_route_returns_none_on_malformed_response():
    malformed = _mock_response(status_code=200, json_data={"unexpected": "shape"})
    with patch("backend.ors_distance.requests.post", return_value=malformed):
        result = get_driving_route(ORIGIN, DESTINATION, "good-key")
    assert result is None


def test_driving_route_returns_none_on_request_exception():
    with patch("backend.ors_distance.requests.post", side_effect=ConnectionError("boom")):
        result = get_driving_route(ORIGIN, DESTINATION, "good-key")
    assert result is None


def test_driving_route_decodes_geometry_on_success():
    valid = _mock_response(status_code=200, json_data={
        "routes": [{"summary": {"distance": 42500.0, "duration": 2100.0},
                    "geometry": REAL_ENCODED_GEOMETRY}],
    })
    with patch("backend.ors_distance.requests.post", return_value=valid):
        result = get_driving_route(ORIGIN, DESTINATION, "good-key")
    assert result["distance_km"] == 42.5
    assert isinstance(result["geometry"], list)
    assert len(result["geometry"]) > 0
    # Each point is [lat, lng] — folium's expected order.
    lat, lng = result["geometry"][0]
    assert -35 < lat < -30   # sanity: within the right part of NSW
    assert 150 < lng < 155


def test_driving_route_geometry_is_empty_list_when_key_missing():
    """No 'geometry' key in the response at all (older/minimal response
    shape) — distance still resolves; geometry degrades to []."""
    no_geometry = _mock_response(status_code=200, json_data={
        "routes": [{"summary": {"distance": 5000.0, "duration": 300.0}}],
    })
    with patch("backend.ors_distance.requests.post", return_value=no_geometry):
        result = get_driving_route(ORIGIN, DESTINATION, "good-key")
    assert result == {"distance_km": 5.0, "geometry": []}


def test_driving_route_geometry_is_empty_list_when_malformed():
    """A geometry string that isn't valid polyline encoding must not crash
    the whole lookup — distance still resolves; geometry degrades to []."""
    bad_geometry = _mock_response(status_code=200, json_data={
        "routes": [{"summary": {"distance": 5000.0, "duration": 300.0},
                    "geometry": "!!!not-a-valid-polyline!!!"}],
    })
    with patch("backend.ors_distance.requests.post", return_value=bad_geometry):
        result = get_driving_route(ORIGIN, DESTINATION, "good-key")
    assert result["distance_km"] == 5.0
    assert result["geometry"] == []


def test_driving_distance_km_matches_driving_route_distance():
    """The backward-compatible wrapper must agree exactly with the new
    combined function — both hit the same endpoint, same response."""
    valid = _mock_response(status_code=200, json_data={
        "routes": [{"summary": {"distance": 42500.0, "duration": 2100.0},
                    "geometry": REAL_ENCODED_GEOMETRY}],
    })
    with patch("backend.ors_distance.requests.post", return_value=valid):
        distance_only = get_driving_distance_km(ORIGIN, DESTINATION, "good-key")
    with patch("backend.ors_distance.requests.post", return_value=valid):
        route = get_driving_route(ORIGIN, DESTINATION, "good-key")
    assert distance_only == route["distance_km"]


# ---------------------------------------------------------------------------
# geocode_address()
# ---------------------------------------------------------------------------
def test_geocode_returns_none_on_empty_features():
    empty = _mock_response(status_code=200, json_data={"features": []})
    with patch("backend.ors_distance.requests.get", return_value=empty):
        result = geocode_address("a nonexistent place", "good-key")
    assert result is None


def test_geocode_returns_correct_dict_on_success():
    valid = _mock_response(status_code=200, json_data={
        "features": [{"geometry": {"coordinates": [152.9167, -31.4333]}}],
    })
    with patch("backend.ors_distance.requests.get", return_value=valid):
        result = geocode_address("123 Smith St, Port Macquarie NSW", "good-key")
    assert result == {"lng": 152.9167, "lat": -31.4333}


def test_geocode_returns_none_on_non_200_status():
    with patch("backend.ors_distance.requests.get", return_value=_mock_response(status_code=500)):
        result = geocode_address("some address", "good-key")
    assert result is None


def test_geocode_returns_none_on_request_exception():
    with patch("backend.ors_distance.requests.get", side_effect=TimeoutError("boom")):
        result = geocode_address("some address", "good-key")
    assert result is None
