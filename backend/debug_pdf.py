import traceback
from simulation.engine import run_simulation
from report.generator import generate_pdf_report

for days in [90, 180, 365]:
    print(f"\n--- {days} days ---")
    try:
        result = run_simulation(days)
        pdf = generate_pdf_report(result)
        print(f"OK: {len(pdf):,} bytes")
    except Exception as e:
        print(f"FAILED: {e}")
        traceback.print_exc()
