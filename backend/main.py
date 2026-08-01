from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
import io

from simulation.engine import run_simulation
from simulation.hospital.engine import run_simulation as run_hospital_simulation
from report.generator import generate_pdf_report
from report.hospital_generator import generate_hospital_pdf_report
from report.exporter import generate_csv_zip, generate_sql
from report.hospital_exporter import generate_hospital_csv_zip, generate_hospital_sql

app = FastAPI(title="Simuleras Simulation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationRequest(BaseModel):
    days: int = Field(..., ge=1, le=365, description="Number of days to simulate")


class HospitalSimulationRequest(BaseModel):
    days: int = Field(..., ge=1, le=365, description="Number of days to simulate")
    force_mass_casualty: bool = Field(
        False, description="Guarantee at least one mass casualty event in the run"
    )


@app.post("/simulate")
def simulate(request: SimulationRequest):
    try:
        result = run_simulation(request.days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate/hospital")
def simulate_hospital(request: HospitalSimulationRequest):
    try:
        return run_hospital_simulation(request.days, request.force_mass_casualty)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report/hospital/pdf")
def report_hospital_pdf(data: dict = Body(...)):
    try:
        days = data.get("summary", {}).get("total_days", 0)
        pdf_bytes = generate_hospital_pdf_report(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f"attachment; filename=hospitalsim_report_{days}days.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/hospital/csv")
def export_hospital_csv(data: dict = Body(...)):
    try:
        days = data.get("summary", {}).get("total_days", 0)
        zip_bytes = generate_hospital_csv_zip(data)
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition":
                    f"attachment; filename=hospitalsim_data_{days}days.zip"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/hospital/sql")
def export_hospital_sql(data: dict = Body(...)):
    try:
        days = data.get("summary", {}).get("total_days", 0)
        sql_bytes = generate_hospital_sql(data)
        return StreamingResponse(
            io.BytesIO(sql_bytes),
            media_type="application/sql",
            headers={
                "Content-Disposition":
                    f"attachment; filename=hospitalsim_data_{days}days.sql"
            },
        )
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
