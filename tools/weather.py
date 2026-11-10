"""Simple weather API integration for OpenWeatherMap."""

import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from langchain_core.tools import tool
from config.settings import get_settings


# Region coordinates (India)
REGIONS = {
    "north": (28.7041, 77.1025),    # Delhi
    "south": (13.0827, 80.2707),    # Chennai
    "east": (22.5726, 88.3639),     # Kolkata
    "west": (19.0760, 72.8777),     # Mumbai
    "central": (23.2599, 77.4126)   # Bhopal
}


def get_weather_forecast(region: str, days: int = 5) -> Dict[str, Any]:
    """
    Get weather forecast for a region.

    Args:
        region: Region name (north/south/east/west/central)
        days: Number of forecast days (max 5)

    Returns:
        Dict with forecast data
    """
    settings = get_settings()
    lat, lon = REGIONS.get(region.lower(), REGIONS["central"])

    try:
        # Call OpenWeatherMap API
        url = f"{settings.openweather_base_url}/forecast"
        response = requests.get(url, params={
            "lat": lat,
            "lon": lon,
            "appid": settings.openweather_api_key,
            "units": "metric",
            "cnt": min(days * 8, 40)
        }, timeout=10)

        response.raise_for_status()
        data = response.json()

        # Process daily forecasts
        daily = {}
        for item in data.get("list", []):
            date = datetime.fromtimestamp(item["dt"]).date().isoformat()
            if date not in daily:
                daily[date] = {"temps": [], "rain": [], "humidity": [], "conditions": []}

            daily[date]["temps"].append(item["main"]["temp"])
            daily[date]["humidity"].append(item["main"]["humidity"])
            daily[date]["rain"].append(item.get("rain", {}).get("3h", 0))
            daily[date]["conditions"].append(item["weather"][0]["main"])

        # Calculate daily averages
        forecasts = []
        for date in sorted(daily.keys())[:days]:
            d = daily[date]
            forecasts.append({
                "date": date,
                "temperature": round(sum(d["temps"]) / len(d["temps"]), 1),
                "rainfall": round(sum(d["rain"]), 1),
                "humidity": round(sum(d["humidity"]) / len(d["humidity"]), 1),
                "condition": max(set(d["conditions"]), key=d["conditions"].count)
            })

        return {"region": region, "days": days, "forecast": forecasts}

    except Exception:
        # Fallback data if API fails
        return {
            "region": region,
            "days": days,
            "forecast": [
                {
                    "date": (datetime.now() + timedelta(days=i+1)).date().isoformat(),
                    "temperature": 25.0,
                    "rainfall": 0.0,
                    "humidity": 65.0,
                    "condition": "Clear"
                }
                for i in range(days)
            ],
            "fallback": True
        }


@tool
def get_weather_forecast_tool(region: str, days: int = 5) -> str:
    """Get weather forecast for a region (north/south/east/west/central) to help with inventory planning. Returns temperature, rainfall, humidity and conditions for the next 5 days.
    
    Args:
        region: The region to get weather for. Must be one of: north, south, east, west, central.
        days: Number of days to forecast. Default is 5.
    """
    result = get_weather_forecast(region, days)
    # Return as formatted string for LLM
    forecasts_str = "\n".join([
        f"  {f['date']}: {f['temperature']}°C, {f['rainfall']}mm rain, {f['humidity']}% humidity, {f['condition']}"
        for f in result.get('forecast', [])
    ])
    return f"Weather forecast for {result['region']} ({result['days']} days):\n{forecasts_str}"

