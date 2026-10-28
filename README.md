# AI Assistant

A Python command-line assistant that streams responses from an OpenAI-compatible chat completions API and can call tools for current time, city weather, and Gmail. Gmail tools can list and read messages, create drafts, and send messages or drafts.

## Requirements

- Python 3.10 or newer
- An API key, base URL, and model name for an OpenAI-compatible chat completions service
- Internet access for the chat API, weather service, and Gmail API

## Setup

1. Create and activate a virtual environment in the project directory:

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

2. Install dependencies:

   ```bash
   python -m pip install openai python-dotenv pydantic requests google-api-python-client google-auth google-auth-oauthlib
   ```

3. Create a `.env` file in the project directory:

   ```dotenv
   API_KEY=your-api-key
   BASE_URL=https://your-api-host
   MODEL=your-model-name
   WEATHER_BASE_URL=https://wttr.in
   MAX_TOOL_CALL_REQUESTS=10
   AI_ASSISTANT_DEBUG=False
   GMAIL=your-gmail-address@example.com
   GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.compose,https://www.googleapis.com/auth/gmail.send
   ```

   `BASE_URL` is the API host without a trailing `/v1`; the assistant appends `/v1`. `GMAIL_SCOPES` is a comma-separated list of Google OAuth scopes. The listed scopes allow reading mail, creating drafts, and sending mail. Keep `.env` private and do not commit it.

4. To use Gmail features, configure OAuth credentials in Google Cloud for a desktop application, enable the Gmail API, and place the downloaded OAuth client file in the project directory as `credentials.json`. On the first Gmail tool call, a browser authorization flow runs and saves the resulting token as `token.json` for later use. Keep both credential files private; they are excluded by `.gitignore`.

Gmail credentials and `GMAIL_SCOPES` are only needed when using Gmail tools. The time and weather tools do not require Gmail setup.

## Run

```bash
python ai_assistant.py
```

Enter a message at the `Samman:` prompt. Type `exit` to quit. Responses stream to the terminal. Set `AI_ASSISTANT_DEBUG=True` to show tool-call logs. The conversation history is kept in memory for the current process and is not persisted after exit.

## Available tools

| Tool | Purpose |
| --- | --- |
| `get_current_time` | Return the machine's local date and time as `YYYY-MM-DD HH:MM:SS`. |
| `get_city_weather` | Fetch a short current-weather report for a city from `WEATHER_BASE_URL`. |
| `get_messages_list` | List recent Gmail messages, with an optional Gmail search query and labels. Defaults to 10 inbox messages; accepts 1–500 results. |
| `get_message` | Retrieve a message's plain-text body (or snippet if no plain-text body is available) by Gmail message ID. |
| `gmail_create_draft` | Save an email draft with recipient, subject, and body. |
| `gmail_send_draft` | Send a saved Gmail draft by draft ID. |
| `gmail_send_message` | Compose and send an email with recipient, subject, and body. |

Sending tools perform real actions in the authorized Gmail account. The assistant may call tools in multiple rounds to answer a request, up to the configured limit.

## Configuration

| Variable | Description |
| --- | --- |
| `API_KEY` | Credential for the configured chat completions API. |
| `BASE_URL` | API host; `/v1` is appended by the client. |
| `MODEL` | Model name accepted by the configured API. |
| `WEATHER_BASE_URL` | Weather service base URL, such as `https://wttr.in`. |
| `MAX_TOOL_CALL_REQUESTS` | Maximum tool-call rounds per user message. Defaults to `10` and is clamped to at least `1`. |
| `AI_ASSISTANT_DEBUG` | Set to `True`, `1`, `yes`, or `on` to print tool execution logs. |
| `GMAIL` | Address used as the `From` header when creating or sending email. |
| `GMAIL_SCOPES` | Comma-separated Google OAuth scope URLs required by the Gmail tools. |

## Project files

- `ai_assistant.py` — command-line conversation loop, streaming API client, and tool-call round limit.
- `tools.py` — combines tool definitions and validates and dispatches tool calls.
- `tool_modules/general.py` — current-time and city-weather tools.
- `tool_modules/gmail.py` — Gmail list, read, draft, and send tools.
- `utils.py` — stream parsing, Gmail OAuth/client setup, email-body extraction, and optional debug logging.
