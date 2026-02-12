import asyncio
import json
from pathlib import Path
from aiohttp import web
import uuid

connected_users = {}  # ws -> username
active_challenges = []  # list of challenge dicts

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    connected_users[ws] = "Unknown"
    print("🔌 Client connected")

    async for msg in ws:
        if msg.type != web.WSMsgType.TEXT:
            continue
        try:
            data = json.loads(msg.data)
        except:
            continue

        msg_type = data.get("type")

        # --- User joins ---
        if msg_type == "join":
            name = data.get("name", "Guest")
            connected_users[ws] = name
            print(f"🟢 {name} joined")
            await broadcast_system(f"{name} joined the chat. ({len(connected_users)} online)")
            await broadcast_active_users()

        # --- User message ---
        elif msg_type == "message":
            name = data.get("name", "Guest")
            color = data.get("color", "6")
            text = data.get("text", "")
            await broadcast_message(name, color, text)

        # --- /who command ---
        elif msg_type == "who":
            users = list(connected_users.values())
            await ws.send_json({"type": "who", "users": users})

        # --- Challenge another player ---
        elif msg_type == "challenge":
            challenger = data.get("challenger", "Guest")
            opponent = data.get("opponent", "Guest")
            challenge = {
                "challenge_id": str(uuid.uuid4()),
                "type": "challenge",
                "challenger": challenger,
                "opponent": opponent,
                "timestamp": data.get("timestamp", 0)
            }
            active_challenges.append(challenge)
            await broadcast_challenge(challenge)
            print(f"⚔️ {challenger} challenged {opponent}")

        # --- Accept challenge ---
        elif msg_type == "accept-challenge":
            challenge_id = data.get("challenge_id")
            matching = [c for c in active_challenges if c.get("challenge_id") == challenge_id]
            if matching:
                challenge = matching[0]
                active_challenges.remove(challenge)
                await broadcast_system(f"{challenge['challenger']} and {challenge['opponent']} started a game!")
                print(f"🎮 Game started: {challenge['challenger']} vs {challenge['opponent']}")

        # --- User leaves ---
        elif msg_type == "leave":
            name = connected_users.get(ws, "Unknown")
            if ws in connected_users: del connected_users[ws]
            await ws.close()
            print(f"🔴 {name} left")
            await broadcast_system(f"{name} left the chat. ({len(connected_users)} online)")
            await broadcast_active_users()

    # --- Unexpected disconnect ---
    if ws in connected_users:
        name = connected_users[ws]
        del connected_users[ws]
        await broadcast_system(f"{name} disconnected unexpectedly. ({len(connected_users)} online)")
        await broadcast_active_users()
        print(f"⚪ {name} disconnected")

    return ws

async def broadcast_message(name, color, text):
    msg_data = {"type":"message","name":name,"color":color,"text":text}
    for ws in list(connected_users.keys()):
        try:
            await ws.send_json(msg_data)
        except:
            if ws in connected_users: del connected_users[ws]

async def broadcast_system(text):
    msg_data = {"type":"system","text":text}
    for ws in list(connected_users.keys()):
        try:
            await ws.send_json(msg_data)
        except:
            if ws in connected_users: del connected_users[ws]

async def broadcast_active_users():
    users = list(connected_users.values())
    msg_data = {"type":"active_users","users":users}
    for ws in list(connected_users.keys()):
        try:
            await ws.send_json(msg_data)
        except:
            if ws in connected_users: del connected_users[ws]

async def broadcast_challenge(challenge):
    for ws in list(connected_users.keys()):
        try:
            await ws.send_json(challenge)
        except:
            if ws in connected_users: del connected_users[ws]

async def index(request):
    # Serve a plain-text index; the browser client is available at /client
    return web.Response(text="Clicom Chat Server is running. Visit /client for the web client.", content_type="text/plain")


async def client_page(request):
    # Return the static client.html file from the clicom/ folder
    root = Path(__file__).parent / 'clicom'
    client_file = root / 'client.html'
    if client_file.exists():
        return web.FileResponse(path=str(client_file))
    return web.Response(text="Client not found.", status=404)

async def game_lobby_page(request):
    # Return the game-lobby.html file from the clicom/ folder
    root = Path(__file__).parent / 'clicom'
    lobby_file = root / 'game-lobby.html'
    if lobby_file.exists():
        return web.FileResponse(path=str(lobby_file))
    return web.Response(text="Game lobby not found.", status=404)

async def game_page(request):
    # Return the game.html file from the clicom/ folder
    root = Path(__file__).parent / 'clicom'
    game_file = root / 'game.html'
    if game_file.exists():
        return web.FileResponse(path=str(game_file))
    return web.Response(text="Game not found.", status=404)

async def scorch_page(request):
    # Return the scorch.html file from the clicom/ folder
    root = Path(__file__).parent / 'clicom'
    scorch_file = root / 'scorch.html'
    if scorch_file.exists():
        return web.FileResponse(path=str(scorch_file))
    return web.Response(text="Scorch game not found.", status=404)

app = web.Application()
app.add_routes([
    web.get("/", index),
    web.get("/client", client_page),
    web.get("/game", scorch_page),
    web.get("/scorch", scorch_page),
    web.get("/game-lobby", game_lobby_page),
    web.get("/ws", websocket_handler)
])

# Serve static assets under /clicom/ (exposes files from ./clicom)
static_path = str(Path(__file__).parent / 'clicom')
app.router.add_static('/clicom/', static_path, show_index=True)

if __name__ == "__main__":
    # Render uses $PORT environment variable
    import os
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
