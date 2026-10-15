from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.main import run_planning_session
import json
import os
from datetime import datetime
app = FastAPI(title="Product Planning API")

class PlanRequest(BaseModel):
    product_spec: str
    budget_usd: float

@app.post("/api/v1/plan/generate")
def generate_plan(request: PlanRequest):
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        # Construct the detailed prompt combining spec and budget constraints
        # full_prompt = f"{request.product_spec}. Maximum unit budget: ${request.budget_usd}."
        # Append the strict date constraint to the prompt
        full_prompt = (
            f"{request.product_spec}. Maximum unit budget: ${request.budget_usd}. "
            f"CRITICAL: The current date is {current_date}. All production timelines "
            f"and Gantt charts MUST start from this exact date."
        )
        # Trigger the synchronous CrewAI execution
        run_planning_session(full_prompt)
        
        # Use the absolute path matching your main.py export logic
        file_path = "/app/results/latest_strategy.json"
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                payload = json.load(f)
            return {"status": "success", "data": payload}
        else:
            raise HTTPException(status_code=500, detail="Planning completed, but JSON output not found.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run via: uvicorn src.api:app --reload --port 8000