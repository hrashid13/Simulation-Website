"""
Hospital departments — the constrained resources of the simulation.

Analogous to ParkSim's rides: each department has a fixed capacity, a queue,
and a chance of a daily disruption that reduces effective capacity.

Capacity figures are sized for a mid-size (~250 bed) general hospital.
Costs are loaded hourly rates; revenue is a flat per-encounter estimate
(no payer or insurance modelling — explicitly out of scope for v1).
"""

# Departments a patient can be routed to. `key` is the stable identifier used
# by patient pathways and by the report/export layers; `name` is display only.
DEPARTMENTS = [
    {
        "key": "emergency_room",
        "name": "Emergency Room",
        "unit": "bays",
        "capacity": 30,
        "staff_ratio": 4,               # patients per clinical staff member
        "staff_cost_per_hour": 62.00,   # per staff member, fully loaded
        "cost_per_bed_hour": 95.00,
        "revenue_per_encounter": 1450.00,
        "disruption_probability": 0.06,
        "can_divert": True,
    },
    {
        "key": "radiology_lab",
        "name": "Radiology / Lab",
        "unit": "slots",
        "capacity": 12,
        "staff_ratio": 6,
        "staff_cost_per_hour": 58.00,
        "cost_per_bed_hour": 140.00,    # equipment-heavy
        "revenue_per_encounter": 420.00,
        "disruption_probability": 0.09,  # scanners go down more than beds do
        "can_divert": False,
    },
    {
        "key": "surgery",
        "name": "Surgery",
        "unit": "operating rooms",
        "capacity": 8,
        "staff_ratio": 2,               # surgeon, anaesthesia, scrub team
        "staff_cost_per_hour": 110.00,
        "cost_per_bed_hour": 550.00,    # OR time is the most expensive resource
        "revenue_per_encounter": 12500.00,
        "disruption_probability": 0.05,
        "can_divert": False,
    },
    {
        "key": "icu",
        "name": "ICU",
        "unit": "beds",
        "capacity": 16,
        "staff_ratio": 2,               # near 1:1 nursing
        "staff_cost_per_hour": 78.00,
        "cost_per_bed_hour": 210.00,
        "revenue_per_encounter": 9800.00,
        "disruption_probability": 0.04,
        "can_divert": True,
    },
    {
        "key": "general_ward",
        "name": "General Ward",
        "unit": "beds",
        "capacity": 120,
        "staff_ratio": 6,
        "staff_cost_per_hour": 54.00,
        "cost_per_bed_hour": 55.00,
        "revenue_per_encounter": 2600.00,
        "disruption_probability": 0.05,
        "can_divert": False,
    },
    {
        "key": "outpatient_clinic",
        "name": "Outpatient Clinic",
        "unit": "rooms",
        "capacity": 24,
        "staff_ratio": 8,
        "staff_cost_per_hour": 49.00,
        "cost_per_bed_hour": 40.00,
        "revenue_per_encounter": 280.00,
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
DIVERSION_QUEUE_THRESHOLD = 8

# Patients already waiting are never retroactively diverted; only new arrivals
# are turned away, and only while the diversion condition holds.
