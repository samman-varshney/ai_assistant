import base64
import os
from typing import Any, Iterable
from types import SimpleNamespace
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def get_gmail_scopes():
    return os.getenv("GMAIL_SCOPES").split(",")

def log(text: str) -> None:
    if os.getenv("AI_ASSISTANT_DEBUG", "").strip().lower() in {"true", "1", "yes", "on"}:
        print(f"\033[90m[LOG] {text}\033[0m")

def print_LLM_response(content: str, message: str) -> str:
    if(not content): return message + content
    prefix = "Assistant: " if not message else ""
    print(prefix + content, end="", flush=True)
    return message + content

def construct_response(stream: Iterable[Any]) -> tuple[str, list[Any]]:
    tool_calls_dict: dict[int, Any] = {}
    message: str = ""
    error_message: str = ""

    try:
        for event in stream:
        
            if not event or not event.choices:
                continue

            delta = event.choices[0].delta

            if delta.content:

                content = delta.content
                message = print_LLM_response(content, message)

            if delta.tool_calls:
                
                tool_calls = delta.tool_calls
                for tool_call in tool_calls:
                    index = tool_call.index
                    tool_calls_dict.setdefault(
                        index,
                        SimpleNamespace(id=None, function=SimpleNamespace(name="", arguments=""))
                    )

                    if tool_call.id:
                        tool_calls_dict[index].id = tool_call.id
                    if tool_call.function and tool_call.function.name:
                        tool_calls_dict[index].function.name += tool_call.function.name
                    if tool_call.function and tool_call.function.arguments:
                        tool_calls_dict[index].function.arguments += tool_call.function.arguments
    
    except KeyboardInterrupt:
        error_message = " \033[31m(Streaming paused by user interrupt)\033[0m"
        tool_calls_dict = {}
    except Exception as e:
        error_message = f" \033[31m(Error while parsing stream events: {e})\033[0m"
        tool_calls_dict = {}

    message = print_LLM_response(error_message, message)

    tool_calls_list = [tool_calls_dict[index] for index in sorted(tool_calls_dict)]
    return message, tool_calls_list
    
def get_gmail_service_client() -> Any:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", get_gmail_scopes())
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", get_gmail_scopes()
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)
 
def construct_tool_calls_payload(tool_calls: list[Any]) -> list[dict[str, Any]]:
    """converting tool_calls to openai acceptable format
    [{
        "type":"function",
        "id":<tool_call_id>
        "function":
        {
            "name":<function_name>,
            "arguments":<function_arguments>
        }
    }]"""

    payload: list[dict[str, Any]] = []

    for tool_call in tool_calls:
        payload.append({
            "type":"function",
            "id":tool_call.id,
            "function":
            {
                "name":tool_call.function.name,
                "arguments":tool_call.function.arguments
            }
        })

    return payload

def find_plain_text(part):
    mime_type = part.get("mimeType", "")
    data = part.get("body", {}).get("data")
    if mime_type == "text/plain" and data:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for child in part.get("parts", []):
        text = find_plain_text(child)
        if text:
            return text
    return None