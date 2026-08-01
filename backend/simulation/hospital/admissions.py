"""
Arrival generation and triage.

Turns a day's event type into a concrete list of patients arriving at each tick,
then assigns each one an ESI level. The engine consumes the plan; it does not
decide who shows up.
"""

import math
import random

from .events import MASS_CASUALTY, MASS_CASUALTY_BURST, shift_severity
from .patients import ARCHETYPES_BY_NAME, PATIENT_ARCHETYPES

# The simulation runs on 15-minute ticks. Hourly ticks made every reported wait
# time a multiple of 60 minutes, which looked obviously synthetic.
TICKS_PER_HOUR = 4
TICKS_PER_DAY = 24 * TICKS_PER_HOUR
MINUTES_PER_TICK = 60 // TICKS_PER_HOUR

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Weekday-equivalent arrival volume before event and weekend effects.
BASE_DAILY_ARRIVALS = (205, 275)

# Relative arrival likelihood by hour of day for unscheduled patients: quiet
# overnight, a late-morning peak, and a second evening bump. Normalised on load,
# so these are weights rather than probabilities.
_RAW_ARRIVAL_CURVE = [
    0.021, 0.017, 0.014, 0.012, 0.011, 0.012,   # 00:00 - 05:00
    0.018, 0.028, 0.042, 0.055, 0.063, 0.066,   # 06:00 - 11:00
    0.064, 0.061, 0.058, 0.056, 0.055, 0.055,   # 12:00 - 17:00
    0.054, 0.052, 0.047, 0.040, 0.033, 0.026,   # 18:00 - 23:00
]
_CURVE_TOTAL = sum(_RAW_ARRIVAL_CURVE)
UNSCHEDULED_ARRIVAL_CURVE = [w / _CURVE_TOTAL for w in _RAW_ARRIVAL_CURVE]

_HOURS = list(range(24))


def get_day_of_week(day_number: int) -> str:
    return DAYS_OF_WEEK[(day_number - 1) % 7]


def is_weekend(day_of_week: str) -> bool:
    return day_of_week in ("Saturday", "Sunday")


def _poisson(lam: float) -> int:
    """Knuth sampler, with a normal approximation once lambda gets large."""
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, int(random.gauss(lam, math.sqrt(lam)) + 0.5))

    target = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= random.random()
        if p <= target:
            return k
        k += 1


def _assign_esi(distribution: dict, severity_shift: float) -> int:
    dist = shift_severity(distribution, severity_shift)
    return random.choices(list(dist), weights=list(dist.values()), k=1)[0]


def _pick_tick(hour: int) -> int:
    return hour * TICKS_PER_HOUR + random.randrange(TICKS_PER_HOUR)


def plan_day_arrivals(day_number: int, event: dict) -> dict:
    """
    Build one day's arrivals.

    Returns {tick_of_day: [arrival, ...]} where each arrival is
    {"archetype": name, "esi": int, "mass_casualty": bool}.

    Weekend effects are applied per archetype rather than to the day total, so
    a Sunday genuinely loses its elective surgery and clinic lists instead of
    redistributing them to walk-ins.
    """
    day_of_week = get_day_of_week(day_number)
    weekend = is_weekend(day_of_week)
    severity_shift = event["severity_shift"]

    base_volume = random.randint(*BASE_DAILY_ARRIVALS) * event["arrival_multiplier"]

    plan: dict[int, list] = {}

    def add(tick: int, archetype_name: str, esi: int, mass_casualty: bool = False) -> None:
        plan.setdefault(tick, []).append({
            "archetype": archetype_name,
            "esi": esi,
            "mass_casualty": mass_casualty,
        })

    for archetype in PATIENT_ARCHETYPES:
        weight = archetype["weight"]
        if weekend:
            weight *= archetype["weekend_multiplier"]

        count = _poisson(base_volume * weight)
        if count <= 0:
            continue

        if archetype["scheduled"]:
            start, end = archetype["arrival_hours"]
            hours = list(range(start, end))
            hour_weights = None
        else:
            hours = _HOURS
            hour_weights = UNSCHEDULED_ARRIVAL_CURVE

        chosen_hours = random.choices(hours, weights=hour_weights, k=count)
        for hour in chosen_hours:
            esi = _assign_esi(archetype["esi_distribution"], severity_shift)
            add(_pick_tick(hour), archetype["name"], esi)

    if event["name"] == MASS_CASUALTY:
        _add_mass_casualty_burst(plan, add)

    return plan


def _add_mass_casualty_burst(plan: dict, add) -> None:
    """
    Drop a burst of high-acuity patients into a single hour, on top of the day's
    normal arrivals. The burst uses its own severity and archetype mix rather
    than the day-level severity shift, which already applied to everyone else.
    """
    burst = MASS_CASUALTY_BURST
    hour = random.randint(*burst["hour_range"])
    count = random.randint(*burst["patient_range"])

    names = list(burst["archetype_weights"])
    weights = [burst["archetype_weights"][n] for n in names]
    esi_dist = burst["esi_distribution"]

    for _ in range(count):
        name = random.choices(names, weights=weights, k=1)[0]
        esi = random.choices(list(esi_dist), weights=list(esi_dist.values()), k=1)[0]
        add(_pick_tick(hour), name, esi, mass_casualty=True)


def build_readmission_arrival(archetype_name: str, severity_shift: float) -> dict:
    """A returning patient, triaged fresh on arrival."""
    archetype = ARCHETYPES_BY_NAME[archetype_name]
    return {
        "archetype": archetype_name,
        "esi": _assign_esi(archetype["esi_distribution"], severity_shift),
        "mass_casualty": False,
    }
