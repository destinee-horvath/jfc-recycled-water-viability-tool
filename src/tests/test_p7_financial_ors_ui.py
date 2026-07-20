"""
tests/test_p7_financial_ors_ui.py
===================================
Frontend wiring for the OpenRouteService address-lookup + map feature on
the Financial Feasibility page (frontend/pages/p7_financial.py). Drives the
real Streamlit widget tree headlessly (streamlit.testing.v1.AppTest) with
every ORS HTTP call mocked — no real network access, no API key required
for these tests to pass regardless of the local .env.

Covers:
  * the Compare button stays disabled until BOTH lookups have succeeded,
    and re-uses the stored results rather than calling ORS again;
  * map rendering never crashes when route geometry is missing or
    malformed on either lookup — it degrades to markers-only.
"""

from unittest.mock import patch, MagicMock

from streamlit.testing.v1 import AppTest

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


def _geocode(lng, lat):
    return _mock_response(json_data={"features": [{"geometry": {"coordinates": [lng, lat]}}]})


def _directions(distance_m=42500.0, geometry=REAL_ENCODED_GEOMETRY):
    route = {"summary": {"distance": distance_m, "duration": 2100.0}}
    if geometry is not None:
        route["geometry"] = geometry
    return _mock_response(json_data={"routes": [route]})


def _financial_app():
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    at.button(key="nav_Financial Feasibility").click().run()
    assert not at.exception, at.exception
    return at


def _compare_button(at):
    # Match by key, not label text — the label flips between "Compare both
    # routes" and "Hide comparison" depending on toggle state.
    return next(b for b in at.button if b.key == "financial_ors_compare_btn")


def _run_lookup(at, role, origin_coords, dest_coords, directions_resp):
    with patch("backend.ors_distance.requests.get",
               side_effect=[_geocode(*origin_coords), _geocode(*dest_coords)]), \
         patch("backend.ors_distance.requests.post", return_value=directions_resp):
        at.text_input(key=f"financial_{role}_addr_origin").set_value("Water source address").run()
        at.text_input(key=f"financial_{role}_addr_dest").set_value("Site address").run()
        at.button(key=f"financial_{role}_calc_btn").click().run()
    assert not at.exception, at.exception


# ---------------------------------------------------------------------------
# Compare button gating
# ---------------------------------------------------------------------------
def test_compare_button_disabled_before_any_lookup():
    at = _financial_app()
    assert _compare_button(at).disabled is True


def test_compare_button_still_disabled_after_only_one_lookup():
    at = _financial_app()
    _run_lookup(at, "potable", (152.9, -31.4), (152.8, -31.1), _directions())
    assert _compare_button(at).disabled is True


def test_compare_button_enabled_after_both_lookups_succeed():
    at = _financial_app()
    _run_lookup(at, "potable", (152.9, -31.4), (152.8, -31.1), _directions())
    _run_lookup(at, "recycled", (152.7, -31.5), (152.6, -31.2), _directions())
    assert _compare_button(at).disabled is False


def test_compare_button_toggles_without_any_further_ors_calls():
    """Clicking Compare must render from what's already in session_state —
    no additional requests.get/post calls once both lookups are stored."""
    at = _financial_app()
    _run_lookup(at, "potable", (152.9, -31.4), (152.8, -31.1), _directions())
    _run_lookup(at, "recycled", (152.7, -31.5), (152.6, -31.2), _directions())

    with patch("backend.ors_distance.requests.get") as mock_get, \
         patch("backend.ors_distance.requests.post") as mock_post:
        _compare_button(at).click().run()
    assert not at.exception, at.exception
    mock_get.assert_not_called()
    mock_post.assert_not_called()
    assert at.session_state["_ors_compare"] is True

    # Toggling back off (button label flips to "Hide comparison").
    with patch("backend.ors_distance.requests.get") as mock_get2, \
         patch("backend.ors_distance.requests.post") as mock_post2:
        _compare_button(at).click().run()
    assert not at.exception, at.exception
    mock_get2.assert_not_called()
    mock_post2.assert_not_called()
    assert at.session_state["_ors_compare"] is False


def test_both_routes_stored_independently_in_session_state():
    at = _financial_app()
    _run_lookup(at, "potable", (152.9, -31.4), (152.8, -31.1), _directions(distance_m=10000.0))
    _run_lookup(at, "recycled", (152.7, -31.5), (152.6, -31.2), _directions(distance_m=20000.0))
    assert at.session_state["_ors_route_potable"]["distance_km"] == 10.0
    assert at.session_state["_ors_route_recycled"]["distance_km"] == 20.0


# ---------------------------------------------------------------------------
# Map rendering degrades to markers-only — never crashes — when geometry
# is missing or malformed, on either lookup, independently.
# ---------------------------------------------------------------------------
def test_no_crash_when_potable_geometry_is_malformed():
    at = _financial_app()
    _run_lookup(at, "potable", (152.9, -31.4), (152.8, -31.1),
                _directions(geometry="!!!not-a-valid-polyline!!!"))
    assert not at.exception, at.exception
    assert at.session_state["_ors_route_potable"]["geometry"] == []
    assert at.session_state["_ors_route_potable"]["distance_km"] == 42.5


def test_no_crash_when_recycled_geometry_key_is_missing_entirely():
    at = _financial_app()
    _run_lookup(at, "recycled", (152.7, -31.5), (152.6, -31.2),
                _directions(geometry=None))
    assert not at.exception, at.exception
    assert at.session_state["_ors_route_recycled"]["geometry"] == []
    assert at.session_state["_ors_route_recycled"]["distance_km"] == 42.5


def test_no_crash_when_comparing_one_good_and_one_malformed_route():
    """The core degrade-gracefully case: compare view renders both maps
    together even though only one of the two has usable geometry."""
    at = _financial_app()
    _run_lookup(at, "potable", (152.9, -31.4), (152.8, -31.1), _directions())
    _run_lookup(at, "recycled", (152.7, -31.5), (152.6, -31.2),
                _directions(geometry="garbage"))
    _compare_button(at).click().run()
    assert not at.exception, at.exception
    assert at.session_state["_ors_route_potable"]["geometry"] != []
    assert at.session_state["_ors_route_recycled"]["geometry"] == []


# ---------------------------------------------------------------------------
# Clear error state — no silent failure — when geocoding fails.
# ---------------------------------------------------------------------------
def test_clear_error_shown_when_geocoding_finds_no_match():
    at = _financial_app()
    empty = _mock_response(json_data={"features": []})
    with patch("backend.ors_distance.requests.get", return_value=empty):
        at.text_input(key="financial_potable_addr_origin").set_value("Nowhere").run()
        at.text_input(key="financial_potable_addr_dest").set_value("Nowhere Else").run()
        at.button(key="financial_potable_calc_btn").click().run()
    assert not at.exception, at.exception
    assert any("Could not locate" in (e.value or "") for e in at.error)
    assert "_ors_route_potable" not in at.session_state


def test_manual_distance_entry_still_works_when_ors_lookup_never_run():
    """The manual number_input is always the fallback — untouched by the
    address-lookup feature until a lookup actually succeeds."""
    at = _financial_app()
    at.number_input(key="financial_potable_distance_km").set_value(77.0).run()
    assert not at.exception, at.exception
    assert at.session_state["inputs"]["financial"]["potable_distance_km"] == 77.0
