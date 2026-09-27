"""Deterministic, synthetic-only SOM preparation for the demo surface.

This module deliberately has no route or operational-data dependency.  A future
verified analytics pipeline can reuse the normalisation/training contract, but
must provide its own licensed input and policy gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import re
from typing import Iterable

import numpy as np


ARTIFACT_VERSION = "synthetic-som-v1"
POLICY_SCENARIO_ID = "synthetic-provider-policy-v1"
GRID_SIZE = 10
TRAINING_SEED = 15_901
FEATURE_NAMES = (
    "carat_weight", "color_grade", "clarity_grade", "system_cut_grade",
    "table_percent", "depth_percent", "crown_angle", "pavilion_angle",
    "permitted_demo_reference_usd_per_carat",
)
BENCHMARK_BAND_KEYS = ("q1", "q2", "q3", "q4")


def median_decimal(values: Iterable[Decimal]) -> Decimal | None:
    """Return an exact Decimal median for a non-empty sequence."""
    ordered = sorted(values)
    if not ordered:
        return None
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / Decimal("2")


def benchmark_quantile_thresholds(values: Iterable[Decimal]) -> tuple[Decimal, Decimal, Decimal] | None:
    """Return deterministic nearest-rank quartile thresholds for cell medians."""
    ordered = sorted(values)
    if not ordered:
        return None
    return tuple(ordered[max(0, int(np.ceil(len(ordered) * fraction)) - 1)] for fraction in (0.25, 0.5, 0.75))


def benchmark_band(value: Decimal | None, thresholds: tuple[Decimal, Decimal, Decimal] | None) -> str | None:
    """Classify a synthetic USD/ct cell summary into a display-only quartile band."""
    if value is None or thresholds is None:
        return None
    for index, threshold in enumerate(thresholds):
        if value <= threshold:
            return BENCHMARK_BAND_KEYS[index]
    return BENCHMARK_BAND_KEYS[-1]


@dataclass(frozen=True)
class SomSourceRow:
    report_id: str
    carat_weight: Decimal
    color_grade: int | None
    clarity_grade: int | None
    system_cut_grade: int | None
    table_percent: Decimal | None
    depth_percent: Decimal | None
    crown_angle: Decimal | None
    pavilion_angle: Decimal | None
    references: dict[str, Decimal]


@dataclass(frozen=True)
class SomPreparedRow:
    source: SomSourceRow
    selected_provider: str
    selected_amount: Decimal
    values: tuple[float, ...]


def _number(report_id: str) -> int:
    match = re.search(r"(\d+)$", report_id)
    if match is None:
        raise ValueError("Synthetic SOM requires numeric DEMO report IDs")
    return int(match.group(1))


def select_permitted_demo_reference(row: SomSourceRow) -> tuple[str, Decimal] | None:
    """Apply the explicit *synthetic* provider-policy scenario.

    It demonstrates the production rule that policy is applied per
    provider-derived feature: Market B is preferred when permitted; Market A
    is an allowed fallback.  On deliberately selected rows both are excluded,
    so the whole vector is excluded rather than silently using a prohibited
    value.  These are fictional conditions, not provider terms.
    """
    number = _number(row.report_id)
    allowed_b = number % 7 != 0
    allowed_a = number % 13 != 0
    if allowed_b and "Demo Market B" in row.references:
        return "Demo Market B", row.references["Demo Market B"]
    if allowed_a and "Demo Market A" in row.references:
        return "Demo Market A", row.references["Demo Market A"]
    return None


def prepare_rows(rows: Iterable[SomSourceRow]) -> tuple[list[SomPreparedRow], int, dict[str, int]]:
    prepared: list[SomPreparedRow] = []
    excluded = 0
    provider_usage = {"Demo Market A": 0, "Demo Market B": 0}
    for row in sorted(rows, key=lambda item: item.report_id):
        selected = select_permitted_demo_reference(row)
        required = (
            row.carat_weight, row.color_grade, row.clarity_grade, row.system_cut_grade,
            row.table_percent, row.depth_percent, row.crown_angle, row.pavilion_angle,
        )
        if selected is None or any(value is None for value in required) or row.carat_weight <= 0:
            excluded += 1
            continue
        provider, amount = selected
        values = (
            float(row.carat_weight), float(row.color_grade), float(row.clarity_grade),
            float(row.system_cut_grade), float(row.table_percent), float(row.depth_percent),
            float(row.crown_angle), float(row.pavilion_angle), float(amount / row.carat_weight),
        )
        provider_usage[provider] += 1
        prepared.append(SomPreparedRow(row, provider, amount, values))
    return prepared, excluded, provider_usage


def train(prepared: list[SomPreparedRow]) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[tuple[int, int, float]]]:
    """Train a small deterministic SOM and return normalisation + assignments."""
    if len(prepared) < 2:
        raise ValueError("Synthetic SOM needs at least two eligible reports")
    values = np.asarray([row.values for row in prepared], dtype=np.float64)
    mean = values.mean(axis=0)
    scale = values.std(axis=0)
    scale[scale == 0] = 1.0
    normalized = (values - mean) / scale
    rng = np.random.default_rng(TRAINING_SEED)
    grid = normalized[rng.choice(len(normalized), size=GRID_SIZE * GRID_SIZE, replace=True)].reshape(
        GRID_SIZE, GRID_SIZE, normalized.shape[1],
    )
    xx, yy = np.meshgrid(np.arange(GRID_SIZE), np.arange(GRID_SIZE), indexing="ij")
    for epoch in range(80):
        progress = epoch / 79
        learning_rate = 0.45 * (1 - progress) + 0.05 * progress
        radius = 4.5 * (1 - progress) + 0.7 * progress
        for index in rng.permutation(len(normalized)):
            vector = normalized[index]
            distances = np.sum((grid - vector) ** 2, axis=2)
            bmu_x, bmu_y = np.unravel_index(np.argmin(distances), distances.shape)
            influence = np.exp(-((xx - bmu_x) ** 2 + (yy - bmu_y) ** 2) / (2 * radius * radius))
            grid += learning_rate * influence[:, :, None] * (vector - grid)
    assignments: list[tuple[int, int, float]] = []
    for vector in normalized:
        distances = np.sqrt(np.sum((grid - vector) ** 2, axis=2))
        x, y = np.unravel_index(np.argmin(distances), distances.shape)
        assignments.append((int(x), int(y), float(distances[x, y])))
    return grid, mean, scale, assignments


def artifact_checksum(*, dataset_sha256: str, prepared: list[SomPreparedRow], assignments: list[tuple[int, int, float]]) -> str:
    payload = {
        "artifact_version": ARTIFACT_VERSION,
        "policy_scenario": POLICY_SCENARIO_ID,
        "seed": TRAINING_SEED,
        "dataset_sha256": dataset_sha256,
        "features": FEATURE_NAMES,
        "rows": [
            [item.source.report_id, item.selected_provider, str(item.selected_amount), assignment[0], assignment[1]]
            for item, assignment in zip(prepared, assignments, strict=True)
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
