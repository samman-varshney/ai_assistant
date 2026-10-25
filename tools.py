"""Public tool registry and tool-call dispatcher.

Tool implementations live in ``tool_modules``; this module keeps the imports
used by the assistant stable.
"""

import json
from typing import Any

from tool_modules.general import (
    TOOLS as GENERAL_TOOLS,
    TOOLS_MAPPING as GENERAL_TOOLS_MAPPING
)
from tool_modules.gmail import (
    TOOLS as GMAIL_TOOLS,
    TOOLS_MAPPING as GMAIL_TOOLS_MAPPING,
)
from utils import log


TOOLS = GENERAL_TOOLS + GMAIL_TOOLS
TOOLS_MAPPING = {**GENERAL_TOOLS_MAPPING, **GMAIL_TOOLS_MAPPING}


def get_tool_response(tool_calls: list[Any]) -> list[dict[str, str]]:
    messages_history: list[dict[str, str]] = []
    tool_name = "unknown"
    for tool_call in tool_calls:
        tool_call_id = tool_call.id
        tool_args = {}
        try:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            log(f"  🛠️ {tool_name}({tool_args})")
            if tool_name not in TOOLS_MAPPING:
                raise ValueError(f"Tool '{tool_name}' is not defined in TOOLS_MAPPING.")

            tool_info = TOOLS_MAPPING[tool_name]
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
            "tool_call_id": tool_call_id,
        })
    return messages_history
