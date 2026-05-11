"""
CSV and SQL export for ParkSim simulation data.
All generation is in-memory (no disk writes).
"""

import csv
import io
import zipfile
from datetime import date


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _csv_bytes(rows: list[list]) -> bytes:
    """Write a list-of-lists (header + data) to CSV bytes."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _build_incident_lookup(data: dict) -> dict:
    """Return {(day, ride_name): hours_down} for quick per-day incident lookup."""
    lookup: dict[tuple, int] = {}
    for inc in data.get("incidents", []):
        key = (inc["day"], inc["ride"])
        lookup[key] = lookup.get(key, 0) + inc["hours_down"]
    return lookup


# ---------------------------------------------------------------------------
# CSV file builders — one function per file
# ---------------------------------------------------------------------------

def _csv_daily_summary(data: dict) -> bytes:
    rows = [["day", "day_of_week", "weather", "total_attendance",
             "ticket_revenue", "food_bev_revenue", "retail_revenue", "total_revenue"]]
    for d in data["daily_data"]:
        rows.append([
            d["day"],
            d["day_of_week"],
            d["weather"],
            d["attendance"],
            round(d["ticket_revenue"], 2),
            round(d["food_beverage_revenue"], 2),
            round(d["retail_merchandise_revenue"], 2),
            round(d["total_revenue"], 2),
        ])
    return _csv_bytes(rows)


def _csv_ride_stats(data: dict) -> bytes:
    incident_lookup = _build_incident_lookup(data)
    ride_meta = data["ride_stats"]  # includes max_hourly_capacity

    rows = [["day", "ride_name", "total_riders", "hours_open",
             "broke_down", "hours_down", "queue_utilization_pct"]]

    for d in data["daily_data"]:
        day = d["day"]
        ride_riders = d.get("ride_riders", {})
        ride_hours = d.get("ride_operating_hours", {})

        for ride_name, meta in ride_meta.items():
            riders = ride_riders.get(ride_name, 0)
            hours_open = ride_hours.get(ride_name, 0)
            hours_down = incident_lookup.get((day, ride_name), 0)
            broke_down = hours_down > 0
            max_cap = meta["max_hourly_capacity"]
            max_daily = max_cap * hours_open if hours_open > 0 else 1
            utilization = round(riders / max_daily * 100, 2) if max_daily > 0 else 0.0

            rows.append([
                day,
                ride_name,
                riders,
                hours_open,
                broke_down,
                hours_down,
                utilization,
            ])

    return _csv_bytes(rows)


def _csv_store_stats(data: dict) -> bytes:
    store_meta = data["store_stats"]  # {name: {category, total_revenue}}

    rows = [["day", "store_name", "category", "transactions", "revenue"]]

    for d in data["daily_data"]:
        day = d["day"]
        store_rev = d.get("store_revenue", {})
        store_txn = d.get("store_transactions", {})

        for store_name, meta in store_meta.items():
            cat = "food_bev" if meta["category"] == "food_beverage" else "retail"
            rows.append([
                day,
                store_name,
                cat,
                store_txn.get(store_name, 0),
                round(store_rev.get(store_name, 0.0), 2),
            ])

    return _csv_bytes(rows)


def _csv_visitor_demographics(data: dict) -> bytes:
    from simulation.archetypes import TICKET_PRICES

    rows = [["day", "ticket_type", "count", "revenue"]]

    for d in data["daily_data"]:
        day = d["day"]
        ticket_counts = d.get("ticket_counts", {})
        for t_type, count in ticket_counts.items():
            revenue = round(count * TICKET_PRICES.get(t_type, 0.0), 2)
            rows.append([day, t_type, count, revenue])

    return _csv_bytes(rows)


def _csv_incidents(data: dict) -> bytes:
    day_lookup = {d["day"]: d["day_of_week"] for d in data["daily_data"]}

    rows = [["day", "day_of_week", "ride_name", "hours_down"]]
    for inc in data.get("incidents", []):
        rows.append([
            inc["day"],
            day_lookup.get(inc["day"], ""),
            inc["ride"],
            inc["hours_down"],
        ])

    return _csv_bytes(rows)


# ---------------------------------------------------------------------------
# Public: CSV ZIP export
# ---------------------------------------------------------------------------

def generate_csv_zip(data: dict) -> bytes:
    """Return a ZIP archive bytes containing all 5 CSV files."""
    days = data["summary"]["total_days"]
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("daily_summary.csv",      _csv_daily_summary(data))
        zf.writestr("ride_stats.csv",          _csv_ride_stats(data))
        zf.writestr("store_stats.csv",         _csv_store_stats(data))
        zf.writestr("visitor_demographics.csv", _csv_visitor_demographics(data))
        zf.writestr("incidents.csv",           _csv_incidents(data))

    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

def _sql_escape(v) -> str:
    """Escape a value for SQL INSERT: strings quoted, numbers/booleans bare."""
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
    value_rows = [
        "(" + ", ".join(_sql_escape(v) for v in row) + ")"
        for row in rows
    ]
    return f"INSERT INTO {table} ({col_list}) VALUES\n" + ",\n".join(value_rows) + ";\n"


# ---------------------------------------------------------------------------
# Public: SQL export
# ---------------------------------------------------------------------------

def generate_sql(data: dict) -> bytes:
    s = data["summary"]
    days = s["total_days"]
    today = date.today().isoformat()
    incident_lookup = _build_incident_lookup(data)
    ride_meta = data["ride_stats"]
    store_meta = data["store_stats"]

    from simulation.archetypes import TICKET_PRICES

    lines: list[str] = []

    # ---- Header comment ----
    lines.append(f"""\
-- ParkSim Synthetic Data Export
-- Generated: {today}
-- Simulation Period: {days} days
-- Total Attendance: {s['total_attendance']:,}
-- Total Revenue: ${s['total_revenue']:,.2f}
-- Compatible with: PostgreSQL, SQLite
""")

    # ---- DROP TABLE ----
    lines.append("DROP TABLE IF EXISTS incidents;")
    lines.append("DROP TABLE IF EXISTS visitor_demographics;")
    lines.append("DROP TABLE IF EXISTS store_stats;")
    lines.append("DROP TABLE IF EXISTS ride_stats;")
    lines.append("DROP TABLE IF EXISTS daily_summary;")
    lines.append("")

    # ---- CREATE TABLE ----
    lines.append("""\
CREATE TABLE daily_summary (
    day                INTEGER,
    day_of_week        TEXT,
    weather            TEXT,
    total_attendance   INTEGER,
    ticket_revenue     REAL,
    food_bev_revenue   REAL,
    retail_revenue     REAL,
    total_revenue      REAL
);
""")

    lines.append("""\
CREATE TABLE ride_stats (
    day                     INTEGER,
    ride_name               TEXT,
    total_riders            INTEGER,
    hours_open              INTEGER,
    broke_down              BOOLEAN,
    hours_down              INTEGER,
    queue_utilization_pct   REAL
);
""")

    lines.append("""\
CREATE TABLE store_stats (
    day          INTEGER,
    store_name   TEXT,
    category     TEXT,
    transactions INTEGER,
    revenue      REAL
);
""")

    lines.append("""\
CREATE TABLE visitor_demographics (
    day         INTEGER,
    ticket_type TEXT,
    count       INTEGER,
    revenue     REAL
);
""")

    lines.append("""\
CREATE TABLE incidents (
    day         INTEGER,
    day_of_week TEXT,
    ride_name   TEXT,
    hours_down  INTEGER
);
""")

    # ---- INSERT: daily_summary ----
    ds_rows = []
    for d in data["daily_data"]:
        ds_rows.append([
            d["day"], d["day_of_week"], d["weather"], d["attendance"],
            round(d["ticket_revenue"], 2),
            round(d["food_beverage_revenue"], 2),
            round(d["retail_merchandise_revenue"], 2),
            round(d["total_revenue"], 2),
        ])
    lines.append(_sql_insert_block(
        "daily_summary",
        ["day", "day_of_week", "weather", "total_attendance",
         "ticket_revenue", "food_bev_revenue", "retail_revenue", "total_revenue"],
        ds_rows,
    ))

    # ---- INSERT: ride_stats ----
    rs_rows = []
    for d in data["daily_data"]:
        day = d["day"]
        ride_riders = d.get("ride_riders", {})
        ride_hours = d.get("ride_operating_hours", {})
        for ride_name, meta in ride_meta.items():
            riders = ride_riders.get(ride_name, 0)
            hours_open = ride_hours.get(ride_name, 0)
            hours_down = incident_lookup.get((day, ride_name), 0)
            broke_down = hours_down > 0
            max_daily = meta["max_hourly_capacity"] * hours_open if hours_open > 0 else 1
            utilization = round(riders / max_daily * 100, 2) if max_daily > 0 else 0.0
            rs_rows.append([day, ride_name, riders, hours_open, broke_down, hours_down, utilization])
    lines.append(_sql_insert_block(
        "ride_stats",
        ["day", "ride_name", "total_riders", "hours_open",
         "broke_down", "hours_down", "queue_utilization_pct"],
        rs_rows,
    ))

    # ---- INSERT: store_stats ----
    ss_rows = []
    for d in data["daily_data"]:
        day = d["day"]
        store_rev = d.get("store_revenue", {})
        store_txn = d.get("store_transactions", {})
        for store_name, meta in store_meta.items():
            cat = "food_bev" if meta["category"] == "food_beverage" else "retail"
            ss_rows.append([
                day, store_name, cat,
                store_txn.get(store_name, 0),
                round(store_rev.get(store_name, 0.0), 2),
            ])
    lines.append(_sql_insert_block(
        "store_stats",
        ["day", "store_name", "category", "transactions", "revenue"],
        ss_rows,
    ))

    # ---- INSERT: visitor_demographics ----
    vd_rows = []
    for d in data["daily_data"]:
        day = d["day"]
        for t_type, count in d.get("ticket_counts", {}).items():
            revenue = round(count * TICKET_PRICES.get(t_type, 0.0), 2)
            vd_rows.append([day, t_type, count, revenue])
    lines.append(_sql_insert_block(
        "visitor_demographics",
        ["day", "ticket_type", "count", "revenue"],
        vd_rows,
    ))

    # ---- INSERT: incidents ----
    day_lookup = {d["day"]: d["day_of_week"] for d in data["daily_data"]}
    inc_rows = [
        [inc["day"], day_lookup.get(inc["day"], ""), inc["ride"], inc["hours_down"]]
        for inc in data.get("incidents", [])
    ]
    lines.append(_sql_insert_block(
        "incidents",
        ["day", "day_of_week", "ride_name", "hours_down"],
        inc_rows,
    ))

    return "\n".join(lines).encode("utf-8")
