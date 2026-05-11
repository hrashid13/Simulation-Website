from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
import io

from simulation.engine import run_simulation
from report.generator import generate_pdf_report
from report.exporter import generate_csv_zip, generate_sql

app = FastAPI(title="Amusement Park Simulation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationRequest(BaseModel):
    days: int = Field(..., ge=1, le=365, description="Number of days to simulate")


@app.post("/simulate")
def simulate(request: SimulationRequest):
    try:
        result = run_simulation(request.days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report/pdf")
def report_pdf(data: dict = Body(...)):
    try:
        pdf_bytes = generate_pdf_report(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=amusement_park_report.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/csv")
def export_csv(data: dict = Body(...)):
    try:
        days = data.get("summary", {}).get("total_days", 0)
        zip_bytes = generate_csv_zip(data)
        filename = f"parksim_data_{days}days.zip"
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/sql")
def export_sql(data: dict = Body(...)):
    try:
        days = data.get("summary", {}).get("total_days", 0)
        sql_bytes = generate_sql(data)
        filename = f"parksim_data_{days}days.sql"
        return StreamingResponse(
            io.BytesIO(sql_bytes),
            media_type="application/sql",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
