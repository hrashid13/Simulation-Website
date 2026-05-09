# Amusement Park Simulation Website

A web application that simulates the daily operations of an amusement park over a user-defined number of days (1–365). Enter a day count, run the simulation, and get a fully generated analytical report with interactive charts and a downloadable PDF.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| Charts | Recharts |
| PDF generation | ReportLab + Matplotlib |

---

## Project Structure

```
simulation_website/
├── backend/
│   ├── main.py                  # FastAPI app — /simulate and /report/pdf endpoints
│   ├── requirements.txt
│   ├── simulation/
│   │   ├── archetypes.py        # Visitor archetype definitions
│   │   ├── rides.py             # Ride definitions
│   │   ├── stores.py            # Store and restaurant definitions
│   │   ├── weather.py           # Weather system
│   │   ├── attendance.py        # Daily attendance model
│   │   └── engine.py            # Core simulation loop
│   └── report/
│       └── generator.py         # PDF report generator
└── frontend/
    ├── package.json
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── ConfigScreen.jsx  # Day input and Run button
        │   ├── LoadingScreen.jsx # Spinner while backend processes
        │   └── ReportScreen.jsx  # Full report with all charts and tables
        └── charts/
            ├── constants.js
            ├── DailyTrendsCharts.jsx
            ├── RevenueCharts.jsx
            ├── RideCharts.jsx
            ├── StoreCharts.jsx
            └── DemographicsCharts.jsx
```

---

## Running Locally

You need **Python 3.10+** and **Node.js 18+** installed.

### 1. Start the backend

Open a terminal in the `backend/` folder:

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

You can confirm it is running by visiting `http://localhost:8000/health` in your browser — it should return `{"status":"ok"}`.

### 2. Start the frontend

Open a second terminal in the `frontend/` folder:

```bash
cd frontend

# Install dependencies (first run only)
npm install

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## Using the App

1. Open `http://localhost:5173` in your browser.
2. Enter the number of days to simulate (1–365), or click a preset button (7d / 30d / 90d / 180d / 365d).
3. Click **Run Simulation** and wait for the report to generate (typically under 10 seconds even for 365 days).
4. Browse the 8-section report — use the navigation bar at the top to jump between sections.
5. Click **Download PDF** to export the full report as a PDF file.
6. Click **New Simulation** to run again with different settings.

---

## API Reference

### `POST /simulate`

Runs the simulation and returns all data needed to render the report.

**Request body:**
```json
{ "days": 30 }
```

**Response:** JSON object with keys: `summary`, `daily_data`, `ride_stats`, `store_stats`, `ticket_stats`, `weather_log`, `incidents`.

### `POST /report/pdf`

Accepts the simulation result JSON and returns a PDF file.

**Request body:** The full JSON response from `/simulate`.

**Response:** `application/pdf` file download.

### `GET /health`

Returns `{"status": "ok"}`. Useful for confirming the server is up.

---

## Environment Variables

### Frontend

Create a `.env` file in the `frontend/` folder to override the default API URL:

```
VITE_API_URL=http://localhost:8000
```

This is only needed if your backend runs on a different host or port.

---

## Building for Production

### Backend

Deploy `backend/` to any Python host (Railway, Render, Fly.io, etc.). The start command is:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm run build
```

The output in `frontend/dist/` can be served from any static host (Netlify, Vercel, GitHub Pages, etc.). Set the `VITE_API_URL` environment variable in your hosting platform to point to your deployed backend URL.
