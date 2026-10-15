import os
import json
from pydantic import BaseModel, Field
from typing import List, Dict
from crewai import Task, Crew, Process
from src.agents import manager_agent, rnd_agent, mfg_agent, mktg_agent
from src.agents import local_llm
import traceback
from datetime import datetime
current_date = datetime.now().strftime("%Y-%m-%d")
# 1. Define the Pydantic Schema for the downstream Power BI Dashboard
class BOMItem(BaseModel):
    component_id: str
    description: str
    quantity: int
    unit_cost: float
    total_cost: float

class ProductStrategyPayload(BaseModel):
    product_name: str
    target_market: str
    technical_feasibility: Dict[str, List[BOMItem] | float] = Field(..., description="Contains the bill_of_materials and total_raw_material_cost.")
    manufacturing_plan: Dict[str, float | int | str] = Field(..., description="Contains assembly overhead, total unit cost, lead time, and gantt_chart_mermaid.")
    market_strategy: Dict[str, float | str | dict] = Field(..., description="Contains competitor price range, recommended retail price, and target demographic.")
    validation_status: str = Field(..., description="APPROVED, REVISED, or REJECTED")

# 2. Define Sequential Sub-Tasks
rnd_task = Task(
    description="Analyze the user's product specification. Search the component catalog to select real-world, orderable hardware parts. Output a draft Bill of Materials.",
    expected_output="A structured list of hardware components with precise SKUs and base costs.",
    agent=rnd_agent
)

mfg_task = Task(
    description=("Take the R&D BOM. Query supply chain logistics for shipping times. Use the Exact Calculator to sum the BOM costs and add a 15% factory assembly overhead. Generate a production timeline in Mermaid.js Gantt format." f"CRITICAL: Today is {current_date}. Your Gantt chart MUST begin on {current_date}. "
        "Do not use 2023."),
    expected_output="A validated cost matrix and a Mermaid.js Gantt chart block.",
    agent=mfg_agent
)

mktg_task = Task(
    description="Take the final manufacturing cost. Search the web for competitor pricing for this type of product. Define a retail price that ensures at least a 30% profit margin.""CRITICAL: You must end your final response with exactly these two lines:\n"
    "Target Retail Price: $[Insert Price]\n"
    "Competitor Range: $[Insert Min] to $[Insert Max]",
    expected_output="A market positioning strategy with competitor price benchmarks and a final retail price.",
    agent=mktg_agent
)

# 3. Define the Orchestration Crew
product_crew = Crew(
    agents=[rnd_agent, mfg_agent, mktg_agent],
    tasks=[rnd_task, mfg_task, mktg_task],
    # process=Process.hierarchical,
    process=Process.sequential,
    # manager_agent=manager_agent,  # Forces the custom manager to evaluate outputs
    # manager_llm=local_llm,
    output_pydantic=ProductStrategyPayload, # Enforces strict JSON structure
    # memory=True,
    verbose=True
)

def run_planning_session(product_spec: str):
    print(f"Initiating Planning Session for: {product_spec}")
    try:
        result = product_crew.kickoff(inputs={'product_specification': product_spec})
        
        # Export to JSON for Business Intelligence ingestion
        os.makedirs("/app/results", exist_ok=True)
        with open("/app/results/latest_strategy.json", "w") as f:
            json.dump(result.dict(), f, indent=4)
        print("Session Complete. Output exported to /results/latest_strategy.json")
        return result
    
    except Exception as e:
        print("\n" + "="*50)
        print("💥 FATAL CREW CRASH CAUGHT 💥")
        traceback.print_exc()
        print("="*50 + "\n")
        raise e

if __name__ == "__main__":
    test_spec = "A portable solar-powered outdoor air quality monitor. Maximum unit budget: $65."
    run_planning_session(test_spec)