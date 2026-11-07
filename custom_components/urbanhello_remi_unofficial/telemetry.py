"""Bounded parsing of optional REMI connection diagnostics.

The dataBundle field is not present on every device. Keys were identified in
P-clean/jeedom-jeeremi; absent or ambiguous values must never become zeroes.
"""
from __future__ import annotations

import math
import re
from typing import Any

TELEMETRY_KEYS = (
    "day_reconnection_count", "day_disconnection_time", "gettime_shift_s",
    "gettime_wayback_max_s", "call_wayback_max_s",
)
_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)")


def parse_connection_telemetry(bundle: Any) -> dict[str, int | float]:
    """Read known numeric keys only, rejecting duplicates and malformed values."""
    if isinstance(bundle, str):
        if len(bundle) > 8192:
            return {}
        values: dict[str, Any] = {}
        duplicates: set[str] = set()
        for token in bundle.split():
            key, separator, value = token.partition(":")
            if not separator or key not in TELEMETRY_KEYS:
                continue
            if key in values:
                duplicates.add(key)
            values[key] = value
        for key in duplicates:
            values.pop(key, None)
    elif isinstance(bundle, dict):
        if len(bundle) > 128:
            return {}
        values = bundle
    else:
        return {}
    result: dict[str, int | float] = {}
    for key in TELEMETRY_KEYS:
        value = values.get(key)
        if isinstance(value, str):
            if len(value) > 24 or not _NUMBER.fullmatch(value):
                continue
            value = float(value)
        if type(value) not in (int, float):
            continue
        try:
            if not math.isfinite(value) or abs(value) > 1_000_000_000:
                continue
        except OverflowError:
            continue
        if key != "gettime_shift_s" and value < 0:
            continue
        if key == "day_reconnection_count" and int(value) != value:
            continue
        result[key] = int(value) if int(value) == value else value
    return result
