"""
backend/ors_distance.py
========================
Optional OpenRouteService integration: geocodes an address, then looks up
driving distance/route geometry between two coordinates for Phase Financial.

All three functions return ``None`` on any failure rather than raising —
this is an optional convenience, so callers must always have a manual-entry
fallback.
"""

from __future__ import annotations

import requests

import config as C


def get_driving_route(origin: dict, destination: dict, api_key: str) -> dict | None:
    """Driving distance (km) and route geometry between two {"lat","lng"}
    points, via one ORS Directions call (geometry comes free in the same
    response). Returns {"distance_km", "geometry"} or None on failure;
    geometry is [] (not a failure) if it's missing/undecodable — render
    markers-only in that case."""
    try:
        resp = requests.post(
            C.ORS_DIRECTIONS_URL,
            json={"coordinates": [
                [origin["lng"], origin["lat"]],
                [destination["lng"], destination["lat"]],
            ]},
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        route = data["routes"][0]
        metres = route["summary"]["distance"]
        return {
            "distance_km": round(metres / 1000, 2),
            "geometry": _decode_geometry(route.get("geometry")),
        }
    except Exception:
        return None


def _decode_geometry(encoded: str | None) -> list[list[float]]:
    """Encoded polyline (Google algorithm, precision 5) -> [[lat, lng], ...].
    Never raises — a bad/missing geometry shouldn't invalidate the distance."""
    if not encoded:
        return []
    try:
        import polyline
        return [[lat, lng] for lat, lng in polyline.decode(encoded)]
    except Exception:
        return []


def get_driving_distance_km(origin: dict, destination: dict, api_key: str) -> float | None:
    """Distance-only convenience wrapper around get_driving_route(), for
    callers that don't need geometry."""
    route = get_driving_route(origin, destination, api_key)
    return route["distance_km"] if route else None


def geocode_address(address: str, api_key: str) -> dict | None:
    """Text address -> {"lat", "lng"} via the ORS Geocoding API, or None."""
    try:
        resp = requests.get(
            C.ORS_GEOCODE_URL,
            params={"api_key": api_key, "text": address, "size": 1},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        features = data.get("features") or []
        if not features:
            return None
        coords = features[0]["geometry"]["coordinates"]
        return {"lng": coords[0], "lat": coords[1]}
    except Exception:
        return None
