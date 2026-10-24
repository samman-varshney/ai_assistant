import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = list(str(os.getenv("GMAIL_SCOPES")).strip().split(","))

def log(text):
    if os.getenv("AI_ASSISTANT_DEBUG", "").strip().lower() in {"true", "1", "yes", "on"}:
        print(f"\033[90m[LOG] {text}\033[0m")

def construct_response(stream, tools):
    try:
        message = ""
        for event in stream:
        
            if not event:
                continue

            elif event.choices[0].delta.content:

                content = event.choices[0].delta.content
                prefix = "Assistant: " if not message else ""
                message += content
                print(prefix + content, end="", flush=True)

            elif event.choices[0].delta.tool_calls:

                
                tool_calls = event.choices[0].delta.tool_calls
                message += str(tool_calls)
                for tool_call in tool_calls:
                    index = tool_call.index
                    if index not in tools:

                        tools[index] = {
                            "id":tool_calls[0].id,
                            "name":tool_calls[0].function.name,
                            "arguments":tool_calls[0].function.arguments
                        }

                    else:
                        tools[index]["arguments"] += tool_calls[0].function.arguments
        return message
    except Exception as e:
        return F"Error while parsing LLM response - {str(e)}"
    
    
def get_gmail_service_client():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)
 
        