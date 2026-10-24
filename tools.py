from datetime import datetime
import json
import os
import requests
from pydantic import BaseModel, Field
from utils import get_gmail_service_client, log
from googleapiclient.errors import HttpError

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

class GetMessagesListRequest(BaseModel):
    maxResults: int = Field(default=10, description="Number of recent mails to fetch, by default last 10 mails are fetched ")

def get_messages_list(maxResults=10):
    try:
        service = get_gmail_service_client()
        results = (
            service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=maxResults).execute()
        )

        messages = results.get("messages", [])
        result = []
        for message in messages:
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            result.append({
                "id":message["id"],
                "snippet":msg["snippet"]
            })
        return str(result)
    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


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
            "description":"Get the list of recent mails of given size of the user, every element in the list have id (email id) and snippet (email snippet)",
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


def get_tool_response(tools_dict, messages_history):
    for index in tools_dict:
        try:
            tool_name = tools_dict[index]['name']
            tool_args = json.loads(tools_dict[index]['arguments'])
            tool_call_id = tools_dict[index]['id']

            log(f"  🛠️ {tool_name}({tool_args})")
            if(tool_name not in TOOLS_MAPPING):
                raise ValueError(f"Tool '{tool_name}' is not defined in TOOLS_MAPPING.")
            
            tool_info = TOOLS_MAPPING.get(tool_name)
            func = tool_info["function"]
            validator = tool_info["validator"]

            validated_args = validator(**tool_args)

            response = func(**validated_args.dict())
        except Exception as e:
            response = f"Error executing tool '{tool_name}': {str(e)}"

        log(f"  💬 response: {response}")

        messages_history.append({
            "role": "tool",
            "content": response,
            "tool_call_id": tool_call_id
        })
