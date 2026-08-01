# HospitalSim — Hospital Operations Simulation

## Overview

A web application that simulates the daily operations of a hospital over a user-defined number of days. Enter how many days you want to simulate, hit run, and receive a fully generated analytical report with data visualizations and a downloadable PDF summary. Every run is randomized based on configurable probability distributions.

This is the second simulation module in the Simuleras platform, following the same architecture established by ParkSim (the amusement park simulator): a Python/FastAPI simulation engine feeding a React/Recharts frontend, with no database required — everything runs in memory per session.

---

## Goals

- Reuse the existing engine → report → frontend pipeline from ParkSim with minimal structural changes
- Model hospital patient flow realistically enough to produce interesting, varied analytics (not just random noise)
- Keep the simulation fast enough to run 1–365 simulated days in a single request/response cycle
- Produce a report that reads like something an actual hospital ops analyst would want to see

---

## Core Concepts

### 1. Patient Archetypes (`simulation/patients.py`)

Each simulated patient is generated from an archetype that determines arrival pattern, acuity, and resource needs:

| Archetype | Typical Path | Length of Stay | Notes |
|---|---|---|---|
| Walk-in / minor | ER → discharge | Hours | Low acuity, fast turnover |
| Emergency / trauma | ER → ICU or surgery | Days | High acuity, resource-intensive |
| Scheduled surgery | Pre-op → surgery → recovery ward | 1–5 days | Predictable, not random arrival |
| Chronic follow-up | Outpatient clinic | Same day | Recurring, low resource load |
| Pediatric | ER or clinic → ward | Varies | Different staffing ratios |
| Elderly / comorbid | ER → ward, higher readmission risk | Longer | Higher chance of complications event |

Each archetype carries: arrival probability weight, triage severity distribution (mapped to ESI 1–5 scale), base length-of-stay distribution, and a complication probability.

### 2. Departments (`simulation/departments.py`)

The hospital's constrained resources, analogous to ParkSim's rides:

- **Emergency Room** — intake point for most walk-in and emergency archetypes; capacity = bays
- **Radiology / Lab** — shared diagnostic resource, causes queueing delays
- **Surgery** — scheduled + emergency cases compete for OR slots
- **ICU** — limited beds, highest cost, triggers diversion when full
- **General Ward** — step-down and recovery beds
- **Outpatient Clinic** — separate low-acuity flow, mostly unaffected by ER surges

Each department has: bed/room capacity, staff-to-patient ratio, a queue, and a random "disruption" event chance (equipment downtime, staff callout, or going on diversion when over capacity) — the hospital analog of a ride breakdown.

### 3. Support Services (`simulation/services.py`)

Secondary touchpoints, analogous to ParkSim's stores:

- Pharmacy
- Billing / registration desk
- Cafeteria (staff and visitor traffic, not clinical but affects satisfaction metrics)

### 4. Events (`simulation/events.py`)

The exogenous shock generator, analogous to ParkSim's weather system. Each simulated day is assigned an event type that shifts arrival volume and severity mix:

- **Normal day** — baseline arrival rate
- **Flu season / seasonal surge** — elevated volume, lower average acuity
- **Mass casualty event** — rare, spikes ER and surgery load sharply
- **Staffing shortage** — reduces effective department capacity rather than increasing demand

### 5. Admissions Engine (`simulation/admissions.py`)

Generates hourly/daily patient arrivals based on the day's event type, archetype weights, and triage severity, then feeds them into the routing engine.

### 6. Core Engine (`simulation/engine.py`)

Ties it together tick by tick: patient generated → triage → routed to department → treatment duration elapses → discharge, transfer, or admission to another department → resource freed.

---

## Report Metrics (`report/generator.py`)

- Average and max wait time by department
- Bed occupancy over the simulated period (time series)
- Patient throughput (admissions, discharges, transfers) per day
- Triage severity breakdown (ESI 1–5 distribution)
- Readmission rate
- Revenue/cost estimate per department
- Staffing utilization vs. capacity
- "Worst day" callout — the day with peak load or an event-driven spike

---

## Tech Stack

Same as ParkSim, no new dependencies required:

| Layer | Technology |
|---|---|
| Frontend | React (Vite) |
| Backend | Python, FastAPI |
| Charts | Recharts |
| PDF Generation | WeasyPrint |

---

## Project Structure

```
backend/
├── main.py                     # add /simulate/hospital route
├── simulation/
│   ├── hospital_engine.py
│   ├── patients.py
│   ├── departments.py
│   ├── services.py
│   ├── events.py
│   └── admissions.py
├── report/
│   └── hospital_report_generator.py
frontend/
├── src/
│   ├── components/
│   │   ├── HospitalConfigScreen.jsx
│   │   ├── DepartmentOccupancyHeatmap.jsx
│   │   ├── WaitTimeChart.jsx
│   │   └── TriageSeverityChart.jsx
```

---

## Out of Scope (v1)

- Multi-hospital / network-level simulation
- Real-time streaming updates (still a single run → full report model, like ParkSim)
- Insurance/billing detail beyond a flat revenue-per-encounter estimate
- Staff scheduling optimization (staffing levels are inputs, not something the sim solves for)

---

## Open Questions

- Should triage severity use the real ESI 1–5 scale, or a simplified 3-tier system for a cleaner report?
- Should mass-casualty events be a rare random occurrence, or a toggle the user can force on to test capacity limits?
- Does "Out of Scope" for v1 include or exclude a simple cost/revenue estimate per department — worth deciding before building the report generator?
