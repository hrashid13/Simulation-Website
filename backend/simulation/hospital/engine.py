"""
Core hospital simulation loop.

Unlike ParkSim, which aggregates each day independently, patients here occupy
beds across day boundaries — an ICU stay can run for five simulated days. The
engine therefore holds real state and advances on 15-minute ticks:

    release finished patients -> route them onward
    admit new arrivals to a queue
    pull from each queue by triage priority while capacity allows
    snapshot occupancy

Everything is in memory and nothing is written to disk; one call in, one result
dict out.
"""

import heapq
import random
from collections import defaultdict

from .admissions import (
    MINUTES_PER_TICK,
    TICKS_PER_DAY,
    TICKS_PER_HOUR,
    build_readmission_arrival,
    get_day_of_week,
    is_weekend,
    plan_day_arrivals,
)
from .departments import (
    DEPARTMENTS,
    DEPARTMENTS_BY_KEY,
    DISRUPTION_TYPES,
    DIVERSION_QUEUE_THRESHOLD,
    DIVERTIBLE_MIN_ESI,
    QUEUE_REPORTED_KEYS,
)
from .events import build_event_schedule
from .patients import (
    ARCHETYPES_BY_NAME,
    COMPLICATION_ICU_DURATION_HOURS,
    COMPLICATION_ICU_ESCALATION_PROBABILITY,
    COMPLICATION_LOS_MULTIPLIER,
    ESI_LEVELS,
    PATIENT_ARCHETYPES,
    READMISSION_DELAY_DAYS,
)
from .services import (
    BASE_SATISFACTION_SCORE,
    SATISFACTION_FLOOR,
    SATISFACTION_PENALTIES,
    SUPPORT_SERVICES,
    TRANSACTION_VALUE_SD_RATIO,
)

# Departments that count as an inpatient admission rather than a visit.
INPATIENT_KEYS = ("icu", "general_ward")

# Complications can escalate a patient from these departments straight to ICU.
ESCALATION_SOURCE_KEYS = ("general_ward", "surgery")

# Above 14 days the hourly occupancy series is tens of thousands of points, too
# large to ship as JSON and unreadable as a chart, so it collapses to per-day.
HOURLY_SERIES_MAX_DAYS = 14

# Support services start backing up once demand passes this share of capacity.
SERVICE_QUEUE_THRESHOLD = 0.85

# The hospital starts completely empty, which is not a state any real hospital is
# ever in. Without a burn-in the opening days are pure warm-up artifact: day 1
# reported 4% ward occupancy against a 79% steady state, and a 7-day run
# understated ward occupancy by 39%. These days are simulated so beds, queues and
# readmissions are already in flight, then discarded before day 1 is recorded.
# 21 days is comfortably past the ~12 days the ICU needs to reach equilibrium.
BURN_IN_DAYS = 21

_DISRUPTION_WEIGHTS = [t["weight"] for t in DISRUPTION_TYPES]


# ---------------------------------------------------------------------------
# Pathway resolution
# ---------------------------------------------------------------------------

def _next_placement(archetype: dict, patient: dict):
    """
    Advance the patient through their pathway until a step actually fires.

    Returns (department_key, duration_hours) or None when the pathway is spent
    and the patient should be discharged.
    """
    pathway = archetype["pathway"]

    while patient["step_index"] < len(pathway):
        step = pathway[patient["step_index"]]
        patient["step_index"] += 1

        if random.random() > step["probability"]:
            continue

        if step["type"] == "branch":
            options = step["options"]
            chosen = random.choices(
                options, weights=[o["weight"] for o in options], k=1
            )[0]
            if chosen["department"] is None:
                continue
            return chosen["department"], random.uniform(*chosen["duration_hours"])

        return step["department"], random.uniform(*step["duration_hours"])

    return None


def _roll_disruptions() -> dict:
    """One optional disruption window per department per day."""
    disruptions = {}
    for dept in DEPARTMENTS:
        if random.random() >= dept["disruption_probability"]:
            continue
        kind = random.choices(DISRUPTION_TYPES, weights=_DISRUPTION_WEIGHTS, k=1)[0]
        duration_hours = random.randint(*kind["duration_hours"])
        start_hour = random.randint(0, 23)
        disruptions[dept["key"]] = {
            "name": kind["name"],
            "capacity_multiplier": kind["capacity_multiplier"],
            "hours": duration_hours,
            "start_tick": start_hour * TICKS_PER_HOUR,
            "end_tick": (start_hour + duration_hours) * TICKS_PER_HOUR,
        }
    return disruptions


def _effective_capacity(dept: dict, event: dict, disruption: dict, tick_of_day: int) -> int:
    capacity = dept["capacity"] * event["capacity_multiplier"]
    if disruption and disruption["start_tick"] <= tick_of_day < disruption["end_tick"]:
        capacity *= disruption["capacity_multiplier"]
    return max(1, int(capacity))


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_simulation(days: int, force_mass_casualty: bool = False) -> dict:
    reported_schedule = build_event_schedule(days, force_mass_casualty)
    # Burn-in gets its own ordinary events; a forced mass casualty must land
    # inside the window the user actually sees.
    event_schedule = build_event_schedule(BURN_IN_DAYS) + reported_schedule

    state = {
        d["key"]: {
            "occupied": 0,
            "intensity_sum": 0.0,
            "queue": [],                       # heap of (esi, queue_tick, seq, patient)
            "releases": defaultdict(list),     # tick -> [patient]
            "effective_capacity": d["capacity"],
        }
        for d in DEPARTMENTS
    }

    def _fresh_totals():
        return {
        d["key"]: {
            "encounters": 0,
            "bed_ticks": 0,
            "occupancy_sum": 0.0,
            "peak_occupancy": 0,
            "wait_sum": 0.0,
            "wait_count": 0,
            "max_wait": 0.0,
            "staff_required_sum": 0.0,
            "disruption_count": 0,
            "disruption_hours": 0,
            "revenue": 0.0,
            "bed_cost": 0.0,
            "staff_cost": 0.0,
        }
        for d in DEPARTMENTS
    }

    def _fresh_esi_totals():
        return {
            level: {"count": 0, "wait_sum": 0.0, "wait_count": 0, "within_target": 0}
            for level in ESI_LEVELS
        }

    totals = _fresh_totals()
    esi_totals = _fresh_esi_totals()
    archetype_totals = {a["name"]: 0 for a in PATIENT_ARCHETYPES}
    service_totals = {
        svc["key"]: {"transactions": 0, "revenue": 0.0, "overflow_hours": 0.0}
        for svc in SUPPORT_SERVICES
    }

    readmission_schedule = defaultdict(list)
    daily_data = []
    disruption_log = []
    occupancy_series = []
    hourly_series = days <= HOURLY_SERIES_MAX_DAYS

    patient_seq = 0
    queue_seq = 0
    total_ticks = days * TICKS_PER_DAY
    total_days = BURN_IN_DAYS + days

    day = 0
    event = event_schedule[0]
    disruptions = {}
    arrival_plan = {}
    day_acc = None

    for tick in range(total_days * TICKS_PER_DAY):
        tick_of_day = tick % TICKS_PER_DAY

        # -- start of day ---------------------------------------------------
        if tick_of_day == 0:
            day += 1
            event = event_schedule[day - 1]

            if day == BURN_IN_DAYS + 1:
                # Beds, queues and pending readmissions carry over; every
                # measurement starts from zero.
                totals = _fresh_totals()
                esi_totals = _fresh_esi_totals()
                for name in archetype_totals:
                    archetype_totals[name] = 0
                for bucket in service_totals.values():
                    bucket.update(transactions=0, revenue=0.0, overflow_hours=0.0)
                daily_data.clear()
                disruption_log.clear()
                occupancy_series.clear()

            disruptions = _roll_disruptions()
            arrival_plan = plan_day_arrivals(day, event)

            for key, disruption in disruptions.items():
                totals[key]["disruption_count"] += 1
                totals[key]["disruption_hours"] += disruption["hours"]
                disruption_log.append({
                    "day": day - BURN_IN_DAYS,
                    "department": DEPARTMENTS_BY_KEY[key]["name"],
                    "type": disruption["name"],
                    "hours": disruption["hours"],
                })

            day_acc = _new_day_accumulator()

            # Readmissions land as fresh arrivals at a random tick.
            for archetype_name in readmission_schedule.pop(day, []):
                arrival = build_readmission_arrival(archetype_name, event["severity_shift"])
                arrival["readmission"] = True
                slot = random.randrange(TICKS_PER_DAY)
                arrival_plan.setdefault(slot, []).append(arrival)

        # -- refresh effective capacity -------------------------------------
        for dept in DEPARTMENTS:
            state[dept["key"]]["effective_capacity"] = _effective_capacity(
                dept, event, disruptions.get(dept["key"]), tick_of_day
            )

        # -- release finished patients --------------------------------------
        for dept in DEPARTMENTS:
            key = dept["key"]
            st = state[key]
            leaving = st["releases"].pop(tick, None)
            if not leaving:
                continue

            for patient in leaving:
                st["occupied"] -= 1
                st["intensity_sum"] -= patient["staff_intensity"]
                archetype = ARCHETYPES_BY_NAME[patient["archetype"]]

                placement = _maybe_escalate(patient, key)
                if placement is None:
                    placement = _next_placement(archetype, patient)

                if placement is None:
                    _discharge(patient, archetype, day, day_acc, readmission_schedule)
                    continue

                day_acc["transfers"] += 1
                _enqueue(state, placement, patient, tick, queue_seq)
                queue_seq += 1

        # -- new arrivals ----------------------------------------------------
        for arrival in arrival_plan.pop(tick_of_day, []):
            archetype = ARCHETYPES_BY_NAME[arrival["archetype"]]
            patient_seq += 1
            patient = _new_patient(patient_seq, arrival, archetype, tick)

            day_acc["arrivals"] += 1
            archetype_totals[patient["archetype"]] += 1
            esi_totals[patient["esi"]]["count"] += 1
            day_acc["esi_counts"][patient["esi"]] += 1
            day_acc["archetype_counts"][patient["archetype"]] += 1
            if patient["complication"]:
                day_acc["complications"] += 1
            if arrival.get("readmission"):
                day_acc["readmissions"] += 1
            if arrival.get("mass_casualty"):
                day_acc["mass_casualty_arrivals"] += 1

            placement = _next_placement(archetype, patient)
            if placement is None:
                _discharge(patient, archetype, day, day_acc, readmission_schedule)
                continue

            target_key = placement[0]
            if _should_divert(state, target_key, patient["esi"]):
                day_acc["diversions"] += 1
                continue

            _enqueue(state, placement, patient, tick, queue_seq)
            queue_seq += 1

        # -- admit from queues ----------------------------------------------
        for dept in DEPARTMENTS:
            key = dept["key"]
            st = state[key]
            queue = st["queue"]

            while queue and st["occupied"] < st["effective_capacity"]:
                _, queued_tick, _, patient = heapq.heappop(queue)

                wait_minutes = (tick - queued_tick) * MINUTES_PER_TICK
                _record_wait(totals[key], esi_totals, day_acc, key, patient, wait_minutes)

                st["occupied"] += 1
                st["intensity_sum"] += patient["staff_intensity"]

                duration_ticks = max(
                    1,
                    round(patient["pending_hours"] * patient["los_multiplier"] * TICKS_PER_HOUR),
                )
                st["releases"][tick + duration_ticks].append(patient)

                totals[key]["encounters"] += 1
                totals[key]["revenue"] += dept["revenue_per_encounter"]
                day_acc["revenue"] += dept["revenue_per_encounter"]
                day_acc["department_encounters"][key] += 1

                if key in INPATIENT_KEYS and not patient["admitted"]:
                    patient["admitted"] = True
                    day_acc["admissions"] += 1

        # -- occupancy snapshot ----------------------------------------------
        inpatient_census = 0
        for dept in DEPARTMENTS:
            key = dept["key"]
            st = state[key]
            occupied = st["occupied"]

            totals[key]["bed_ticks"] += occupied
            totals[key]["occupancy_sum"] += occupied
            totals[key]["staff_required_sum"] += st["intensity_sum"] / dept["staff_ratio"]
            if occupied > totals[key]["peak_occupancy"]:
                totals[key]["peak_occupancy"] = occupied

            day_acc["occupancy_sum"][key] += occupied
            if occupied > day_acc["peak_occupancy"][key]:
                day_acc["peak_occupancy"][key] = occupied

            if key in INPATIENT_KEYS:
                inpatient_census += occupied

        day_acc["census_sum"] += inpatient_census

        if hourly_series and tick_of_day % TICKS_PER_HOUR == 0:
            row = {"day": day - BURN_IN_DAYS, "hour": tick_of_day // TICKS_PER_HOUR}
            for dept in DEPARTMENTS:
                row[dept["key"]] = round(
                    state[dept["key"]]["occupied"] / dept["capacity"] * 100, 1
                )
            occupancy_series.append(row)

        # -- end of day --------------------------------------------------------
        if tick_of_day == TICKS_PER_DAY - 1:
            summary = _close_day(day - BURN_IN_DAYS, event, day_acc, totals, service_totals)
            daily_data.append(summary)

            if not hourly_series:
                # Take the day number off the closed summary, which is already
                # offset for burn-in — using the raw loop counter here left the
                # occupancy series numbered 22..51 for a 30-day run.
                row = {"day": summary["day"]}
                for dept in DEPARTMENTS:
                    row[dept["key"]] = summary["department_occupancy"][dept["key"]]["avg_pct"]
                occupancy_series.append(row)

    return _finalize(
        days=days,
        daily_data=daily_data,
        totals=totals,
        esi_totals=esi_totals,
        archetype_totals=archetype_totals,
        service_totals=service_totals,
        event_schedule=reported_schedule,
        disruption_log=disruption_log,
        occupancy_series=occupancy_series,
        hourly_series=hourly_series,
        total_ticks=total_ticks,
    )


# ---------------------------------------------------------------------------
# Patient lifecycle helpers
# ---------------------------------------------------------------------------

def _new_patient(patient_id: int, arrival: dict, archetype: dict, tick: int) -> dict:
    complication = random.random() < archetype["complication_probability"]
    return {
        "id": patient_id,
        "archetype": archetype["name"],
        "esi": arrival["esi"],
        "step_index": 0,
        "complication": complication,
        "los_multiplier": (
            random.uniform(*COMPLICATION_LOS_MULTIPLIER) if complication else 1.0
        ),
        "icu_escalated": False,
        "admitted": False,
        "staff_intensity": archetype["staff_intensity"],
        "arrival_tick": tick,
        "pending_hours": 0.0,
    }


def _enqueue(state: dict, placement: tuple, patient: dict, tick: int, seq: int) -> None:
    key, hours = placement
    patient["pending_hours"] = hours
    heapq.heappush(state[key]["queue"], (patient["esi"], tick, seq, patient))


def _maybe_escalate(patient: dict, current_key: str):
    """A complication can send an inpatient straight to the ICU, once."""
    if not patient["complication"] or patient["icu_escalated"]:
        return None
    if current_key not in ESCALATION_SOURCE_KEYS:
        return None
    if random.random() >= COMPLICATION_ICU_ESCALATION_PROBABILITY:
        return None

    patient["icu_escalated"] = True
    return "icu", random.uniform(*COMPLICATION_ICU_DURATION_HOURS)


def _should_divert(state: dict, key: str, esi: int) -> bool:
    """
    Only fresh arrivals are turned away, only from divertable units, and never
    the sickest patients — an ESI 1 or 2 is always taken.
    """
    if not DEPARTMENTS_BY_KEY[key]["can_divert"]:
        return False
    if esi < DIVERTIBLE_MIN_ESI:
        return False
    st = state[key]
    return (
        st["occupied"] >= st["effective_capacity"]
        and len(st["queue"]) >= DIVERSION_QUEUE_THRESHOLD
    )


def _discharge(patient, archetype, day, day_acc, readmission_schedule) -> None:
    day_acc["discharges"] += 1
    if random.random() < archetype["readmission_probability"]:
        # Counted at the moment it is scheduled, not when the patient walks back
        # in. Returns land 3-30 days out, so any that fall past the end of the
        # run never arrive — counting arrivals alone would understate the rate
        # badly on short runs (a 30-day run reported 3.1% against a true 7.0%).
        day_acc["readmissions_scheduled"] += 1
        return_day = day + random.randint(*READMISSION_DELAY_DAYS)
        readmission_schedule[return_day].append(patient["archetype"])


def _record_wait(dept_totals, esi_totals, day_acc, key, patient, wait_minutes) -> None:
    dept_totals["wait_sum"] += wait_minutes
    dept_totals["wait_count"] += 1
    if wait_minutes > dept_totals["max_wait"]:
        dept_totals["max_wait"] = wait_minutes

    day_acc["wait_sum"][key] += wait_minutes
    day_acc["wait_count"][key] += 1
    if wait_minutes > day_acc["max_wait"][key]:
        day_acc["max_wait"][key] = wait_minutes

    # Time-to-provider is only meaningful at the front door.
    if key == "emergency_room":
        stats = esi_totals[patient["esi"]]
        stats["wait_sum"] += wait_minutes
        stats["wait_count"] += 1
        if wait_minutes <= ESI_LEVELS[patient["esi"]]["target_wait_minutes"]:
            stats["within_target"] += 1


# ---------------------------------------------------------------------------
# Daily aggregation
# ---------------------------------------------------------------------------

def _new_day_accumulator() -> dict:
    keys = [d["key"] for d in DEPARTMENTS]
    return {
        "arrivals": 0,
        "admissions": 0,
        "discharges": 0,
        "transfers": 0,
        "diversions": 0,
        "complications": 0,
        "readmissions": 0,
        "readmissions_scheduled": 0,
        "mass_casualty_arrivals": 0,
        "revenue": 0.0,
        "census_sum": 0,
        "esi_counts": {level: 0 for level in ESI_LEVELS},
        "archetype_counts": {a["name"]: 0 for a in PATIENT_ARCHETYPES},
        "department_encounters": {k: 0 for k in keys},
        "occupancy_sum": {k: 0 for k in keys},
        "peak_occupancy": {k: 0 for k in keys},
        "wait_sum": {k: 0.0 for k in keys},
        "wait_count": {k: 0 for k in keys},
        "max_wait": {k: 0.0 for k in keys},
    }


def _close_day(day, event, acc, totals, service_totals) -> dict:
    day_of_week = get_day_of_week(day)

    occupancy = {}
    bed_cost = 0.0
    staff_cost = 0.0
    for dept in DEPARTMENTS:
        key = dept["key"]
        avg_occupied = acc["occupancy_sum"][key] / TICKS_PER_DAY
        occupancy[key] = {
            "avg_pct": round(avg_occupied / dept["capacity"] * 100, 1),
            "peak_pct": round(acc["peak_occupancy"][key] / dept["capacity"] * 100, 1),
            "avg_occupied": round(avg_occupied, 1),
            "peak_occupied": acc["peak_occupancy"][key],
        }

        dept_bed_cost = (
            acc["occupancy_sum"][key] / TICKS_PER_HOUR * dept["cost_per_bed_hour"]
        )
        dept_staff_cost = (
            dept["capacity"] / dept["staff_ratio"]
            * dept["staff_cost_per_hour"]
            * dept["staffed_hours_per_day"]
        )
        bed_cost += dept_bed_cost
        staff_cost += dept_staff_cost
        totals[key]["bed_cost"] += dept_bed_cost
        totals[key]["staff_cost"] += dept_staff_cost

    waits = {}
    for key in [d["key"] for d in DEPARTMENTS]:
        count = acc["wait_count"][key]
        waits[key] = {
            "avg_minutes": round(acc["wait_sum"][key] / count, 1) if count else 0.0,
            "max_minutes": round(acc["max_wait"][key], 1),
        }

    service_revenue, overflow = _run_services(acc, service_totals)
    cost = bed_cost + staff_cost
    revenue = acc["revenue"] + service_revenue

    satisfaction = _satisfaction_score(acc, waits, overflow)

    return {
        "day": day,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend(day_of_week),
        "event": event["name"],
        "arrivals": acc["arrivals"],
        "admissions": acc["admissions"],
        "discharges": acc["discharges"],
        "transfers": acc["transfers"],
        "diversions": acc["diversions"],
        "complications": acc["complications"],
        "readmissions": acc["readmissions"],
        "readmissions_scheduled": acc["readmissions_scheduled"],
        "mass_casualty_arrivals": acc["mass_casualty_arrivals"],
        "avg_inpatient_census": round(acc["census_sum"] / TICKS_PER_DAY, 1),
        # Stringified so the payload survives a JSON round-trip unchanged.
        "esi_counts": {str(k): v for k, v in acc["esi_counts"].items()},
        "archetype_counts": dict(acc["archetype_counts"]),
        "department_encounters": dict(acc["department_encounters"]),
        "department_occupancy": occupancy,
        "department_waits": waits,
        "revenue": round(revenue, 2),
        "cost": round(cost, 2),
        "net": round(revenue - cost, 2),
        "satisfaction": satisfaction,
    }


def _run_services(acc, service_totals):
    """Support-service volume is derived from the day's clinical activity."""
    drivers = {
        "discharges": acc["discharges"],
        "encounters": acc["arrivals"],
        "occupancy": acc["census_sum"] / TICKS_PER_DAY,
    }

    total_revenue = 0.0
    overflow = {}

    for service in SUPPORT_SERVICES:
        key = service["key"]
        transactions = int(
            drivers[service["driver"]] * service["transactions_per_driver_unit"]
        )
        capacity = service["max_hourly_throughput"] * service["operating_hours"]
        utilization = transactions / capacity if capacity else 0.0
        overflow_hours = max(0.0, utilization - SERVICE_QUEUE_THRESHOLD) * service["operating_hours"]

        revenue = 0.0
        value = service["avg_transaction_value"]
        if value > 0 and transactions > 0:
            for _ in range(transactions):
                revenue += max(
                    0.5, random.gauss(value, value * TRANSACTION_VALUE_SD_RATIO)
                )

        service_totals[key]["transactions"] += transactions
        service_totals[key]["revenue"] += revenue
        service_totals[key]["overflow_hours"] += overflow_hours

        overflow[key] = overflow_hours
        total_revenue += revenue

    return total_revenue, overflow


def _satisfaction_score(acc, waits, overflow) -> float:
    penalties = SATISFACTION_PENALTIES
    er_wait_hours = waits["emergency_room"]["avg_minutes"] / 60.0

    weighted_overflow = sum(
        overflow[s["key"]] * s["satisfaction_weight"] for s in SUPPORT_SERVICES
    )

    score = (
        BASE_SATISFACTION_SCORE
        - er_wait_hours * penalties["er_wait_per_hour"]
        - acc["diversions"] * penalties["diversion_per_patient"]
        - weighted_overflow * penalties["service_queue_per_hour"]
        - acc["complications"] * penalties["complication_per_patient"]
    )
    return round(max(SATISFACTION_FLOOR, min(BASE_SATISFACTION_SCORE, score)), 1)


# ---------------------------------------------------------------------------
# Final assembly
# ---------------------------------------------------------------------------

def _finalize(days, daily_data, totals, esi_totals, archetype_totals,
              service_totals, event_schedule, disruption_log, occupancy_series,
              hourly_series, total_ticks) -> dict:

    department_stats = {}
    for dept in DEPARTMENTS:
        key = dept["key"]
        t = totals[key]
        staffed_level = dept["capacity"] / dept["staff_ratio"]
        cost = t["bed_cost"] + t["staff_cost"]

        department_stats[key] = {
            "name": dept["name"],
            "unit": dept["unit"],
            "capacity": dept["capacity"],
            "total_encounters": t["encounters"],
            "total_bed_hours": round(t["bed_ticks"] / TICKS_PER_HOUR, 1),
            "avg_occupancy_pct": round(
                t["occupancy_sum"] / total_ticks / dept["capacity"] * 100, 1
            ),
            "peak_occupancy_pct": round(t["peak_occupancy"] / dept["capacity"] * 100, 1),
            "peak_occupied": t["peak_occupancy"],
            "avg_wait_minutes": round(t["wait_sum"] / t["wait_count"], 1) if t["wait_count"] else 0.0,
            "max_wait_minutes": round(t["max_wait"], 1),
            "staff_utilization_pct": round(
                t["staff_required_sum"] / total_ticks / staffed_level * 100, 1
            ),
            "staffed_level": round(staffed_level, 1),
            "disruption_count": t["disruption_count"],
            "disruption_hours": t["disruption_hours"],
            "revenue": round(t["revenue"], 2),
            "cost": round(cost, 2),
            "net_margin": round(t["revenue"] - cost, 2),
            "queue_reported": key in QUEUE_REPORTED_KEYS,
        }

    esi_stats = {}
    total_triaged = sum(s["count"] for s in esi_totals.values()) or 1
    for level, s in esi_totals.items():
        esi_stats[str(level)] = {
            "label": ESI_LEVELS[level]["label"],
            "count": s["count"],
            "share_pct": round(s["count"] / total_triaged * 100, 1),
            "target_wait_minutes": ESI_LEVELS[level]["target_wait_minutes"],
            "avg_er_wait_minutes": round(s["wait_sum"] / s["wait_count"], 1) if s["wait_count"] else 0.0,
            "within_target_pct": round(s["within_target"] / s["wait_count"] * 100, 1) if s["wait_count"] else 0.0,
        }

    service_stats = {}
    for service in SUPPORT_SERVICES:
        key = service["key"]
        s = service_totals[key]
        service_stats[key] = {
            "name": service["name"],
            "category": service["category"],
            "total_transactions": s["transactions"],
            "revenue": round(s["revenue"], 2),
            "overflow_hours": round(s["overflow_hours"], 1),
        }

    total_arrivals = sum(d["arrivals"] for d in daily_data)
    total_discharges = sum(d["discharges"] for d in daily_data)
    total_readmissions = sum(d["readmissions"] for d in daily_data)
    total_readmissions_scheduled = sum(d["readmissions_scheduled"] for d in daily_data)
    total_complications = sum(d["complications"] for d in daily_data)
    total_diversions = sum(d["diversions"] for d in daily_data)
    total_revenue = sum(d["revenue"] for d in daily_data)
    total_cost = sum(d["cost"] for d in daily_data)

    busiest_day = max(daily_data, key=lambda d: d["arrivals"])
    worst_day = max(
        daily_data,
        key=lambda d: (d["department_waits"]["emergency_room"]["avg_minutes"], d["diversions"]),
    )

    event_summary = {}
    for event in event_schedule:
        name = event["name"]
        event_summary.setdefault(name, {"count": 0, "total_arrivals": 0, "total_diversions": 0})
    for day_row in daily_data:
        bucket = event_summary[day_row["event"]]
        bucket["count"] += 1
        bucket["total_arrivals"] += day_row["arrivals"]
        bucket["total_diversions"] += day_row["diversions"]
    for name, bucket in event_summary.items():
        count = bucket["count"] or 1
        bucket["avg_arrivals"] = round(bucket["total_arrivals"] / count, 1)
        bucket["avg_diversions"] = round(bucket["total_diversions"] / count, 2)

    er = department_stats["emergency_room"]

    return {
        "summary": {
            "total_days": days,
            "total_patients": total_arrivals,
            "total_admissions": sum(d["admissions"] for d in daily_data),
            "total_discharges": total_discharges,
            "total_transfers": sum(d["transfers"] for d in daily_data),
            "total_diversions": total_diversions,
            "total_complications": total_complications,
            # Scheduled at discharge; the window-independent clinical measure.
            "total_readmissions": total_readmissions_scheduled,
            "readmission_rate_pct": round(
                total_readmissions_scheduled / total_discharges * 100, 2
            ) if total_discharges else 0.0,
            # Those that actually came back before the run ended. Always lower
            # than the scheduled count, and much lower on short runs.
            "readmissions_returned_in_window": total_readmissions,
            "complication_rate_pct": round(
                total_complications / total_arrivals * 100, 2
            ) if total_arrivals else 0.0,
            "diversion_rate_pct": round(
                total_diversions / total_arrivals * 100, 2
            ) if total_arrivals else 0.0,
            "avg_er_wait_minutes": er["avg_wait_minutes"],
            "max_er_wait_minutes": er["max_wait_minutes"],
            "avg_daily_arrivals": round(total_arrivals / days, 1),
            "avg_satisfaction": round(
                sum(d["satisfaction"] for d in daily_data) / days, 1
            ),
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "net_margin": round(total_revenue - total_cost, 2),
            "net_margin_pct": round(
                (total_revenue - total_cost) / total_revenue * 100, 2
            ) if total_revenue else 0.0,
            "busiest_day": {
                "day": busiest_day["day"],
                "day_of_week": busiest_day["day_of_week"],
                "event": busiest_day["event"],
                "arrivals": busiest_day["arrivals"],
            },
            "worst_day": {
                "day": worst_day["day"],
                "day_of_week": worst_day["day_of_week"],
                "event": worst_day["event"],
                "arrivals": worst_day["arrivals"],
                "avg_er_wait_minutes": worst_day["department_waits"]["emergency_room"]["avg_minutes"],
                "diversions": worst_day["diversions"],
            },
            "archetype_totals": archetype_totals,
            "esi_totals": {str(level): s["count"] for level, s in esi_totals.items()},
            "event_summary": event_summary,
            "occupancy_resolution": "hourly" if hourly_series else "daily",
        },
        "daily_data": daily_data,
        "department_stats": department_stats,
        "service_stats": service_stats,
        "esi_stats": esi_stats,
        "occupancy_series": occupancy_series,
        "event_log": [
            {"day": i + 1, "event": e["name"]} for i, e in enumerate(event_schedule)
        ],
        "disruptions": disruption_log,
    }
