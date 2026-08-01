"""
CSV and SQL export for HospitalSim simulation data.

All generation is in-memory (no disk writes) — the user keeps whatever they
download, the site keeps nothing.

Note on ESI keys: the engine emits them as strings so the payload round-trips
through JSON unchanged, which means they sort lexicographically unless coerced.
Every ordering here sorts by int.
"""

import csv
import io
import zipfile
from datetime import date

# Column order is fixed once and reused by both the CSV and SQL builders so the
# two exports can never drift apart.
DAILY_COLUMNS = [
    "day", "day_of_week", "is_weekend", "event", "arrivals", "admissions",
    "discharges", "transfers", "diversions", "complications",
    "readmissions_scheduled", "readmissions_returned", "mass_casualty_arrivals",
    "avg_inpatient_census", "revenue", "cost", "net", "satisfaction",
]

DEPARTMENT_DAILY_COLUMNS = [
    "day", "department", "encounters", "avg_occupancy_pct", "peak_occupancy_pct",
    "avg_occupied", "peak_occupied", "avg_wait_minutes", "max_wait_minutes",
]

TRIAGE_DAILY_COLUMNS = ["day", "esi_level", "severity", "patients"]
ARCHETYPE_DAILY_COLUMNS = ["day", "archetype", "patients"]

DEPARTMENT_SUMMARY_COLUMNS = [
    "department", "unit", "capacity", "total_encounters", "total_bed_hours",
    "avg_occupancy_pct", "peak_occupancy_pct", "avg_wait_minutes",
    "max_wait_minutes", "staffed_level", "staff_utilization_pct",
    "disruption_count", "disruption_hours", "revenue", "cost", "net_margin",
]

TRIAGE_SUMMARY_COLUMNS = [
    "esi_level", "severity", "patients", "share_pct", "avg_er_wait_minutes",
    "target_wait_minutes", "within_target_pct",
]

OCCUPANCY_COLUMNS_BASE = ["day", "hour"]
DISRUPTION_COLUMNS = ["day", "department", "disruption_type", "hours"]
EVENT_COLUMNS = ["day", "event"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _csv_bytes(rows: list[list]) -> bytes:
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return buf.getvalue().encode("utf-8")


def _esi_levels(data: dict) -> list[str]:
    return sorted(data["esi_stats"], key=int)


def _department_keys(data: dict) -> list[str]:
    return list(data["department_stats"])


def _department_name(data: dict, key: str) -> str:
    return data["department_stats"][key]["name"]


# ---------------------------------------------------------------------------
# Row builders — shared by the CSV and SQL paths
# ---------------------------------------------------------------------------

def _daily_rows(data: dict) -> list[list]:
    rows = []
    for d in data["daily_data"]:
        rows.append([
            d["day"], d["day_of_week"], d["is_weekend"], d["event"],
            d["arrivals"], d["admissions"], d["discharges"], d["transfers"],
            d["diversions"], d["complications"], d["readmissions_scheduled"],
            d["readmissions"], d["mass_casualty_arrivals"],
            d["avg_inpatient_census"],
            round(d["revenue"], 2), round(d["cost"], 2), round(d["net"], 2),
            d["satisfaction"],
        ])
    return rows


def _department_daily_rows(data: dict) -> list[list]:
    rows = []
    keys = _department_keys(data)
    for d in data["daily_data"]:
        for key in keys:
            occ = d["department_occupancy"][key]
            wait = d["department_waits"][key]
            rows.append([
                d["day"], _department_name(data, key),
                d["department_encounters"][key],
                occ["avg_pct"], occ["peak_pct"], occ["avg_occupied"], occ["peak_occupied"],
                wait["avg_minutes"], wait["max_minutes"],
            ])
    return rows


def _triage_daily_rows(data: dict) -> list[list]:
    rows = []
    levels = _esi_levels(data)
    for d in data["daily_data"]:
        for level in levels:
            rows.append([
                d["day"], int(level),
                data["esi_stats"][level]["label"],
                d["esi_counts"][level],
            ])
    return rows


def _archetype_daily_rows(data: dict) -> list[list]:
    rows = []
    for d in data["daily_data"]:
        for name, count in d["archetype_counts"].items():
            rows.append([d["day"], name, count])
    return rows


def _department_summary_rows(data: dict) -> list[list]:
    rows = []
    for s in data["department_stats"].values():
        rows.append([
            s["name"], s["unit"], s["capacity"], s["total_encounters"],
            s["total_bed_hours"], s["avg_occupancy_pct"], s["peak_occupancy_pct"],
            s["avg_wait_minutes"], s["max_wait_minutes"], s["staffed_level"],
            s["staff_utilization_pct"], s["disruption_count"], s["disruption_hours"],
            round(s["revenue"], 2), round(s["cost"], 2), round(s["net_margin"], 2),
        ])
    return rows


def _triage_summary_rows(data: dict) -> list[list]:
    rows = []
    for level in _esi_levels(data):
        s = data["esi_stats"][level]
        rows.append([
            int(level), s["label"], s["count"], s["share_pct"],
            s["avg_er_wait_minutes"], s["target_wait_minutes"], s["within_target_pct"],
        ])
    return rows


def _occupancy_columns(data: dict) -> list[str]:
    # Hourly runs carry an `hour` column; daily runs do not.
    hourly = data["summary"]["occupancy_resolution"] == "hourly"
    base = OCCUPANCY_COLUMNS_BASE if hourly else ["day"]
    return base + [f"{k}_occupancy_pct" for k in _department_keys(data)]


def _occupancy_rows(data: dict) -> list[list]:
    hourly = data["summary"]["occupancy_resolution"] == "hourly"
    keys = _department_keys(data)
    rows = []
    for row in data["occupancy_series"]:
        prefix = [row["day"], row["hour"]] if hourly else [row["day"]]
        rows.append(prefix + [row[k] for k in keys])
    return rows


def _disruption_rows(data: dict) -> list[list]:
    return [[d["day"], d["department"], d["type"], d["hours"]]
            for d in data["disruptions"]]


def _event_rows(data: dict) -> list[list]:
    return [[e["day"], e["event"]] for e in data["event_log"]]


# ---------------------------------------------------------------------------
# Public: CSV ZIP export
# ---------------------------------------------------------------------------

def generate_hospital_csv_zip(data: dict) -> bytes:
    """Return ZIP archive bytes containing every hospital CSV table."""
    buf = io.BytesIO()

    files = [
        ("daily_summary.csv",       DAILY_COLUMNS,              _daily_rows(data)),
        ("department_daily.csv",    DEPARTMENT_DAILY_COLUMNS,   _department_daily_rows(data)),
        ("triage_daily.csv",        TRIAGE_DAILY_COLUMNS,       _triage_daily_rows(data)),
        ("archetype_daily.csv",     ARCHETYPE_DAILY_COLUMNS,    _archetype_daily_rows(data)),
        ("occupancy_timeseries.csv", _occupancy_columns(data),  _occupancy_rows(data)),
        ("department_summary.csv",  DEPARTMENT_SUMMARY_COLUMNS, _department_summary_rows(data)),
        ("triage_summary.csv",      TRIAGE_SUMMARY_COLUMNS,     _triage_summary_rows(data)),
        ("disruptions.csv",         DISRUPTION_COLUMNS,         _disruption_rows(data)),
        ("events.csv",              EVENT_COLUMNS,              _event_rows(data)),
    ]

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, columns, rows in files:
            zf.writestr(name, _csv_bytes([columns] + rows))

    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

def _sql_escape(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def _sql_insert_block(table: str, columns: list[str], rows: list[list]) -> str:
    if not rows:
        return f"-- No data for {table}\n"
    col_list = ", ".join(columns)
    values = ["(" + ", ".join(_sql_escape(v) for v in row) + ")" for row in rows]
    return f"INSERT INTO {table} ({col_list}) VALUES\n" + ",\n".join(values) + ";\n"


# ---------------------------------------------------------------------------
# Public: SQL export
# ---------------------------------------------------------------------------

def generate_hospital_sql(data: dict) -> bytes:
    s = data["summary"]
    today = date.today().isoformat()

    occupancy_columns = _occupancy_columns(data)
    occupancy_ddl = ",\n".join(
        f"    {c:<28} {'INTEGER' if c in ('day', 'hour') else 'REAL'}"
        for c in occupancy_columns
    )

    lines: list[str] = []

    lines.append(f"""\
-- HospitalSim Synthetic Data Export
-- Generated: {today}
-- Simulation Period: {s['total_days']} days
-- Total Patients: {s['total_patients']:,}
-- Total Revenue: ${s['total_revenue']:,.2f}
-- Occupancy Resolution: {s['occupancy_resolution']}
-- Compatible with: PostgreSQL, SQLite
""")

    # Dropped in reverse dependency order so a rerun is clean.
    for table in ("events", "disruptions", "triage_summary", "department_summary",
                  "occupancy_timeseries", "archetype_daily", "triage_daily",
                  "department_daily", "daily_summary"):
        lines.append(f"DROP TABLE IF EXISTS {table};")
    lines.append("")

    lines.append("""\
CREATE TABLE daily_summary (
    day                     INTEGER,
    day_of_week             TEXT,
    is_weekend              BOOLEAN,
    event                   TEXT,
    arrivals                INTEGER,
    admissions              INTEGER,
    discharges              INTEGER,
    transfers               INTEGER,
    diversions              INTEGER,
    complications           INTEGER,
    readmissions_scheduled  INTEGER,
    readmissions_returned   INTEGER,
    mass_casualty_arrivals  INTEGER,
    avg_inpatient_census    REAL,
    revenue                 REAL,
    cost                    REAL,
    net                     REAL,
    satisfaction            REAL
);
""")

    lines.append("""\
CREATE TABLE department_daily (
    day                 INTEGER,
    department          TEXT,
    encounters          INTEGER,
    avg_occupancy_pct   REAL,
    peak_occupancy_pct  REAL,
    avg_occupied        REAL,
    peak_occupied       INTEGER,
    avg_wait_minutes    REAL,
    max_wait_minutes    REAL
);
""")

    lines.append("""\
CREATE TABLE triage_daily (
    day       INTEGER,
    esi_level INTEGER,
    severity  TEXT,
    patients  INTEGER
);
""")

    lines.append("""\
CREATE TABLE archetype_daily (
    day       INTEGER,
    archetype TEXT,
    patients  INTEGER
);
""")

    lines.append(f"""\
CREATE TABLE occupancy_timeseries (
{occupancy_ddl}
);
""")

    lines.append("""\
CREATE TABLE department_summary (
    department            TEXT,
    unit                  TEXT,
    capacity              INTEGER,
    total_encounters      INTEGER,
    total_bed_hours       REAL,
    avg_occupancy_pct     REAL,
    peak_occupancy_pct    REAL,
    avg_wait_minutes      REAL,
    max_wait_minutes      REAL,
    staffed_level         REAL,
    staff_utilization_pct REAL,
    disruption_count      INTEGER,
    disruption_hours      INTEGER,
    revenue               REAL,
    cost                  REAL,
    net_margin            REAL
);
""")

    lines.append("""\
CREATE TABLE triage_summary (
    esi_level            INTEGER,
    severity             TEXT,
    patients             INTEGER,
    share_pct            REAL,
    avg_er_wait_minutes  REAL,
    target_wait_minutes  INTEGER,
    within_target_pct    REAL
);
""")

    lines.append("""\
CREATE TABLE disruptions (
    day             INTEGER,
    department      TEXT,
    disruption_type TEXT,
    hours           INTEGER
);
""")

    lines.append("""\
CREATE TABLE events (
    day   INTEGER,
    event TEXT
);
""")

    blocks = [
        ("daily_summary",        DAILY_COLUMNS,              _daily_rows(data)),
        ("department_daily",     DEPARTMENT_DAILY_COLUMNS,   _department_daily_rows(data)),
        ("triage_daily",         TRIAGE_DAILY_COLUMNS,       _triage_daily_rows(data)),
        ("archetype_daily",      ARCHETYPE_DAILY_COLUMNS,    _archetype_daily_rows(data)),
        ("occupancy_timeseries", occupancy_columns,          _occupancy_rows(data)),
        ("department_summary",   DEPARTMENT_SUMMARY_COLUMNS, _department_summary_rows(data)),
        ("triage_summary",       TRIAGE_SUMMARY_COLUMNS,     _triage_summary_rows(data)),
        ("disruptions",          DISRUPTION_COLUMNS,         _disruption_rows(data)),
        ("events",               EVENT_COLUMNS,              _event_rows(data)),
    ]

    for table, columns, rows in blocks:
        lines.append(_sql_insert_block(table, columns, rows))

    return "\n".join(lines).encode("utf-8")
