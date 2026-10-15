import pytest
from src.tools import ExactMathTool
from src.main import ProductStrategyPayload

def test_exact_math_tool_accuracy():
    math_tool = ExactMathTool()
    # Test deterministic arithmetic execution
    equation = "2.50 * 5000 + (2.50 * 5000 * 0.15)"
    result = math_tool._run(equation)
    
    # The ExactMathTool should return the precise mathematical float, not a hallucinated string
    assert "14375" in str(result), f"Expected 14375 in result, got {result}"

def test_math_tool_error_handling():
    math_tool = ExactMathTool()
    # Simulate the LLM passing conversational text instead of an equation
    bad_input = "Calculate the cost of 5 units"
    result = math_tool._run(bad_input)
    
    # The tool must catch the error and trigger the ReAct reflection loop
    assert "Action Input Error" in result

def test_pydantic_schema_validation():
    # Simulate a successful JSON payload from the Manager agent
    mock_payload = {
        "product_name": "Smart Thermostat",
        "target_market": "Residential",
        "technical_feasibility": {
            "bill_of_materials": [
                {"component_id": "cpl_123", "description": "Sensor", "quantity": 1, "unit_cost": 5.0, "total_cost": 5.0}
            ],
            "total_raw_material_cost": 5.0
        },
        "manufacturing_plan": {
            "assembly_overhead_cost": 2.0,
            "total_unit_cost": 7.0,
            "projected_lead_time_weeks": 4,
            "gantt_chart_mermaid": "gantt..."
        },
        "market_strategy": {
            "competitor_price_range": {"min": 15.0, "max": 25.0},
            "recommended_retail_price": 19.99,
            "projected_profit_margin_percent": 65.0,
            "target_demographic": "Homeowners"
        },
        "validation_status": "APPROVED"
    }
    
    # This will raise a ValidationError if the agent missed a field or hallucinated a string instead of a float
    validated_data = ProductStrategyPayload(**mock_payload)
    assert validated_data.validation_status == "APPROVED"