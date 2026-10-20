
from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
from tools import TOOLS
from utils import get_tool_response, log

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

client = OpenAI(
    base_url=f"{os.getenv("BASE_URL")}/v1",
    api_key=os.getenv("API_KEY")
)



messages_history = []

max_tool_call_requests = int(os.getenv("MAX_TOOL_CALL_REQUESTS", 10))

messages_history.append({
    "role": "system",
    "content": (
        "You are a helpful assistant."
        "Don't execeed the {max_tool_call_requests} subsequent tool calls limit. "
        "Keep responses under 100 words."
    ),
})

print("type exit to stop the conversation")

while True : 

    query = input("\nSamman: ")
    if(query.lower() in ("exit")):
        break
    messages_history.append({
        "role": "user",
        "content": query
    })

    

    for i in range(max_tool_call_requests):

        response = client.chat.completions.create(
                model=os.getenv("MODEL"),
                messages=messages_history,
                tools=TOOLS
            )
        
        message = response.choices[0].message

        if not message.tool_calls:
            break

        log(f"Step {i+1}: LLM requested {len(message.tool_calls)} tool call(s).")

        messages_history.append(message)
        get_tool_response(message, messages_history)

    else:

        messages_history.append({
            "role": "assistant",
            "content": "Error: Too many tool calls. Please try again."
            })
        print("Assistant: Too many tool calls. Please try again.")
        continue


    messages_history.append({
        "role": "assistant",
        "content": message.content
    })

    reply = message.content if message.content else "No response from the assistant."

    print(f'Assistant: {reply}')


