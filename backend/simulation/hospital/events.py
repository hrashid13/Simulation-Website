"""
Daily event types — the exogenous shock generator.

Analogous to ParkSim's weather system: every simulated day is assigned exactly
one event type, which shifts arrival volume, severity mix, or effective
capacity. Unlike weather, some events act on the supply side rather than demand.
"""

import math
import random

from .patients import ARCHETYPES_BY_NAME, ESI_LEVELS

# `severity_shift` tilts the ESI mix. Positive values push the mix toward
# higher ESI numbers (milder cases); negative values toward ESI 1-2 (sicker).
# `capacity_multiplier` scales every department's effective capacity.
EVENT_TYPES = [
    {
        "name": "Normal Day",
        "probability": 0.72,
        "arrival_multiplier": 1.00,
        "severity_shift": 0.0,
        "capacity_multiplier": 1.00,
        "description": "Baseline arrival rate and severity mix.",
    },
    {
        "name": "Seasonal Surge",
        "probability": 0.15,
        "arrival_multiplier": 1.45,
        "severity_shift": 0.60,     # more patients, but on average less sick
        "capacity_multiplier": 1.00,
        "description": "Flu season volume spike weighted toward lower acuity.",
    },
    {
        "name": "Staffing Shortage",
        "probability": 0.10,
        "arrival_multiplier": 1.00,
        "severity_shift": 0.0,
        "capacity_multiplier": 0.72,  # supply-side shock, demand unchanged
        "description": "Reduced effective capacity with unchanged demand.",
    },
    {
        "name": "Mass Casualty",
        "probability": 0.03,
        "arrival_multiplier": 1.15,
        "severity_shift": -1.40,
        "capacity_multiplier": 1.00,
        "description": "A sudden burst of high-acuity arrivals in a single hour.",
    },
]

EVENT_NAMES = [e["name"] for e in EVENT_TYPES]
EVENTS_BY_NAME = {e["name"]: e for e in EVENT_TYPES}

MASS_CASUALTY = "Mass Casualty"

# The burst that defines a mass casualty event: a large group of mostly ESI 1-2
# patients arriving within one hour, on top of that day's normal arrivals.
MASS_CASUALTY_BURST = {
    "patient_range": (25, 60),
    "hour_range": (8, 20),
    "esi_distribution": {1: 0.25, 2: 0.40, 3: 0.25, 4: 0.10},
    # Trauma dominates a mass casualty, but not exclusively.
    "archetype_weights": {
        "Emergency / Trauma": 0.72,
        "Elderly / Comorbid": 0.14,
        "Pediatric": 0.14,
    },
}

_EVENT_WEIGHTS = [e["probability"] for e in EVENT_TYPES]

# Controls how hard `severity_shift` tilts the ESI mix. Each level is scaled by
# exp(shift * (level - 3) * _SEVERITY_TILT) and the result is renormalised, so
# the realised change is milder than the raw multiplier: at the mass casualty
# shift of -1.4 the raw ESI-1 factor is ~4x but the resulting share of the
# cohort roughly doubles.
_SEVERITY_TILT = 0.5


def roll_event() -> dict:
    return random.choices(EVENT_TYPES, weights=_EVENT_WEIGHTS, k=1)[0]


def build_event_schedule(days: int, force_mass_casualty: bool = False) -> list:
    """
    Roll one event per simulated day.

    When `force_mass_casualty` is set and the random schedule produced none, one
    day is overwritten so the user always gets the capacity stress test they
    asked for. Day 1 is avoided when possible so the run has a baseline to
    compare the spike against.
    """
    schedule = [roll_event() for _ in range(days)]

    if force_mass_casualty and not any(e["name"] == MASS_CASUALTY for e in schedule):
        target = random.randrange(1, days) if days > 1 else 0
        schedule[target] = EVENTS_BY_NAME[MASS_CASUALTY]

    return schedule


def shift_severity(distribution: dict, shift: float) -> dict:
    """
    Re-weight an ESI distribution by `shift`, renormalised to sum to 1.

    ESI 3 is the pivot: it is barely affected, while the tails move in opposite
    directions. A positive shift makes a cohort milder, a negative one sicker.
    """
    if not shift:
        return dict(distribution)

    tilted = {
        level: p * math.exp(shift * (level - 3) * _SEVERITY_TILT)
        for level, p in distribution.items()
    }
    total = sum(tilted.values())
    if total <= 0:
        return dict(distribution)

    return {level: p / total for level, p in tilted.items()}


def _validate() -> None:
    total = sum(e["probability"] for e in EVENT_TYPES)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"event probabilities sum to {total}, expected 1.0")

    burst_total = sum(MASS_CASUALTY_BURST["esi_distribution"].values())
    if abs(burst_total - 1.0) > 1e-6:
        raise ValueError(f"mass casualty ESI mix sums to {burst_total}, expected 1.0")

    for level in MASS_CASUALTY_BURST["esi_distribution"]:
        if level not in ESI_LEVELS:
            raise ValueError(f"mass casualty references unknown ESI level {level}")

    archetype_total = sum(MASS_CASUALTY_BURST["archetype_weights"].values())
    if abs(archetype_total - 1.0) > 1e-6:
        raise ValueError(
            f"mass casualty archetype mix sums to {archetype_total}, expected 1.0"
        )

    for name in MASS_CASUALTY_BURST["archetype_weights"]:
        if name not in ARCHETYPES_BY_NAME:
            raise ValueError(f"mass casualty references unknown archetype {name!r}")


_validate()
