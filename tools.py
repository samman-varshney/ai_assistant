from datetime import datetime
import os
import requests
from pydantic import BaseModel, Field

class GetCurrentTimeRequest(BaseModel):
    pass

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class GetCityWeatherRequest(BaseModel):
    location: str = Field(description="The city for which to get the weather")

def get_city_weather(location):
    response = requests.get(f"{os.getenv('WEATHER_BASE_URL')}/{location}?format=3")
    response.raise_for_status() # this will raise an error if the request was unsuccessful
    return response.text


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in the format YYYY-MM-DD HH:MM:SS",
            "parameters": GetCurrentTimeRequest.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_weather",
            "description": "Get the current weather for a given city",
            "parameters": GetCityWeatherRequest.model_json_schema()
        }
    }
]

TOOLS_MAPPING = {
    "get_current_time": {
        "function": get_current_time,
        "validator": GetCurrentTimeRequest
    },
    "get_city_weather": {
        "function": get_city_weather,
        "validator": GetCityWeatherRequest
    }
}   