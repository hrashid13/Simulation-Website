# ParkSim — Amusement Park Simulation Website

A web application that simulates the daily operations of an amusement park over a user-defined number of days. Enter how many days you want to simulate, hit run, and receive a fully generated analytical report with data visualizations and a downloadable PDF summary. Every run is completely random.

---

## Note

The main reason for this project is to make a PRD of an idea for a website, and see how well Claude code can follow it. From there I will build more features off the foundation that Claude creates. 

---

## Features

- Simulate 1 to 365 days of amusement park operations
- Dynamic weather system (sunny, cloudy, rainy) affecting attendance and revenue
- 6 visitor archetypes with unique behaviors and spending patterns
- 7 rides with capacity limits, queue tracking, and random breakdown events
- 12 stores and restaurants across food & beverage and retail categories
- Full analytical report with charts covering attendance, revenue, rides, stores, and demographics
- Downloadable PDF report

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite) |
| Backend | Python, FastAPI |
| Charts | Recharts |
| PDF Generation | WeasyPrint |

---

## Project Structure

```
simulation_website/
├── backend/
│   ├── main.py
│   ├── simulation/
│   │   ├── engine.py
│   │   ├── archetypes.py
│   │   ├── rides.py
│   │   ├── stores.py
│   │   ├── weather.py
│   │   └── attendance.py
│   ├── report/
│   │   └── generator.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   └── package.json
├── amusement_park_sim_PRD.md
├── .gitignore
└── README.md
```

---

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## How It Works

1. Enter the number of days to simulate on the config screen
2. Click **Run Simulation**
3. The backend runs the full simulation in memory — no database required
4. The report renders in-browser with all analytics and visualizations
5. Download the PDF summary when done

## Author

**Built by Hesham Rashid**
- Portfolio: https://www.heshamrashid.org/
- LinkedIn: https://www.linkedin.com/in/hesham-rashid/
- Email: h.f.rashid@gmail.com

Master's in AI and Business Analytics - University of South Florida
