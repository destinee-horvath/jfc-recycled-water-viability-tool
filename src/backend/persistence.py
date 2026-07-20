"""
backend/persistence.py
=======================
PERSISTENCE — CSV save/load.

For persistent (non-ephemeral) storage, swap the file-based functions below
for a cloud storage bucket or database client — the rest of the application
(models, phases, orchestration, frontend) is unaffected since everything
here goes through the same handful of function signatures.
"""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime
from typing import Any

import config as C


def _ensure_dir():
    os.makedirs(C.SAVE_DIR, exist_ok=True)


def _flatten(inputs: dict[str, dict]) -> dict:
    """Flatten {phase: {k: v}} -> {phase.k: v} for CSV columns."""
    flat = {}
    for pid, vals in inputs.items():
        for k, v in (vals or {}).items():
            if isinstance(v, (list, tuple)):
                v = "|".join(str(x) for x in v)
            flat[f"{pid}.{k}"] = v
    return flat


def _unflatten(flat: dict) -> dict[str, dict]:
    """Reverse of _flatten. List columns are split on '|'."""
    out: dict[str, dict] = {}
    for key, v in flat.items():
        if "." not in key:
            continue
        pid, k = key.split(".", 1)
        out.setdefault(pid, {})[k] = _coerce(v)
    return out


def _coerce(v: Any):
    """Best-effort string -> bool/int/float/list coercion for reloaded CSV."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    if "|" in s:
        return s.split("|")
    low = s.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def build_record(inputs: dict[str, dict], meta: dict) -> dict:
    """One flat dict = one saved assessment (audit trail + inputs). No
    verdict/score — removed; clients only want the per-check readiness
    breakdown (see orchestration.readiness_summary), not a headline verdict."""
    rec = {
        "assessment_name": meta.get("assessment_name", ""),
        "assessed_by": meta.get("assessed_by", ""),
        "saved_at": meta.get("saved_at") or datetime.now().isoformat(timespec="seconds"),
    }
    rec.update(_flatten(inputs))
    return rec


def record_to_csv_bytes(rec: dict) -> bytes:
    """phase/field/value rows — phase.field keys (see _flatten) are split
    into their own columns; meta keys (no dot, e.g. assessment_name) get an
    empty phase."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["phase", "field", "value"])
    for k, v in rec.items():
        phase, field = k.split(".", 1) if "." in k else ("", k)
        w.writerow([phase, field, "" if v is None else v])
    return buf.getvalue().encode("utf-8")


def save_assessment(rec: dict, filename: str) -> str:
    """Write a record to saved_assessments/<filename>.csv. Returns full path."""
    _ensure_dir()
    if not filename.lower().endswith(".csv"):
        filename += ".csv"
    path = os.path.join(C.SAVE_DIR, filename)
    with open(path, "wb") as f:
        f.write(record_to_csv_bytes(rec))
    return path


def list_saved() -> list[str]:
    _ensure_dir()
    return sorted(f for f in os.listdir(C.SAVE_DIR) if f.lower().endswith(".csv"))


def load_assessment_bytes(data: bytes) -> dict:
    """Parse CSV bytes (phase/field/value rows) -> record dict, rejoining
    phase+field into the phase.field keys _unflatten() expects."""
    text = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data
    rec = {}
    r = csv.reader(io.StringIO(text))
    rows = list(r)
    if rows and rows[0][:3] == ["phase", "field", "value"]:
        rows = rows[1:]
    for row in rows:
        if len(row) >= 3:
            phase, field, value = row[0], row[1], row[2]
            rec[f"{phase}.{field}" if phase else field] = value
    return rec


def load_assessment_file(filename: str) -> dict:
    path = os.path.join(C.SAVE_DIR, filename)
    with open(path, "rb") as f:
        return load_assessment_bytes(f.read())


def record_to_inputs(rec: dict) -> tuple[dict[str, dict], dict]:
    """Split a saved record back into (inputs, meta) for repopulating fields.
    Tolerates legacy verdict/score columns from files saved before that
    concept was removed — silently dropped, not surfaced in meta."""
    meta = {
        "assessment_name": rec.get("assessment_name", ""),
        "assessed_by": rec.get("assessed_by", ""),
        "saved_at": rec.get("saved_at", ""),
    }
    flat = {k: v for k, v in rec.items()
            if k not in ("assessment_name", "assessed_by", "saved_at", "verdict", "score")}
    return _unflatten(flat), meta


def suggest_filename(assessment_name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_"
                   for ch in (assessment_name or "assessment")).strip("_")
    return f"{safe}_{datetime.now():%Y-%m-%d}.csv"
