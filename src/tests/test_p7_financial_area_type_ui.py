"""
tests/test_p7_financial_area_type_ui.py
=========================================
Frontend wiring for the "Average travel speed" area-type selector on the
Financial Feasibility page (frontend/pages/p7_financial.py). Drives the
real Streamlit widget tree headlessly (streamlit.testing.v1.AppTest).

Regression coverage for a reported bug: selecting Urban (dense
city) / Urban / Rural appeared not to update anything. Root cause was that
the number_input's `value=` argument is only honoured the first time a
widget with a given key is created — once `financial_avg_speed_kmh`
already existed in session_state, re-passing a new `value=` on a later
run was silently ignored, so the average-speed field (and everything
downstream of it) never actually changed.
"""

import config as C
from streamlit.testing.v1 import AppTest


def _financial_app():
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()
    at.button(key="nav_Financial Feasibility").click().run()
    assert not at.exception, at.exception
    return at


def _select_area_type(at, area_type):
    at.radio(key="financial_area_type").set_value(area_type).run()
    assert not at.exception, at.exception


def _avg_speed_widget(at):
    return next(n for n in at.number_input if n.key == "financial_avg_speed_kmh")


def _metric_value(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_selecting_each_area_type_updates_the_speed_field():
    at = _financial_app()
    for area_type, expected_speed in C.AREA_TYPE_SPEEDS.items():
        _select_area_type(at, area_type)
        assert _avg_speed_widget(at).value == expected_speed
        assert at.session_state["inputs"]["financial"]["avg_speed_kmh"] == expected_speed


def test_selecting_each_area_type_changes_the_transport_cost_metric():
    """The bug wasn't just cosmetic — a stuck avg_speed_kmh silently
    mispriced the displayed transport cost too."""
    at = _financial_app()
    seen_costs = {}
    for area_type in C.AREA_TYPE_SPEEDS:
        _select_area_type(at, area_type)
        seen_costs[area_type] = _metric_value(at, "Recycled / day")

    assert len(set(seen_costs.values())) == len(seen_costs), (
        f"Expected a distinct transport cost per area type, got {seen_costs}")


def test_manually_edited_speed_is_not_clobbered_by_a_rerun():
    """Only an actual area-type change should reset the speed field —
    an unrelated rerun must not clobber a manually-entered value."""
    at = _financial_app()
    _select_area_type(at, "Rural")
    at.number_input(key="financial_avg_speed_kmh").set_value(77.0).run()
    assert not at.exception, at.exception

    at.number_input(key="financial_num_trucks").set_value(3).run()
    assert _avg_speed_widget(at).value == 77.0
