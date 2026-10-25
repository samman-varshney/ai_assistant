from datetime import datetime
import json
import os
from typing import Any
import requests
from pydantic import BaseModel, Field
from utils import get_gmail_service_client, log

class GetCurrentTimeRequest(BaseModel):
    pass

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class GetCityWeatherRequest(BaseModel):
    location: str = Field(description="The city for which to get the weather")

def get_city_weather(location: str) -> str:
    response = requests.get(f"{os.getenv('WEATHER_BASE_URL')}/{location}?format=3")
    response.raise_for_status() # this will raise an error if the request was unsuccessful
    return response.text

class GetMessagesListRequest(BaseModel):
    maxResults: int = Field(
        default=10,
        description="Number of recent mails to be fetched." \
        "By default recent 10 mails are fetched." \
        "Maximum 500 recent mails can be fetched per request" \
        "Minimum 1 recent mails can be fetched per request",
        max=500,
        min=1
    )

def get_messages_list(maxResults: int = 10) -> list[dict[str, str]]:
    service = get_gmail_service_client()
    results = (
        service
        .users()
        .messages()
        .list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=maxResults
            )
        .execute()
    )

    messages = results.get("messages", [])
    result = []

    for message in messages:
        msg = (
            service
            .users()
            .messages()
            .get(userId="me", id=message["id"])
            .execute()
        )
        result.append({
            "id":message["id"],
            "snippet":msg["snippet"]
        })
    return result

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
    },
    {
        "type":"function",
        "function":{
            "name":"get_messages_list",
            "description":("Get list of recent mails of user of given size."
            "output list contains id (email id) and snippet for every email."),
            "parameters": GetMessagesListRequest.model_json_schema()
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
    },
    "get_messages_list":{
        "function":get_messages_list,
        "validator":GetMessagesListRequest
    }
}   


def get_tool_response(tool_calls: list[Any]) -> list[dict[str, str]]:
    messages_history: list[dict[str, str]] = []
    tool_name = "unknown"
    for tool_call in tool_calls:
        tool_call_id = tool_call.id
        try:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            tool_call_id = tool_call.id

            log(f"  🛠️ {tool_name}({tool_args})")
            if(tool_name not in TOOLS_MAPPING):
                raise ValueError(f"Tool '{tool_name}' is not defined in TOOLS_MAPPING.")
            
            tool_info = TOOLS_MAPPING.get(tool_name)
            func = tool_info["function"]
            validator = tool_info["validator"]
            validated_args = validator(**tool_args)
            response = json.dumps(func(**validated_args.model_dump()), ensure_ascii=False)

        except Exception as e:
            response = f"Error executing tool '{tool_name}': {e}"

        log(f"  💬 response: {response}")

        messages_history.append({
            "role": "tool",
            "content": response,
            "tool_call_id": tool_call_id
        })
    return messages_history
