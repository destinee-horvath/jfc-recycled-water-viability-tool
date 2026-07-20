"""
backend/ors_distance.py
========================
Optional OpenRouteService integration for Phase Financial's transport
distance inputs — geocodes an address to coordinates, then looks up the
driving distance (and route geometry, for the map display) between two
coordinates.

All three functions degrade to ``None`` on ANY failure (network error,
timeout, non-200 status, or a malformed/unexpected response body) rather
than raising — callers must always have a manual-entry fallback available,
since this is an optional convenience, not a dependency.
"""

from __future__ import annotations

import requests

import config as C


def get_driving_route(origin: dict, destination: dict, api_key: str) -> dict | None:
    """
    Driving distance (km) AND route geometry between two ``{"lat": float,
    "lng": float}`` points, via ONE call to the OpenRouteService Directions
    API — the JSON response already includes an encoded polyline geometry
    at no extra cost, so there's no need for a second request just to draw
    the route on a map.

    Returns ``{"distance_km": float, "geometry": [[lat, lng], ...]}`` on
    success, or ``None`` on any failure. ``geometry`` is ``[]`` (never a
    failure by itself) if the response has no geometry or it fails to
    decode — callers should render markers-only in that case, not crash.
    """
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
    """Encoded polyline (Google algorithm, precision 5 — ORS's default
    directions geometry format) -> [[lat, lng], ...]. Decode failures never
    propagate — a route with a bad/missing geometry still has a valid
    distance, so this returns [] rather than raising."""
    if not encoded:
        return []
    try:
        import polyline
        return [[lat, lng] for lat, lng in polyline.decode(encoded)]
    except Exception:
        return []


def get_driving_distance_km(origin: dict, destination: dict, api_key: str) -> float | None:
    """
    Driving distance (km) between two ``{"lat": float, "lng": float}``
    points, via the OpenRouteService Directions API. Returns ``None`` on
    any failure. Distance-only convenience wrapper around
    ``get_driving_route()`` — kept for callers that don't need geometry.
    """
    route = get_driving_route(origin, destination, api_key)
    return route["distance_km"] if route else None


def geocode_address(address: str, api_key: str) -> dict | None:
    """
    Text address -> ``{"lat": float, "lng": float}`` via the OpenRouteService
    Geocoding API. Returns ``None`` on any failure or if no match is found.
    """
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
