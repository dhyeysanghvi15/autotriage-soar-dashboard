from __future__ import annotations

from collections.abc import Callable
from typing import Any

from autotriage.core.models.alert import NormalizationResult
from autotriage.core.normalize.vendor_a import normalize_vendor_a
from autotriage.core.normalize.vendor_b import normalize_vendor_b
from autotriage.core.normalize.vendor_c import normalize_vendor_c

Normalizer = Callable[[dict[str, Any]], NormalizationResult]


def detect_vendor(payload: dict[str, Any]) -> str:
    if payload.get("vendor") == "vendor_a":
        return "vendor_a"
    if payload.get("source") == "vendor_b":
        return "vendor_b"
    if payload.get("vendor") == "vendor_c":
        return "vendor_c"
    if "event" in payload and "entities" in payload:
        return "vendor_b"
    if "finding" in payload:
        return "vendor_c"
    return "vendor_a"


def get_normalizer(vendor: str) -> Normalizer:
    return {
        "vendor_a": normalize_vendor_a,
        "vendor_b": normalize_vendor_b,
        "vendor_c": normalize_vendor_c,
    }.get(vendor, normalize_vendor_a)


def normalize(payload: dict[str, Any]) -> NormalizationResult:
    vendor = detect_vendor(payload)
    return get_normalizer(vendor)(payload)
