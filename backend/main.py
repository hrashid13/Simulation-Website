from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from simulation.engine import run_simulation
from report.generator import generate_pdf_report

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


@app.get("/health")
def health():
    return {"status": "ok"}
