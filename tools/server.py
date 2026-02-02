from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI()

class MarginRequest(BaseModel):
    revenue: float
    cost: float

@app.get("/")
def home():
    return {"message": "ALU/Tool Server Online"}

@app.get("/hello")
def hello():
    return {"value": 90, "status": "success"}

@app.get("/health")
def health_check():
    # This is the "Heartbeat" signal for the Control Unit
    return {"status": "ok"}

@app.get("/tools")
def get_tools():
    """Return available tools in Claude's tool format with endpoint metadata"""
    return {
        "tools": [
            {
                "name": "calculate_margin",
                "description": "Calculates the profit margin for a project given revenue and cost.",
                "endpoint": "/calculate_margin",
                "method": "POST",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "revenue": {
                            "type": "number",
                            "description": "The project revenue"
                        },
                        "cost": {
                            "type": "number",
                            "description": "The project cost"
                        }
                    },
                    "required": ["revenue", "cost"]
                }
            },
            {
                "name": "get_weather",
                "description": "Get the current weather for any location",
                "endpoint": "/weather",
                "method": "GET",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get weather for (e.g., 'Ann Arbor', 'New York', 'London')"
                        }
                    },
                    "required": ["location"]
                }
            }
        ]
    }

@app.post("/calculate_margin")
def calculate_margin(request: MarginRequest):
    """Calculate profit margin"""
    print("\n" + "="*60)
    print(f"📊 [MARGIN ENDPOINT] POST /calculate_margin called")
    print(f"  Revenue: {request.revenue}")
    print(f"  Cost: {request.cost}")
    
    if request.cost == 0:
        error = {"error": "Cost cannot be zero"}
        print(f"❌ [MARGIN] {error}")
        print("="*60 + "\n")
        return error
    
    margin = ((request.revenue - request.cost) / request.revenue) * 100
    result = {
        "revenue": request.revenue, 
        "cost": request.cost, 
        "margin": margin
    }
    print(f"✓ [MARGIN] Calculated margin: {margin:.2f}%")
    print(f"  Result: {result}")
    print("="*60 + "\n")
    return result

@app.get("/weather")
def get_weather(location: str = "Ann Arbor"):
    """Get current weather for a given location"""
    print("\n" + "="*60)
    print(f"🔍 [WEATHER ENDPOINT] GET /weather?location={location}")
    print("="*60)
    try:
        print(f"🔍 [WEATHER] Creating httpx client with 10s timeout...")
        with httpx.Client(timeout=10.0) as c:
            print(f"🔍 [WEATHER] Making request to wttr.in API for {location}...")
            # Using wttr.in free API (supports any location)
            response = c.get(
                f"https://wttr.in/{location}?format=j1",
                headers={"User-Agent": "Python/Weather"}
            )
            print(f"🔍 [WEATHER] Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            print(f"🔍 [WEATHER] Response received successfully")
            
            # Extract current weather data
            try:
                current = data.get("current_condition", [{}])[0] if isinstance(data.get("current_condition"), list) else data.get("current_condition", {})
                
                # Get nearest area name from response
                nearest_area = data.get("nearest_area", [{}])[0] if isinstance(data.get("nearest_area"), list) else {}
                area_name = location
                if nearest_area:
                    country = nearest_area.get("country", [{}])[0].get("value", "") if isinstance(nearest_area.get("country"), list) else nearest_area.get("country", {}).get("value", "")
                    region = nearest_area.get("areaName", [{}])[0].get("value", "") if isinstance(nearest_area.get("areaName"), list) else nearest_area.get("areaName", {}).get("value", "")
                    if region and country:
                        area_name = f"{region}, {country}"
                    elif region:
                        area_name = region
                
                result = {
                    "location": area_name,
                    "temperature_c": current.get("temp_C", "N/A"),
                    "temperature_f": current.get("temp_F", "N/A"),
                    "description": current.get("weatherDesc", [{}])[0].get("value", "N/A") if current.get("weatherDesc") else "N/A",
                    "humidity": current.get("humidity", "N/A"),
                    "wind_speed_kmh": current.get("windspeedKmph", "N/A"),
                    "feels_like_c": current.get("FeelsLikeC", "N/A"),
                    "feels_like_f": current.get("FeelsLikeF", "N/A")
                }
                print(f"🔍 [WEATHER] Parsed result: {result}")
                print("="*60)
                return result
            except (KeyError, IndexError, TypeError) as e:
                print(f"🔍 [WEATHER] Data parsing error: {e}")
                print(f"🔍 [WEATHER] Raw data structure: {data}")
                return {"error": f"Could not parse weather data: {str(e)}"}
    
    except httpx.TimeoutException as e:
        error_msg = f"Timeout error: {str(e)}"
        print(f"❌ [WEATHER] {error_msg}")
        print("="*60)
        return {"error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"Network error fetching weather: {str(e)}"
        print(f"❌ [WEATHER] {error_msg}")
        print("="*60)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Failed to fetch weather: {str(e)}"
        print(f"❌ [WEATHER] {error_msg}")
        import traceback
        traceback.print_exc()
        print("="*60)
        return {"error": error_msg}