# Clicom

Lightweight WebSocket chat system with both server and clients (terminal + web) built with Python and aiohttp.

This repository contains:
- `server.py`: A simple async chat server that accepts WebSocket connections and broadcasts messages.
- `main.py`: A feature-rich terminal client with colors, stats tracking, and a nice ASCII banner.

## Features

Server (`server.py`):
- WebSocket chat endpoint (`/ws`) with simple JSON protocol
- Active-users broadcasts and basic /who support
- Runs on configurable port via the `PORT` environment variable (default 10000)

Terminal Client (`main.py`):
- Colorful interface with ASCII banner and ANSI color support
- Stats tracking (messages sent/received, unique users met)
- Supports named colors (1-6) and custom HEX colors (e.g., #ff6600)
- Settings persistence (remembers your name and color)

## Project Files
- `server.py` — WebSocket chat server (aiohttp)
- `main.py` — Terminal client with colorful UI
- `requirements.txt` — Python dependencies

## Requirements
- Python 3.8+ (async/await + aiohttp)
- Windows PowerShell example commands are shown below

## Install & Run (PowerShell)
First, create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the server (in one terminal):
```powershell
$env:PORT = 10000
python .\server.py
# Server listens on 0.0.0.0:10000
```

Run the terminal client (in another terminal):
```powershell
python .\main.py
```

The server listens on `0.0.0.0:$PORT` (default 10000). Connect a WebSocket client to ws://localhost:10000/ws

## WebSocket protocol (JSON)
Clients and server exchange JSON objects with a `type` field.

- Join:
  {"type":"join","name":"Alice"}

- Send message:
  {"type":"message","name":"Alice","color":"6","text":"Hello"}

- Ask who's online:
  {"type":"who"}

- Leave:
  {"type":"leave"}

Server-to-client message examples:

- Chat message:
  {"type":"message","name":"Alice","color":"6","text":"Hello"}

- System message:
  {"type":"system","text":"Alice joined the chat. (3 online)"}

- Active users list:
  {"type":"active_users","users":["Alice","Bob"]}

- Who response (to requester):
  {"type":"who","users":["Alice","Bob"]}

## Dependencies
See `requirements.txt`:
- `aiohttp`: WebSocket client/server (used by both `server.py` and `main.py`)
- `colorama`: Terminal colors (used by `main.py`)
- `aiortc`, `cryptography`: Not currently used, may be for planned features

## Client Commands
Terminal client (`main.py`) supports:
- `/exit` — Leave the chat
- `/stats` — Show your message counts and unique users met
- `/who` — List active users
- `/color` — Change your chat color (named colors or hex)
- `/server <url>` — Changes the server url `default`, `local`, `wss://<host:port>/ws`, `ws://<host:port>/ws`

## Notes & Next steps
- Add connection error handling (allow chnage server or retry?)
- Add automatic reconnect when server changes
- Add room support to allow private conversations
- Add error logging.
- Validate incoming JSON more strictly and add message size/rate limits.
- Add tests (unit tests for broadcast helpers and a small integration test that connects a client).
- Consider adding:
  - Direct messages between users
  - Message history (currently messages are not stored)
  - Rate limiting for messages

## License
MIT-style (no license file included). Add a `LICENSE` file if you need formal licensing.
