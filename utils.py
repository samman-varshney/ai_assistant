
import json
import os
from tools import TOOLS_MAPPING


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

                message += str(event)
                tool_calls = event.choices[0].delta.tool_calls
                index = tool_calls[0].index

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
    
