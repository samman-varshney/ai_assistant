
import json
import os
from tools import TOOLS_MAPPING


def get_tool_response(message, messages_history):
    for tool_call in message.tool_calls:
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

            response = func(**validated_args.dict())
        except Exception as e:
            response = f"Error executing tool '{tool_name}': {str(e)}"

        log(f"  💬 response: {response}")

        messages_history.append({
            "role": "tool",
            "content": response,
            "tool_call_id": tool_call_id
        })

def log(text):
    if(os.getenv("DEBUG") == "True"):
        print(f"\033[90m[LOG] {text}\033[0m")
