# AI Assistant

A command-line AI assistant that uses an OpenAI-compatible chat completions API. It can call tools to get the current time and current weather for a city.

## Requirements

- Python 3.10 or newer
- An API key and endpoint for an OpenAI-compatible chat completions service
- Internet access for the API and weather requests

## Setup

1. Clone or download this project and open a terminal in the project folder.
2. Create and activate a virtual environment:

   **Windows (PowerShell):**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS / Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   python -m pip install openai python-dotenv pydantic requests
   ```
4. Create a `.env` file in the project folder:
   ```dotenv
   API_KEY=your-api-key
   BASE_URL=https://your-api-host
   MODEL=your-model-name
   WEATHER_BASE_URL=https://wttr.in
   MAX_TOOL_CALL_REQUESTS=10
   AI_ASSISTANT_DEBUG=False
   ```

   The app adds `/v1` to `BASE_URL`. Keep your API key private and do not commit `.env`.

## Run

```bash
python ai_assistant.py
```

Enter a message at the `Samman:` prompt. Type `exit` to quit. Set `AI_ASSISTANT_DEBUG=True` in `.env` to display tool-call logs.

## Project files

- `ai_assistant.py` — command-line conversation loop and API client
- `tools.py` — combined tool registry and tool-call dispatcher
- `tool_modules/general.py` — current-time and city-weather tools
- `tool_modules/gmail.py` — Gmail read, draft, and send tools
- `utils.py` — Gmail authentication, response parsing, and optional logging

## Configuration

| Variable | Description |
| --- | --- |
| `API_KEY` | API credential |
| `BASE_URL` | API base URL; `/v1` is appended by the app |
| `MODEL` | Model name supported by the configured API |
| `WEATHER_BASE_URL` | Weather service base URL, such as `https://wttr.in` |
| `MAX_TOOL_CALL_REQUESTS` | Maximum tool-call rounds for each user message; defaults to `10` |
| `AI_ASSISTANT_DEBUG` | Set to `True` to show tool execution logs |
