"""
frontend/pavement_sync.py
==========================
Keeps the pavement-layer data that both Financial Feasibility (Pavement
Profile) and Soil & Site Conditions edit — included/active, OMC, current
MC, thickness, density, per layer (subgrade/sub-base/base) — in sync in
BOTH directions. This replaces the old one-way "Soil & Site seeds
Financial once" behaviour (still present as a same-run bootstrap fallback
in p7_financial.py's page_financial(), harmless once this module takes
over) with an ongoing sync driven by a snapshot of the last-synced values,
so we can tell which side actually changed since the two were last equal.

sync_pavement_profile() must run once per script execution, BEFORE the
active page's body runs (see app.py's main()) — pushing a value into a
phase's widgets is only safe before that phase's widgets are instantiated
in the same run (see the same constraint documented in p7_financial.py's
_address_lookup()/`_pending_...` handling). Reading from the plain
per-phase input dicts (not the raw widget keys) is what makes pre-routing
positioning still correctly pick up an edit made on the previous run —
a widget's value is only committed to its phase's dict when that phase's
page function runs, which always happens once per edit before the next
run's sync pass.

Only a field that's actually decided to move (financial changed / soil
changed / manual conflict resolve) is ever written to its destination —
NOT a blanket "re-assert the merged state" pass over every field on every
run. That distinction matters: at the point this function runs, the
CURRENTLY ACTIVE page's own plain dict can still be one run stale relative
to a widget the user just committed (Streamlit updates a widget's session
key immediately on submit, before the script reruns — the plain dict only
catches up once that page's body actually executes, later in this same
run). Rewriting an unchanged field's widget key from that stale dict value
would silently clobber the user's own just-typed edit before the page
ever got to read it back.

If both sides have changed since the last sync (a genuine conflict), that
field is left untouched on both sides — see resolve_pavement_conflict(),
wired to the two buttons in Financial Feasibility's Pavement Profile
section.
"""

import streamlit as st

import config as C

_LAYER_NAMES = ("subgrade", "subbase", "base")
_FIELDS = ("included", "omc_pct", "mc_pct", "thickness_m", "density_kg_m3")
_EPS = 1e-9


def _differs(a, b) -> bool:
    if a is None or b is None:
        return a is not b
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) != bool(b)
    return abs(a - b) > _EPS


def _first_category_and_class():
    category = next(iter(C.USCS_SOIL_TABLE))
    uscs_class = next(iter(C.USCS_SOIL_TABLE[category]))
    return category, uscs_class


def _soil_omc_density_widget_keys(name: str, soil_d: dict):
    """Subgrade/sub-base OMC & density widgets are keyed per USCS class
    (see p5_soil_conditions.py._uscs_layer_section) so a previously-entered
    value for one class isn't clobbered by switching to another; base has
    no class, so its keys are plain (base's density is a Measured/Not
    measured field, unlike subgrade/sub-base's). Falls back to the same
    default category/class the page itself would pick on first render, if
    Soil & Site Conditions has never been opened for this layer yet — see
    module docstring."""
    if name == "base":
        return "soil_conditions_base_omc_pct", "v_soil_conditions_base_density_kN_m3"
    category = soil_d.get(f"{name}_category")
    uscs_class = soil_d.get(f"{name}_uscs_class")
    if not category or not uscs_class:
        category, uscs_class = _first_category_and_class()
    suffix = f"__{category}__{uscs_class}"
    return f"soil_conditions_{name}_omc_pct{suffix}", f"soil_conditions_{name}_density_kN_m3{suffix}"


def _financial_values(fin_d: dict, name: str) -> dict:
    D = C.FINANCIAL_DEFAULTS["pavement_layers"][name]
    return {
        "included": bool(fin_d.get(f"layer_{name}_included", D["included"])),
        "omc_pct": fin_d.get(f"layer_{name}_omc_pct", D["omc_pct"]),
        "mc_pct": fin_d.get(f"layer_{name}_mc_pct", D["mc_pct"]),
        "thickness_m": fin_d.get(f"layer_{name}_thickness_m", D["thickness_m"]),
        "density_kg_m3": fin_d.get(f"layer_{name}_density_kg_m3", D["density_kg_m3"]),
    }


def _soil_values(soil_d: dict, name: str) -> dict:
    """In Financial's units (density converted kN/m3 -> kg/m3) so the two
    sides can be compared directly. omc_pct/thickness_m are always present
    once the layer's been rendered (compulsory fields); mc_pct (all
    layers) and density (base only) may be None — genuinely "not
    measured", not a value we can or should push anywhere."""
    density_kN = soil_d.get(f"{name}_density_kN_m3")
    return {
        "included": bool(soil_d.get(f"{name}_active", True)),
        "omc_pct": soil_d.get(f"{name}_omc_pct"),
        "mc_pct": soil_d.get(f"{name}_mc_pct"),
        "thickness_m": soil_d.get(f"{name}_thickness_m"),
        "density_kg_m3": density_kN * C.KN_M3_TO_KG_M3 if density_kN is not None else None,
    }


def _push_field_to_financial(fin_d: dict, name: str, field: str, value):
    key = f"layer_{name}_{field}"
    fin_d[key] = value
    st.session_state[f"financial_{key}"] = value


def _push_field_to_soil(soil_d: dict, name: str, field: str, value):
    if field == "included":
        soil_d[f"{name}_active"] = value
        st.session_state[f"soil_conditions_{name}_active"] = value
    elif field == "thickness_m":
        soil_d[f"{name}_thickness_m"] = value
        st.session_state[f"soil_conditions_{name}_thickness_m"] = value
    elif field == "mc_pct":
        soil_d[f"{name}_mc_pct"] = value
        st.session_state[f"v_soil_conditions_{name}_mc_pct"] = value
        # Otherwise the pushed number sits behind Soil & Site's own "Not
        # measured" toggle and never actually shows.
        st.session_state[f"measured_state_soil_conditions_{name}_mc_pct"] = True
    elif field == "omc_pct":
        soil_d[f"{name}_omc_pct"] = value
        omc_widget_key, _ = _soil_omc_density_widget_keys(name, soil_d)
        st.session_state[omc_widget_key] = value
    elif field == "density_kg_m3":
        density_kN = value / C.KN_M3_TO_KG_M3
        soil_d[f"{name}_density_kN_m3"] = density_kN
        _, density_widget_key = _soil_omc_density_widget_keys(name, soil_d)
        st.session_state[density_widget_key] = density_kN
        if name == "base":
            st.session_state["measured_state_soil_conditions_base_density_kN_m3"] = True


def _push_layer_to_financial(fin_d: dict, name: str, values: dict):
    for field in _FIELDS:
        if values[field] is not None:
            _push_field_to_financial(fin_d, name, field, values[field])


def _push_layer_to_soil(soil_d: dict, name: str, values: dict):
    for field in _FIELDS:
        if values[field] is not None:
            _push_field_to_soil(soil_d, name, field, values[field])


def sync_pavement_profile():
    """Run once per script execution, before the active page's body runs
    (see module docstring for why). Auto-propagates a field's value in
    whichever direction actually changed since the last sync; leaves a
    field untouched (flagged in _pavement_sync_conflicts) if both sides
    changed to different values. A field that hasn't changed on either
    side is never written to — see module docstring on why that matters."""
    fin_d = st.session_state.inputs.setdefault("financial", {})
    soil_d = st.session_state.inputs.setdefault("soil_conditions", {})
    snapshot = st.session_state.setdefault("_pavement_sync_snapshot", {})
    conflicts = set()

    for name in _LAYER_NAMES:
        fin_vals = _financial_values(fin_d, name)
        soil_vals = _soil_values(soil_d, name)
        layer_snapshot = snapshot.setdefault(name, {})
        layer_has_conflict = False

        for field in _FIELDS:
            fin_val, soil_val = fin_vals[field], soil_vals[field]

            if field not in layer_snapshot:
                # No known baseline yet for this field — adopt one
                # silently (preferring Soil & Site, matching the old
                # one-way seed priority) rather than comparing against a
                # missing snapshot, which would otherwise misread
                # Financial's own untouched default as a "change".
                baseline = soil_val if soil_val is not None else fin_val
                layer_snapshot[field] = baseline
                if soil_val is not None and _differs(fin_val, soil_val):
                    _push_field_to_financial(fin_d, name, field, soil_val)
                continue

            snap_val = layer_snapshot[field]
            fin_changed = _differs(fin_val, snap_val)
            soil_changed = soil_val is not None and _differs(soil_val, snap_val)

            if fin_changed and soil_changed:
                if _differs(fin_val, soil_val):
                    layer_has_conflict = True
                else:
                    layer_snapshot[field] = fin_val
            elif fin_changed:
                _push_field_to_soil(soil_d, name, field, fin_val)
                layer_snapshot[field] = fin_val
            elif soil_changed:
                _push_field_to_financial(fin_d, name, field, soil_val)
                layer_snapshot[field] = soil_val
            # else: neither changed since the last sync — leave both sides
            # completely untouched.

        if layer_has_conflict:
            conflicts.add(name)

    st.session_state["_pavement_sync_conflicts"] = conflicts


def conflicting_layers() -> list:
    return sorted(st.session_state.get("_pavement_sync_conflicts", set()))


def has_pavement_conflict() -> bool:
    return bool(st.session_state.get("_pavement_sync_conflicts"))


def resolve_pavement_conflict(keep: str):
    """``keep`` is "financial" or "soil" — that side's current values win
    for every layer (not just the conflicting ones), overwriting the other
    side and clearing every conflict. A full re-sync, not a per-field
    merge, matching the "use these values everywhere" framing of the two
    buttons in Financial Feasibility's Pavement Profile section."""
    fin_d = st.session_state.inputs.setdefault("financial", {})
    soil_d = st.session_state.inputs.setdefault("soil_conditions", {})
    snapshot = st.session_state.setdefault("_pavement_sync_snapshot", {})

    for name in _LAYER_NAMES:
        source = (_financial_values(fin_d, name) if keep == "financial"
                  else _soil_values(soil_d, name))
        _push_layer_to_financial(fin_d, name, source)
        _push_layer_to_soil(soil_d, name, source)
        # Re-read Financial's own values post-push (rather than snapshotting
        # ``source`` directly) — Financial's fields are never None, so this
        # avoids a None from an unmeasured Soil & Site field (e.g. MC)
        # leaking into the snapshot, which would otherwise immediately
        # re-flag Financial's retained (unpushed) value as "changed" next
        # run — see _push_layer_to_financial's None-guard.
        snapshot[name] = _financial_values(fin_d, name)

    st.session_state["_pavement_sync_conflicts"] = set()
