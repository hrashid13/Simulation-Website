"""
Support services — secondary touchpoints outside the clinical pathway.

Analogous to ParkSim's stores. These do not gate patient flow the way a bed
does; they generate ancillary revenue and feed the satisfaction score.

Each service is driven by a different signal:
    discharges - volume scales with patients leaving the hospital
    encounters - volume scales with every patient who enters
    occupancy  - volume scales with the inpatient census (visitors and staff)
"""

SUPPORT_SERVICES = [
    {
        "key": "pharmacy",
        "operating_hours": 24,
        "name": "Pharmacy",
        "category": "clinical_support",
        "driver": "discharges",
        "transactions_per_driver_unit": 0.85,   # scripts filled per discharge
        "avg_transaction_value": 48.00,
        "max_hourly_throughput": 60,
        "satisfaction_weight": 0.30,
    },
    {
        "key": "registration",
        "operating_hours": 24,
        "name": "Billing / Registration",
        "category": "administrative",
        "driver": "encounters",
        "transactions_per_driver_unit": 1.00,   # everyone gets registered
        "avg_transaction_value": 0.00,          # cost centre, not a revenue line
        "max_hourly_throughput": 45,
        "satisfaction_weight": 0.40,
    },
    {
        "key": "cafeteria",
        "operating_hours": 14,
        "name": "Cafeteria",
        "category": "non_clinical",
        "driver": "occupancy",
        "transactions_per_driver_unit": 0.55,   # visitor and staff meals
        "avg_transaction_value": 11.50,
        "max_hourly_throughput": 120,
        "satisfaction_weight": 0.30,
    },
]

SERVICES_BY_KEY = {s["key"]: s for s in SUPPORT_SERVICES}
SERVICE_KEYS = [s["key"] for s in SUPPORT_SERVICES]

# Per-transaction value noise, matching ParkSim's store model.
TRANSACTION_VALUE_SD_RATIO = 0.25

# ---------------------------------------------------------------------------
# Satisfaction model
#
# Starts at 100 and is docked for the things patients actually notice: waiting,
# being turned away, and queueing at the support desks. Deliberately blunt — it
# is a composite indicator for the report, not a clinical quality measure.
# ---------------------------------------------------------------------------
BASE_SATISFACTION_SCORE = 100.0
SATISFACTION_FLOOR = 0.0

SATISFACTION_PENALTIES = {
    # Points lost per hour of mean ER wait, the dominant term by far.
    "er_wait_per_hour": 6.0,
    # Each diverted patient is a hard service failure.
    "diversion_per_patient": 0.40,
    # Points lost per hour of mean support-service queueing.
    "service_queue_per_hour": 2.5,
    # A complication sours the whole encounter.
    "complication_per_patient": 0.25,
}


def _validate() -> None:
    total = sum(s["satisfaction_weight"] for s in SUPPORT_SERVICES)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"service satisfaction weights sum to {total}, expected 1.0")

    valid_drivers = {"discharges", "encounters", "occupancy"}
    for service in SUPPORT_SERVICES:
        if service["driver"] not in valid_drivers:
            raise ValueError(f"{service['name']}: unknown driver {service['driver']!r}")


_validate()
