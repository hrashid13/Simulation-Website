"""
Hospital departments — the constrained resources of the simulation.

Analogous to ParkSim's rides: each department has a fixed capacity, a queue,
and a chance of a daily disruption that reduces effective capacity.

Capacity figures are sized for a mid-size general hospital: 261 inpatient
beds (225 ward + 36 ICU) plus 36 ER bays, 8 operating rooms, 10 imaging slots
and 14 clinic rooms.
Costs are loaded hourly rates; revenue is a flat per-encounter estimate
(no payer or insurance modelling — explicitly out of scope for v1).
"""

# Departments a patient can be routed to. `key` is the stable identifier used
# by patient pathways and by the report/export layers; `name` is display only.
DEPARTMENTS = [
    {
        "key": "emergency_room",
        "staffed_hours_per_day": 24,
        "name": "Emergency Room",
        "unit": "bays",
        # Sized so a normal day sits near 72% occupancy. At 28 the department
        # was throughput-saturated every day: extra demand from a surge could
        # only turn into diversions, so average wait stopped tracking load.
        "capacity": 36,
        "staff_ratio": 4,               # patients per clinical staff member
        "staff_cost_per_hour": 62.00,   # per staff member, fully loaded
        "cost_per_bed_hour": 95.00,
        "revenue_per_encounter": 1270.00,
        "disruption_probability": 0.06,
        "can_divert": True,
    },
    {
        "key": "radiology_lab",
        "staffed_hours_per_day": 24,
        "name": "Radiology / Lab",
        "unit": "slots",
        "capacity": 10,
        "staff_ratio": 6,
        "staff_cost_per_hour": 58.00,
        "cost_per_bed_hour": 140.00,    # equipment-heavy
        "revenue_per_encounter": 375.00,
        "disruption_probability": 0.09,  # scanners go down more than beds do
        "can_divert": False,
    },
    {
        "key": "surgery",
        "staffed_hours_per_day": 24,
        "name": "Surgery",
        "unit": "operating rooms",
        # Elective lists are compressed into the daytime window, so OR demand
        # peaks far above its 24-hour average. At 8 rooms with longer cases the
        # department sat at 93% occupancy with a 9-hour wait for a table.
        "capacity": 9,
        "staff_ratio": 2,               # surgeon, anaesthesia, scrub team
        "staff_cost_per_hour": 110.00,
        "cost_per_bed_hour": 550.00,    # OR time is the most expensive resource
        "revenue_per_encounter": 9060.00,
        "disruption_probability": 0.05,
        "can_divert": False,
    },
    {
        "key": "icu",
        "staffed_hours_per_day": 24,
        "name": "ICU",
        "unit": "beds",
        # ICU and ward are sized for queue stability over a full 365-day run, not
        # just a short one. At 22/170 the boarding queues grew without bound:
        # a 30-day run looked fine while 180 days hit 96% occupancy and multi-day
        # waits for a bed.
        "capacity": 36,
        "staff_ratio": 2,               # near 1:1 nursing
        "staff_cost_per_hour": 78.00,
        "cost_per_bed_hour": 245.00,
        "revenue_per_encounter": 7070.00,
        "disruption_probability": 0.04,
        "can_divert": True,
    },
    {
        "key": "general_ward",
        "staffed_hours_per_day": 24,
        "name": "General Ward",
        "unit": "beds",
        "capacity": 225,
        "staff_ratio": 6,
        "staff_cost_per_hour": 54.00,
        "cost_per_bed_hour": 68.00,
        "revenue_per_encounter": 1935.00,
        "disruption_probability": 0.05,
        "can_divert": False,
    },
    {
        "key": "outpatient_clinic",
        "staffed_hours_per_day": 10,
        "name": "Outpatient Clinic",
        "unit": "rooms",
        "capacity": 14,
        "staff_ratio": 8,
        "staff_cost_per_hour": 49.00,
        "cost_per_bed_hour": 40.00,
        "revenue_per_encounter": 232.00,
        "disruption_probability": 0.03,
        "can_divert": False,
    },
]

DEPARTMENTS_BY_KEY = {d["key"]: d for d in DEPARTMENTS}
DEPARTMENT_KEYS = [d["key"] for d in DEPARTMENTS]

# Departments whose queues are worth reporting wait times for. The clinic is
# appointment-driven, so its "wait" is not comparable to an ER wait.
QUEUE_REPORTED_KEYS = [
    "emergency_room",
    "radiology_lab",
    "surgery",
    "icu",
    "general_ward",
]

# ---------------------------------------------------------------------------
# Disruptions — the hospital analog of a ride breakdown.
# Rolled per department per day; reduces effective capacity for a window of
# hours rather than closing the department outright.
# ---------------------------------------------------------------------------
DISRUPTION_TYPES = [
    {
        "name": "Equipment downtime",
        "weight": 0.40,
        "capacity_multiplier": 0.65,
        "duration_hours": (2, 6),
    },
    {
        "name": "Staff callout",
        "weight": 0.45,
        "capacity_multiplier": 0.78,
        "duration_hours": (4, 12),
    },
    {
        "name": "Deep clean / contamination",
        "weight": 0.15,
        "capacity_multiplier": 0.55,
        "duration_hours": (3, 8),
    },
]

# An ER or ICU goes on diversion when it is full and the queue exceeds this
# many waiting patients. Diverted patients leave the system uncared for and are
# counted separately — they are the sharpest signal that capacity was exceeded.
#
# Set high enough that queues (and therefore reported wait times) can genuinely
# grow under load before the release valve opens. A low threshold capped the
# queue so tightly that average ER wait stopped responding to demand at all.
DIVERSION_QUEUE_THRESHOLD = 24

# Diversion only ever applies to lower-acuity arrivals. A real department does
# not turn away a resuscitation or emergent case at the door however full it is,
# and letting it do so also biased the wait statistics: the longest-waiting
# patients were removed from the sample exactly when the hospital was busiest.
DIVERTIBLE_MIN_ESI = 3

# Patients already waiting are never retroactively diverted; only new arrivals
# are turned away, and only while the diversion condition holds.
