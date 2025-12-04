from mcp.server.fastmcp import FastMCP
import json
from typing import TypedDict, Annotated, Literal, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


mcp = FastMCP("Sales",host="0.0.0.0",port=8800)


@mcp.tool(name="capture_and_recommend_vehicle")
def capture_and_recommend_vehicle(vehicle_model: str, vehicle_type: str, usage_preference: str, budget: int, terrain_type: str) -> dict:
    """Capture user vehicle preferences and recommend suitable vehicles.

    Args:
        vehicle_model (str): Specific vehicle model
        vehicle_type (str): Type of vehicle
        usage_preference (str): Primary usage preference
        budget (int): Budget in currency units
        terrain_type (str): Typical terrain type

    Returns:
        str: Recommended vehicles in JSON format
    """
    # Mock recommendation logic
    recommendations = {
        "SUV": ["Ford Explorer"],
        "Sedan": ["Ford Territory"],
        "Truck": ["Ford F-150"],
        "Coupe": ["Ford Mustang"]    
    }
    
    result = {
        "status": "success",
        "recommended_vehicles": recommendations.get(vehicle_type, [])[:3],
        "message": f"Based on your preference for a {vehicle_type}, here are our top recommendations"
    }
    return result


@mcp.tool(name="explain_vehicle_details")
def explain_vehicle_details(vehicle_model: str) -> str:
    """Get the model name and explain the vehicle details.

    Args:
        vehicle_model (str): Vehicle model name

    Returns:
        str: Vehicle details in JSON format
    """
    # Mock vehicle database
    vehicle_info = {
        "specs": {
            "engine": "2.5L 4-cylinder",
            "horsepower": "203 hp",
            "transmission": "8-speed automatic",
            "fuel_economy": "28 city / 35 highway mpg"
        },
        "features": ["Adaptive Cruise Control", "Lane Keeping Assist", "Apple CarPlay", "Leather Seats"],
        "pricing": {
            "base_price": 35000,
            "currency": "USD"
        }
    }
    if vehicle_model in [ "Ford Explorer", "Ford Territory", "Ford Mustang", "Ford F-150"]:
        result = {
            "status": "success",
            "vehicle": vehicle_model,
            "details": vehicle_info
        }
        return json.dumps(result)
    else:
        return json.dumps({"status": "error", "message": "Model not found."})




@mcp.tool(name="capture_financial_information")
def capture_financial_information(payment_type:Literal["Cash Purchase", "Financing"], 
                                  trade_in:Literal["Yes", "No"], 
                                  tenure_years:int=5, 
                                  employment_entity:Literal["Government Agency", "Private sector", "Retired"] | None = None, 
                                  salary_in_account:int | None = None,
                                  resident_type:Literal["Citizen", "Resident"] | None = None) -> str:
    """Captures and processes financial information for vehicle purchase.

    Args:
        payment_type (Literal["Cash Purchase", "Financing"]): Payment type
        trade_in (Literal["Yes", "No"]): Trade-in option
        tenure_years (int, optional): Tenure in years. Defaults to 5.
        employment_entity (Literal["Government Agency", "Private sector", "Retired"] | None, optional): Employment entity. Defaults to None.
        salary_in_account (int | None, optional): Salary in account. Defaults to None.
        resident_type (Literal["Citizen", "Resident"] | None, optional): Resident type. Defaults to None.

    Returns:
        str: Financial information in JSON format
    """
    # Mock eligibility calculation
    eligibility = "approved" if payment_type == "Cash Purchase" or (
        salary_in_account and salary_in_account > 5000
    ) else "pending_review"
    
    result = {
        "status": "success",
        "eligibility": eligibility,
        "financing_options": {
            "monthly_payment": 650 if payment_type == "Financing" else None,
            "down_payment": 5000 if payment_type == "Financing" else None,
            "interest_rate": "4.5%" if payment_type == "Financing" else None
        }
    }
    return json.dumps(result)


@mcp.tool(name="book_appointment")
async def book_appointment(name: str, booking_type: Literal["Test Drive", "Showroom Visit"], time: str, city: str, vehicle_model: str) -> dict:
    """Books a test drive or showroom visit with the provided details.

    Args:
        name (str): Customer name
        booking_type (Literal["Test Drive", "Showroom Visit"]): Appointment type
        time (str): Time in ISO 8601 format
        city (str): City for appointment
        vehicle_model (str): Vehicle of interest

    Returns:
        dict: Booking status and confirmation details
    """
    result = {
        "status": "success",
        "confirmation_number": f"APT-{datetime.now().strftime('%Y%m%d%H%M')}",
        "booking_details": {
            "name": name,
            "type": booking_type,
            "datetime": time,
            "location": f"{city} Showroom",
            "vehicle": vehicle_model
        },
        "message": "Your appointment has been confirmed. We'll send a confirmation email shortly."
    }
    return result


if __name__ == "__main__":
    mcp.run(transport="streamable-http")