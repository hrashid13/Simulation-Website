"""
Patient archetypes — what arrives at the hospital and where it goes.

Analogous to ParkSim's visitor archetypes: each archetype carries an arrival
weight, a triage severity distribution, a care pathway through the departments,
and probabilities for complications and readmission.

Triage uses the real ESI 1-5 scale (1 = most severe). ESI is strictly an
emergency department instrument; applying it to clinic and elective surgery
arrivals is a deliberate simplification that gives every patient one comparable
severity axis. Expect the hospital-wide mix to look milder than a published ED
mix would, because the clinic and elective cohorts sit at ESI 4-5.
"""

from .departments import DEPARTMENTS_BY_KEY

# ---------------------------------------------------------------------------
# Emergency Severity Index
#
# `target_wait_minutes` is the benchmark time-to-provider for each level. The
# report scores each ESI band against it ("% seen within target"), which is the
# metric an actual ED dashboard leads with.
# ---------------------------------------------------------------------------
ESI_LEVELS = {
    1: {"label": "Resuscitation", "target_wait_minutes": 0,   "priority": 0},
    2: {"label": "Emergent",      "target_wait_minutes": 10,  "priority": 1},
    3: {"label": "Urgent",        "target_wait_minutes": 30,  "priority": 2},
    4: {"label": "Less Urgent",   "target_wait_minutes": 60,  "priority": 3},
    5: {"label": "Non-Urgent",    "target_wait_minutes": 120, "priority": 4},
}

# Pathway step types:
#   visit  - go to `department` with probability `probability`
#   branch - pick exactly one of `options` by weight; a None department means
#            the branch resolves to "no further care at this stage"
#
# Durations are in hours and are sampled uniformly from the given range. The
# engine multiplies them by the patient's complication factor.
PATIENT_ARCHETYPES = [
    {
        "name": "Walk-in / Minor",
        "weight": 0.33,
        "esi_distribution": {3: 0.15, 4: 0.45, 5: 0.40},
        "scheduled": False,
        "weekend_multiplier": 1.10,     # minor complaints skew to days off
        "staff_intensity": 0.85,
        "pathway": [
            {"type": "visit", "department": "emergency_room", "probability": 1.00,
             "duration_hours": (1.0, 4.0)},
            {"type": "visit", "department": "radiology_lab", "probability": 0.25,
             "duration_hours": (0.5, 1.5)},
        ],
        "complication_probability": 0.02,
        "readmission_probability": 0.03,
    },
    {
        "name": "Emergency / Trauma",
        "weight": 0.14,
        "esi_distribution": {1: 0.22, 2: 0.48, 3: 0.30},
        "scheduled": False,
        "weekend_multiplier": 1.20,
        "staff_intensity": 1.40,
        "pathway": [
            {"type": "visit", "department": "emergency_room", "probability": 1.00,
             "duration_hours": (2.0, 6.0)},
            {"type": "visit", "department": "radiology_lab", "probability": 0.80,
             "duration_hours": (0.5, 2.0)},
            {"type": "branch", "probability": 1.00, "options": [
                {"weight": 0.12, "department": "icu", "duration_hours": (24.0, 120.0)},
                {"weight": 0.30, "department": "surgery", "duration_hours": (2.0, 8.0)},
                {"weight": 0.58, "department": None, "duration_hours": (0.0, 0.0)},
            ]},
            {"type": "visit", "department": "general_ward", "probability": 0.55,
             "duration_hours": (24.0, 96.0)},
        ],
        "complication_probability": 0.18,
        "readmission_probability": 0.12,
    },
    {
        "name": "Scheduled Surgery",
        "weight": 0.10,
        "esi_distribution": {3: 0.55, 4: 0.45},
        "scheduled": True,
        "arrival_hours": (7, 15),       # booked slots, not random arrivals
        "weekend_multiplier": 0.12,     # elective lists barely run on weekends
        "staff_intensity": 1.20,
        "pathway": [
            # Pre-op holding is folded into the OR block rather than modelled as
            # its own department; it consumes surgical staff either way.
            {"type": "visit", "department": "surgery", "probability": 1.00,
             "duration_hours": (2.0, 6.0)},
            {"type": "visit", "department": "general_ward", "probability": 0.55,
             "duration_hours": (24.0, 96.0)},
        ],
        "complication_probability": 0.08,
        "readmission_probability": 0.07,
    },
    {
        "name": "Chronic Follow-up",
        "weight": 0.25,
        "esi_distribution": {4: 0.35, 5: 0.65},
        "scheduled": True,
        "arrival_hours": (8, 17),
        "weekend_multiplier": 0.08,
        "staff_intensity": 0.70,
        "pathway": [
            {"type": "visit", "department": "outpatient_clinic", "probability": 1.00,
             "duration_hours": (0.5, 1.5)},
            {"type": "visit", "department": "radiology_lab", "probability": 0.40,
             "duration_hours": (0.25, 1.0)},
        ],
        "complication_probability": 0.01,
        # Follow-up care is recurring by definition — this is a scheduled return
        # visit rather than a failure of the previous encounter.
        "readmission_probability": 0.05,
    },
    {
        "name": "Pediatric",
        "weight": 0.10,
        "esi_distribution": {2: 0.10, 3: 0.30, 4: 0.40, 5: 0.20},
        "scheduled": False,
        "weekend_multiplier": 1.05,
        "staff_intensity": 1.35,        # tighter staffing ratios for children
        "pathway": [
            {"type": "branch", "probability": 1.00, "options": [
                {"weight": 0.60, "department": "emergency_room",
                 "duration_hours": (1.5, 5.0)},
                {"weight": 0.40, "department": "outpatient_clinic",
                 "duration_hours": (0.5, 1.5)},
            ]},
            {"type": "visit", "department": "radiology_lab", "probability": 0.30,
             "duration_hours": (0.5, 1.5)},
            {"type": "visit", "department": "general_ward", "probability": 0.15,
             "duration_hours": (12.0, 72.0)},
        ],
        "complication_probability": 0.06,
        "readmission_probability": 0.06,
    },
    {
        "name": "Elderly / Comorbid",
        "weight": 0.08,
        "esi_distribution": {1: 0.08, 2: 0.35, 3: 0.42, 4: 0.15},
        "scheduled": False,
        "weekend_multiplier": 1.00,
        "staff_intensity": 1.25,
        "pathway": [
            {"type": "visit", "department": "emergency_room", "probability": 1.00,
             "duration_hours": (2.0, 7.0)},
            {"type": "visit", "department": "radiology_lab", "probability": 0.60,
             "duration_hours": (0.5, 2.0)},
            {"type": "visit", "department": "general_ward", "probability": 0.70,
             "duration_hours": (48.0, 120.0)},
        ],
        "complication_probability": 0.28,
        "readmission_probability": 0.22,
    },
]

ARCHETYPE_NAMES = [a["name"] for a in PATIENT_ARCHETYPES]
ARCHETYPES_BY_NAME = {a["name"]: a for a in PATIENT_ARCHETYPES}

# ---------------------------------------------------------------------------
# Complication and readmission tuning
# ---------------------------------------------------------------------------

# A complication stretches every remaining stay by this factor.
COMPLICATION_LOS_MULTIPLIER = (1.3, 2.4)

# Chance a complication escalates an inpatient straight to the ICU.
COMPLICATION_ICU_ESCALATION_PROBABILITY = 0.18
COMPLICATION_ICU_DURATION_HOURS = (18.0, 72.0)

# How long after discharge a readmitted patient comes back. Readmissions that
# would land past the end of the simulation window simply never arrive.
READMISSION_DELAY_DAYS = (3, 30)

# Readmissions inside this window are the ones that count against the headline
# readmission rate, matching the standard 30-day measure.
READMISSION_WINDOW_DAYS = 30


def get_archetype_weights() -> list:
    return [a["weight"] for a in PATIENT_ARCHETYPES]


def _validate() -> None:
    """Fail loudly at import if the hand-tuned distributions drift out of sync."""
    total_weight = sum(a["weight"] for a in PATIENT_ARCHETYPES)
    if abs(total_weight - 1.0) > 1e-6:
        raise ValueError(f"archetype weights sum to {total_weight}, expected 1.0")

    for archetype in PATIENT_ARCHETYPES:
        esi_total = sum(archetype["esi_distribution"].values())
        if abs(esi_total - 1.0) > 1e-6:
            raise ValueError(
                f"{archetype['name']}: ESI distribution sums to {esi_total}, expected 1.0"
            )
        for level in archetype["esi_distribution"]:
            if level not in ESI_LEVELS:
                raise ValueError(f"{archetype['name']}: unknown ESI level {level}")

        for step in archetype["pathway"]:
            if step["type"] == "branch":
                branch_total = sum(o["weight"] for o in step["options"])
                if abs(branch_total - 1.0) > 1e-6:
                    raise ValueError(
                        f"{archetype['name']}: branch weights sum to {branch_total}, expected 1.0"
                    )
                targets = [o["department"] for o in step["options"]]
            elif step["type"] == "visit":
                targets = [step["department"]]
            else:
                raise ValueError(f"{archetype['name']}: unknown step type {step['type']!r}")

            for key in targets:
                # None is legal on a branch option; it means "no care at this stage".
                if key is not None and key not in DEPARTMENTS_BY_KEY:
                    raise ValueError(f"{archetype['name']}: unknown department {key!r}")


_validate()
